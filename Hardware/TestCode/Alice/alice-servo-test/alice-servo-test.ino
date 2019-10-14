#include <Servo.h>

Servo servo_right;
Servo servo_left;

void setup() {
  // put your setup code here, to run once:
  servo_right.attach(2);
  servo_left.attach(3);
  servo_right.write(95);
  servo_left.write(120);
}

void loop() {
  // put your main code here, to run repeatedly:
  servo_right.write(100);
  delay(1000);
  servo_right.write(95);
  servo_left.write(107);
  delay(1000);
  servo_left.write(120);
  
}
