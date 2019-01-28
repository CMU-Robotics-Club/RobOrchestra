#include <Servo.h>

Servo servo1;
Servo servo2;

void setup(){
  servo1.attach(5);
  servo2.attach(9);
  Serial.begin(9600);
}

void slamQuick(Servo servo)
{
servo.write(90);
delay(200);
servo.write(60);
}

void loop(){
  servo2.write(90);
  servo1.write(60);
  delay(200);
  servo1.write(90);
  servo2.write(60);
  delay(200);
}

