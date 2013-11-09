/*
* Skellysnare/Roboskeleton Head Code
* Written by: Daniel Shope (webster32@gmail.com) 
* Last Updated: 03/12/2010
* 
* Moves jaw, pan/tilt head, and eye pan on RobOrchestra head
* Uses 4 standard HS-311 servos, but any ordinary 180deg servo will work
* Calibration constants (#defines) should not be changed unless head has
* been modified.
* 
* Future Additions: Simplify existing code and add more functions for
* interesting behavior. Make autonomous mode with random "wandering" behavior.
* Might need protothreading for random eye movements, etc. Need to supress random 
* movement during pre-scripted movements. Not sure how well that will work with
* servos since both are using the same hardware timers...
* Red LED eyes? Easy to code
* 
*/ 

#include <Servo.h>

#define MOUTH_SERVO 6
#define MOUTH_CLOSED 70
#define MOUTH_OPEN 120
#define MOUTH_OPEN_WIDE 180
#define MOUTH_SERVO_DELAY_MS 40

#define EYE_SERVO 5
#define EYE_NORMAL 90
#define EYE_LEFT 170
#define EYE_RIGHT 35

#define HEAD_TILT_SERVO 9
#define HEAD_TILT_NORMAL 90
#define HEAD_TILT_UP 175
#define HEAD_TILT_DOWN 30

#define HEAD_PAN_SERVO 10
#define HEAD_PAN_NORMAL 90
#define HEAD_PAN_LEFT 50
#define HEAD_PAN_RIGHT 130

#define UpLeft 100
#define UpRight 101
#define Up 102
#define DownLeft 103
#define DownRight 104
#define Down 105
#define Forward 106 
#define Left 107
#define Right 108

// instantiate the servo control objects
Servo mouthServo;  Servo headTiltServo; Servo headPanServo; Servo eyeServo;

// setup global tracking variables for head position
int headPanAngle = HEAD_PAN_NORMAL;
int headTiltAngle = HEAD_TILT_NORMAL;
byte command = 'S';

void setup() {
  eyeServo.attach(EYE_SERVO);
  mouthServo.attach(MOUTH_SERVO);
  headTiltServo.attach(HEAD_TILT_SERVO);
  headPanServo.attach(HEAD_PAN_SERVO);
  Serial.begin(9600);
  Serial.print("BEWARE: Entering Initiation Sequence");
  delay(2000);
}

void loop() {
  lookAroundCircle();
  
}

void headMove(int tiltAngle, int panAngle) {
  byte dTilt = max(tiltAngle,headTiltAngle)-min(tiltAngle,headTiltAngle);
  byte dPan = max(panAngle,headPanAngle)-min(panAngle,headPanAngle);
  int stepTilt = ceil(dTilt/40);
  int stepPan = ceil(dPan/40);
  
  if (headTiltAngle > tiltAngle) {
    //down for both tilt
    stepTilt = -1*stepTilt;
  }
  if (headPanAngle > panAngle) {
    //down for pan
    stepPan = -1*stepPan;
  }
  for (int i=0; i<40; i++) {
      headTiltAngle += stepTilt;
      headPanAngle += stepPan;
    
      headTiltServo.write(headTiltAngle);
      headPanServo.write(headPanAngle);
      delay(15);
  }
}

void headTilt(int moveToAngle) {
    int pos;
    if (headTiltAngle <= moveToAngle) {
      for(pos = headTiltAngle; pos < moveToAngle; pos += 5) {
        headTiltServo.write(pos); delay(15);
      }
    } else {
      for(pos = headTiltAngle; pos>=moveToAngle; pos-=5) {                                
        headTiltServo.write(pos); delay(15);
      }
    }
    headTiltAngle = moveToAngle;
}

void headTurn(int moveToAngle) {
    int pos;
    if (headPanAngle <= moveToAngle) {
      for(pos = headPanAngle; pos < moveToAngle; pos += 5) {
        headPanServo.write(pos); delay(30);
      }
    } else {
      for(pos = headPanAngle; pos>=moveToAngle; pos-=5) {
        headPanServo.write(pos); delay(30);
      }
    }
    headPanAngle = moveToAngle;
}

//nod head specified number of times, speed parameter could be added...
void headNod(int repeat) {
  int pos;
  for (int i=0; i<repeat; i++) {
//    for(pos = HEAD_TILT_DOWN; pos < HEAD_TILT_UP; pos += 5) {
//      headTiltServo.write(pos); delay(15);
//    }
//    for(pos = HEAD_TILT_UP; pos>=HEAD_TILT_DOWN; pos-=5) {                                
//      headTiltServo.write(pos); delay(15);
//    }
    headTiltServo.write(HEAD_TILT_NORMAL); delay(300);
    headTiltServo.write(HEAD_TILT_DOWN); delay(300);
  }
  //return head to default position
  headTiltServo.write(HEAD_TILT_NORMAL);
}

void headUp() {
  headTiltServo.write(HEAD_TILT_UP); 
}

void mouthOpen(int position, int delayms) {
  mouthServo.write(position);
  delay(delayms);
  
  //close mouth
  mouthServo.write(MOUTH_CLOSED);
}

void mouthChatter() {
  for (int i=0; i<5 ;i++) {
    mouthOpen(MOUTH_OPEN, 175);
    delay(175);
  }
}

void eyeLook(int position) {
  eyeServo.write(position);
}

//pre-programmed positions for eyes and head
void look(int position) {
  int headTiltPos; int headPanPos; int eyePos;
  
  switch (position) {
    case UpLeft:
      headTiltPos = HEAD_TILT_UP; headPanPos = HEAD_PAN_LEFT; eyePos = EYE_LEFT; break;
    case UpRight:
      headTiltPos = HEAD_TILT_UP; headPanPos = HEAD_PAN_RIGHT; eyePos = EYE_RIGHT; break;
    case Up:
      headTiltPos = HEAD_TILT_UP; headPanPos = HEAD_PAN_NORMAL; eyePos = EYE_NORMAL; break;    
    case DownLeft:
      headTiltPos = HEAD_TILT_DOWN; headPanPos = HEAD_PAN_LEFT; eyePos = EYE_LEFT; break; 
    case DownRight:
      headTiltPos = HEAD_TILT_DOWN; headPanPos = HEAD_PAN_RIGHT; eyePos = EYE_LEFT; break; 
    case Down:
      headTiltPos = HEAD_TILT_DOWN; headPanPos = HEAD_PAN_NORMAL; eyePos = EYE_NORMAL; break; 
    case Forward:
      headTiltPos = HEAD_TILT_NORMAL; headPanPos = HEAD_PAN_NORMAL; eyePos = EYE_NORMAL; break;
    case Left:
      headTiltPos = HEAD_TILT_NORMAL; headPanPos = HEAD_PAN_LEFT; eyePos = EYE_LEFT; break;
    case Right: 
      headTiltPos = HEAD_TILT_NORMAL; headPanPos = HEAD_PAN_RIGHT; eyePos = EYE_RIGHT; break;    
  }
  eyeServo.write(eyePos);
  headTiltServo.write(headTiltPos);
  headPanServo.write(headPanPos);
  
}
