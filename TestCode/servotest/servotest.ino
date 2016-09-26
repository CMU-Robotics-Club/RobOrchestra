#include <Servo.h>

Servo myservo;

int x[] = {1, 2, 3, 4, 5};

void setup() {
  //pinMode(LED, OUTPUT);
  //Serial3.begin(115200);
  myservo.attach(10);
  for(int x = 0; x < 10; x++){
    hit(250, 10);
    hit(750, 50);
    /*hit(500, 10);
    hit(250, 10);
    hit(250, 10);
    hit(1000, 20);*/
  }
  exit(0);
}

void loop() {
  // put your main code here, to run repeatedly:
  
}

void hit(int i){
  myservo.write(80); //Up (80 before)
  delay(30);
  myservo.write(103); //Down (103 before)
  delay(30);
  delay(i-60);
}

/*for(int x = 0; x < i; x++){

}*/

void hit(int i, int a){
  myservo.write(103-a); //Up (80 before)
  delay(30);
  myservo.write(103); //Down (103 before)
  delay(30);
  delay(i-60);
}

