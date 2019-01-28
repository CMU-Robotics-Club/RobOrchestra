#include <Servo.h>

Servo s[7];
long start;

void setup(){
  for(byte i = 0; i < 7; ++i){
    s[i].attach(4+i);
    s[i].write(100);
  }
  start = millis();
}

void loop(){
  delay(5000);
  for(byte i = 0; i < 7; ++i)
    s[i].write(70);
}
