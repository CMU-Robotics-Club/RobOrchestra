#include <MIDI.h>
#include <Servo.h>

Servo myservo;
Servo servo2;


void setup()
{
  myservo.attach(10);
  servo2.attach(11);
}

int which = 0;

void loop()
{ 
  
  if(which == 1){
    hit();
    delay(500);
    which = -1;
  }else{
    hit2();
     delay(500);
     which = 1;
   }
   
}

void hit() {
  
  myservo.write(85);
  delay(100);
  myservo.write(103);
  delay(100);

}


void hit2() {
  
  servo2.write(85);
  delay(100);
  servo2.write(103);
  delay(100);

}

