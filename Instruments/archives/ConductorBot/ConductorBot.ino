#include <Servo.h>

#define PITCH_UP 90
#define PITCH_DOWN 30
#define YAW_LEFT 180
#define YAW_RIGHT 0
#define YAW_MIDDLE 90

Servo servoYaw;
Servo servoPitch;

void setup() {
  servoYaw.attach(5);
  servoPitch.attach(6);
}


void loop() {
  int timing = 667;
  servoYaw.write(YAW_MIDDLE);
  servoPitch.write(PITCH_UP);
  delay(timing);
  servoPitch.write(PITCH_DOWN);
  delay(timing);
  servoYaw.write(YAW_LEFT);
  delay(timing);
  servoYaw.write(YAW_RIGHT);
  delay(timing);
}
