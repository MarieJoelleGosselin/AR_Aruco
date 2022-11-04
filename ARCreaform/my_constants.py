import numpy as np
import cv2

#hardcoded intrinsic matrix for my webcam
A = [[1484.418, 0, 978.461], [0, 1500.0, 539.08], [0, 0, 1]] 
A = np.array(A)

# constants specific to the implementation with tracking
lk_params = dict( winSize  = (19, 19),
                  maxLevel = 2,
                  criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))

feature_params = dict( maxCorners = 50,
                       qualityLevel = 0.01,
                       minDistance = 8,
                       blockSize = 19 )

FREQUENCY = 100 # of finding the aruco marker from scratch
TRACKING_QUALITY_THRESHOLD_PERCENTAGE = 100 #reducing this number will make the program tolerate poorer tracking without refreshing to fix it


