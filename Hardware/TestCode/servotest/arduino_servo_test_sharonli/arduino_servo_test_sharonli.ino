#include <Servo.h>

Servo myservo;  // create servo object to control a servo
// twelve servo objects can be created on most boards

int pos = 0;    // variable to store the servo position
int buttonState = 0; 
int posState = 0;
const int buttonPin = 43;
const int servoPin = 51;

void setup() {
  myservo.attach(servoPin);  // attaches the servo on pin 9 to the servo object
    // initialize the pushbutton pin as an input:
  pinMode(buttonPin, INPUT);
}

void loop() {
    // read the state of the pushbutton value:
  buttonState = digitalRead(buttonPin);

  // check if the pushbutton is pressed. If it is, the buttonState is HIGH:
  if (buttonState == HIGH) {
    // turn servo cw:
    posState++;
  }
  else {
    posState++;
  }
  if (posState%2 ==0){
    pos = 0;
    myservo.write(pos);
  }

  else{
    pos = 180;
    myservo.write(pos);
  }
}



