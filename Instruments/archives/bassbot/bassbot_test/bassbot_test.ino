/*
Initial test for BassBot.  Opens and closes the pedal at a constant rate.
4/6/14
*/

#define SOL1 8
#define SOL2 9

void setup(){
  pinMode(SOL1, OUTPUT);
  pinMode(SOL2, OUTPUT);
}

void hit (int delayTime) {
  digitalWrite(SOL2, HIGH);
  delay(delayTime);
  digitalWrite(SOL2, LOW);
  delay(10);
  digitalWrite(SOL1, HIGH);
  delay(delayTime);
  digitalWrite(SOL1, LOW);
  delay(10); 
}

void loop(){
  hit(90);
  hit(90);
  delay(500);
}
