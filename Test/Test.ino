const int buttonPin = 4;
const int buttonPin2 = 9;
const int ledPin = 6;
const int ledPin2 = 12;
int buttonState1 = 0;  
int lastButtonState1 = 0;
int buttonState2 = 0;  
int lastButtonState2 = 0;

// the setup function runs once when you press reset or power the board
void setup() {
  // initialize digital pin LED_BUILTIN as an output.
  Serial.begin(19200);
  Serial.flush();
  pinMode(LED_BUILTIN, OUTPUT);
  pinMode(buttonPin, INPUT_PULLUP);
  pinMode(buttonPin2, INPUT_PULLUP);
  pinMode(ledPin, OUTPUT);
  pinMode(ledPin2, OUTPUT);
}

// the loop function runs over and over again forever
void loop() {
  buttonState1 = digitalRead(buttonPin);
  if (buttonState1 == HIGH )
  {
    digitalWrite(ledPin, LOW);  
  }
  else
  {
    digitalWrite(ledPin, HIGH);
    if ( lastButtonState1 == HIGH )
    {
       Serial.write("BUTTON1PRESSED\n");
    }     
  }
  lastButtonState1 = buttonState1;

  buttonState2 = digitalRead(buttonPin2);
  if (buttonState2 == HIGH )
  {
    digitalWrite(ledPin2, LOW);  
  }
  else
  {
    digitalWrite(ledPin2, HIGH);
     if ( lastButtonState2 == HIGH )
    {
       Serial.write("BUTTON2PRESSED\n");
    }    
  }  
  lastButtonState2 = buttonState2;
}
