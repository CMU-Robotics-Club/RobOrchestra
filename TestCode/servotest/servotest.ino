#include <Servo.h>

Servo myservo;
Servo myservo2;

//int x[] = {1, 2, 3, 4, 5};

void setup() {
  //pinMode(LED, OUTPUT);
  //Serial3.begin(115200);
  myservo2.attach(5);

}

void loop() {
  hit();
  
}


void hit(){

  myservo2.write(100); //Up (80 before)
  delay(200);
  myservo2.write(70); //Down (103 before)
  delay(200);

}

