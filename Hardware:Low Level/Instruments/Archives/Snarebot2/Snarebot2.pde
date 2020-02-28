/*
* RobOrchestra Snarebot 2.0
 * Written by: Daniel Shope (webster32@gmail.com) 
 * Last Modified: 04/14/2010
 * 
 * Controls the Snarebot 2.0 (built Spring 2010)
 * Using (2) HS-422 Servos and (2) Pull Solenoids
 * 
 * Listens on digital pins (2) and (3) for a LOW interrupt
 * which signals either a regular hit or a buzzRoll().
 * The ISR sets a state flag which is handled by the next loop iteration. For
 * regular hit, alternates between left and right for the fastest response.
 * 
 * CAUTION: Do not exceed activation time longer than 30 seconds
 * for the solenoids as this will cause damage
 * 
 * FUTURE ADDITIONS: Change to non-blocking delay
 * Create function that sets up or down flag, position, and delay. This will
 * replace the delay function, timing being handled by a millis() loop.
 * 
 */

#include <Servo.h>

#define TRIGGER_PIN 2
#define TRIGGER_INTERRUPT 0 //hardware pin 2, interrupt 1

#define ROLL_PIN 3
#define ROLL_INTERRUPT 1

#define LEFT 0
#define LEFT_SOLENOID 6
#define LEFT_SERVO 9
#define LEFT_UP 90
#define LEFT_DOWN 70
#define LEFT_ROLL_UP_LOW 80
#define LEFT_ROLL_UP_MEDIUM 85

#define RIGHT 1
#define RIGHT_SOLENOID 7
#define RIGHT_SERVO 10
#define RIGHT_UP 90
#define RIGHT_DOWN 110
#define RIGHT_ROLL_UP_LOW 105
#define RIGHT_ROLL_UP_MEDIUM 115

#define DELAY_ROLL_MEDIUM 60
#define DELAY_DOWN 65
#define DELAY_DOWN_SHORT 50
#define VOLUME_LOW 0
#define VOLUME_MEDIUM 1

#define ST_NO_ACTION 0
#define ST_DO_HIT 1
#define ST_DO_ROLL 2

Servo leftServo; Servo rightServo;    //setup the servo objects
unsigned long last_tm = 0;            //used for non-blocking delay
byte stickJustHit = RIGHT;            //keeps track for stick alternation
int myState = ST_NO_ACTION;           //default state
//int nextPos = UP;
int k;                                //global int used for cycle tracking

void setup() {  
  pinMode(TRIGGER_PIN, INPUT);
  pinMode(LEFT_SOLENOID, OUTPUT); pinMode(RIGHT_SOLENOID, OUTPUT);
  attachInterrupt(TRIGGER_INTERRUPT, isrHit, CHANGE); //would like to use "low" in the future
  attachInterrupt(ROLL_INTERRUPT, isrRoll, CHANGE); //would like to use "low" in the future
  leftServo.attach(LEFT_SERVO); rightServo.attach(RIGHT_SERVO);
  resetAll();
  //doDemo();
}

void loop() {
  evaluateState();
//doDemo();
}

void evaluateState() {
  switch(myState) {
     case ST_DO_HIT:
       myState = ST_NO_ACTION;
       if (stickJustHit==RIGHT) {
         stickJustHit = LEFT;
       } else {
         stickJustHit = RIGHT;
       }
       drumHit(stickJustHit,false);
       break;
     case ST_DO_ROLL:
       singleStrokeRoll(500);
       break;
  }
}

//release solenoids and raise sticks above drum
void resetAll() {
  leftServo.write(LEFT_UP); rightServo.write(RIGHT_UP);
  digitalWrite(LEFT_SOLENOID, LOW); digitalWrite(RIGHT_SOLENOID, LOW);
}

//for regular hits, just servo, for accents, use solenoid too
void drumHit(byte side, boolean doAccent) {
  if (side==LEFT) {
    if (doAccent==true) {
      digitalWrite(LEFT_SOLENOID, LOW);
      leftServo.write(LEFT_DOWN); delay(20);
      digitalWrite(LEFT_SOLENOID, HIGH); delay(50);
    } else {
      leftServo.write(LEFT_DOWN);
      delay(75);
    }
    leftServo.write(LEFT_UP);
  } 
  else {
    if (doAccent==true) {
      digitalWrite(RIGHT_SOLENOID, LOW);
      rightServo.write(RIGHT_DOWN); delay(20);
      digitalWrite(RIGHT_SOLENOID, HIGH); delay(50);
    } else {
      rightServo.write(RIGHT_DOWN);
      delay(75);
    }
    rightServo.write(RIGHT_UP);
  }
}

//activate both sticks (servos and solenoids)
void hitAll() {
  digitalWrite(LEFT_SOLENOID, LOW);
  digitalWrite(RIGHT_SOLENOID, LOW);
  leftServo.write(LEFT_DOWN);
  rightServo.write(RIGHT_DOWN);
  delay(5);
  digitalWrite(LEFT_SOLENOID, HIGH);
  digitalWrite(RIGHT_SOLENOID, HIGH);
  delay(75);
  leftServo.write(LEFT_UP);
  rightServo.write(RIGHT_UP);
}

void isrHit() {
 if (digitalRead(TRIGGER_PIN)==HIGH) { //activate
   myState = ST_DO_HIT;
 }
}

void isrRoll() {
 if (digitalRead(ROLL_PIN)==HIGH) { //activate
   myState = ST_DO_ROLL;
 } else {
   myState = ST_NO_ACTION; //stop roll
 }
}
