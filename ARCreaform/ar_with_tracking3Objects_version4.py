# v1 - this version uses sparse optical tracking for a more responsive program

import cv2
import numpy as np
import math
from object_module import *
import sys
import aruco_module as aruco
from my_constants import *
from utils import get_extended_RT

import time
import serial

def checkedTrace(img0, img1, p0, back_threshold = 1.0):
    p1, st, err = cv2.calcOpticalFlowPyrLK(img0, img1, p0, None, **lk_params)
    p0r, st, err = cv2.calcOpticalFlowPyrLK(img1, img0, p1, None, **lk_params)
    d = abs(p0-p0r).reshape(-1, 2).max(-1)
    status = d < back_threshold
    return p1, status

if __name__ == '__main__':
    
    marker_colored = cv2.imread('data/m1.png')
    assert marker_colored is not None, "Could not find the aruco marker image file"
    #accounts for lateral inversion caused by the webcam
    marker_colored = cv2.flip(marker_colored, 1)

    marker_colored =  cv2.resize(marker_colored, (480,480), interpolation = cv2.INTER_CUBIC )
    marker = cv2.cvtColor(marker_colored, cv2.COLOR_BGR2GRAY)

    print("trying to access the webcam")
    cv2.namedWindow("AR webcam")
    vc = cv2.VideoCapture(0) #put 0 for internal webcam, 1 for externaL
    assert vc.isOpened(), "couldn't access the webcam"
    
    arduino = serial.Serial('/dev/cu.usbserial-14140', baudrate=19200)  
    assert arduino.isOpen(), "couldn't acces the arduino"

    h,w = marker.shape
    #considering all 4 rotations
    marker_sig1 = aruco.get_bit_sig(marker, np.array([[0,0],[0,w], [h,w], [h,0]]).reshape(4,1,2))
    marker_sig2 = aruco.get_bit_sig(marker, np.array([[0,w], [h,w], [h,0], [0,0]]).reshape(4,1,2))
    marker_sig3 = aruco.get_bit_sig(marker, np.array([[h,w],[h,0], [0,0], [0,w]]).reshape(4,1,2))
    marker_sig4 = aruco.get_bit_sig(marker, np.array([[h,0],[0,0], [0,w], [h,w]]).reshape(4,1,2))

    sigs = [marker_sig1, marker_sig2, marker_sig3, marker_sig4]
    rval, frame = vc.read()
    assert rval, "couldn't access the webcam"
    h2, w2,  _ = frame.shape
    h_canvas = max(h, h2)
    w_canvas = w + w2

    ################################################################
    # initialising all the variables needed for tracking
    p0 = None
    use_ransac = True
    print("Identifying important points to track")
    fixed_gp = cv2.goodFeaturesToTrack(marker, **feature_params)
    H_from_aruco = None #the initial homography, the partial homography obtained from tracking is combined witht this to get the full homography
    counter = 0
    started_once = False
    lost_tracking = True #initially means that we havent started
    all_tracking_pts = fixed_gp.shape[0]
    TRACKING_QUALITY_THRESHOLD = max(4, int(0.01 * TRACKING_QUALITY_THRESHOLD_PERCENTAGE * all_tracking_pts))
    print(f"good pts in the marker are {all_tracking_pts}")
    print(f"homography is calculated from scratch when number of pts tracked falls below {TRACKING_QUALITY_THRESHOLD} ({TRACKING_QUALITY_THRESHOLD_PERCENTAGE}%); ")
    
    ##################################################################
    obj = three_d_object('data/3d_objects/low-poly-fox-by-pixelmannen.obj', 'data/3d_objects/texture.png')      
    scale = 10         
    current_ar_model = 0;
    max_num_models = 3;
    prev_change = time.time()
    while rval:
        counter += 1
        rval, frame = vc.read() #fetch frame from webcam
        canvas = np.zeros((h_canvas, w_canvas, 3), np.uint8) #final display created, filled later
        canvas[:h, :w, :] = marker_colored #marker for reference
        canvas[:h2 , w: , :] = np.flip(frame, axis = 1) # putting the raw frame for now
        
        keyObj = 0xFF & cv2.waitKey(1)
        #if keyObj == ord('l'):
        if arduino.inWaiting():
            #print("reading arduino")
            value = arduino.readline().decode()
            #print(value)
            diff_time = time.time() - prev_change
            if (diff_time < 5 ):
                continue;
            else:
                if ( value == "BUTTON1PRESSED\n"):
                    print('next')
                    current_ar_model += 1;
                elif ( value == "BUTTON2PRESSED\n"):
                    print('prev')
                    current_ar_model -= 1;
    
                if ( current_ar_model >= max_num_models):
                    current_ar_model = 0
    
                if ( current_ar_model < 0):
                    current_ar_model = max_num_models
                
                prev_change = time.time()
            
        if ( current_ar_model == 0):
            obj = three_d_object('data/3d_objects/LibertStatue.obj', 'data/3d_objects/Liberty-GreenBronze-1.png', False, (20, 100, 50))
            scale = 1000         
          
            #obj = three_d_object('data/3d_objects/stanford-bunny.obj', 'data/3d_objects/negx.png', False, (0, 200, 200))            
            #scale = 5000   

            #print('selected l(iberty)')            
        elif current_ar_model == 1:                
            obj = three_d_object('data/3d_objects/Ginger_Bread_Cookies_OBJ.obj', 'data/3d_objects/Ginger_Bread Cookies_BaseColor.png', False, (100, 100, 200))
            scale = 3000            
            #print('selected G(inger)')
        elif current_ar_model == 2:    
            obj = three_d_object('data/3d_objects/low-poly-fox-by-pixelmannen.obj', 'data/3d_objects/texture.png')  
            scale = 5
            #print('selected f(ox)')

        frame_copy = frame.copy()
        frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        if not lost_tracking:
            p2, trace_status = checkedTrace(frame_gray_previous, frame_gray, p1)
            p1 = p2[trace_status].copy()
            p0 = p0[trace_status].copy()
            frame_gray_previous = frame_gray
            if len(p0) < TRACKING_QUALITY_THRESHOLD:
                lost_tracking = True
                print("LOST YOU")
                continue
            H_mid, status = cv2.findHomography(p0, p1, (0, cv2.RANSAC)[use_ransac], 10.0)
            combined_homography = (H_mid).dot(H_from_aruco)
            R_T = get_extended_RT(np.float64(A), np.float64(combined_homography))
            transformation = np.float64(A).dot(R_T)           
            augmented = np.flip(augment(frame, obj, transformation, marker, scale), axis = 1)                
            canvas[:h2 , w: , :] = augmented

        canvas = cv2.resize(canvas, (0,0), fx=0.5, fy=0.5)
        cv2.imshow("AR webcam", canvas)
        
        if keyObj == 27: # Escape key to exit
            break
        initiating_keystroke = (keyObj == ord(' ')) #spacebar
        
        
        time_to_refresh_from_scratch = (started_once and (counter - last_refreshed) >= FREQUENCY)
        havent_started = not started_once

        if initiating_keystroke or lost_tracking or time_to_refresh_from_scratch or havent_started:
            last_refreshed = counter
            if(time_to_refresh_from_scratch):
                print(f"refreshed, counter is {counter}")

            # wiping the state
            lost_tracking = True
            p0 = None
            H_from_aruco = None
            success = False
            try:
                # trying to find the aruco marker
                success, H_from_aruco  = aruco.find_homography_aruco(frame_copy, marker, sigs)
            except Exception as e:
                print(e)
                print('couldnt find and draw the homography')
                pass

            if success and H_from_aruco is not None:
                started_once = True
                temp_pts = np.float32(fixed_gp).reshape(-1,1,2)
                p0 = cv2.perspectiveTransform(temp_pts,H_from_aruco)
                p1 = p0
                frame_gray_previous = frame_gray
                lost_tracking = False

        if keyObj == ord('r'):
            use_ransac = not use_ransac
            print("ransac turned {}".format("on" if use_ransac else "off"))

vc.release()
cv2.destroyAllWindows()