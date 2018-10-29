
#define ENABLE (4)
#define INPUT_A (5)
#define INPUT_B (6)

void setup() {
  // put your setup code here, to run once:
  pinMode(ENABLE,OUTPUT);
  pinMode(INPUT_A,OUTPUT);
  pinMode(INPUT_B,OUTPUT);
  digitalWrite(ENABLE,HIGH);
}

void loop() {
  // put your main code here, to run repeatedly: 
  analogWrite(INPUT_A,255);
  analogWrite(INPUT_B,0);
}
