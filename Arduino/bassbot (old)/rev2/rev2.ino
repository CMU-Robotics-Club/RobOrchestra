#define PWMA (11)
#define AIN2 (12)
#define AIN1 (13)
#define STBY (8)


void setup() {
  // put your setup code here, to run once:
  pinMode(PWMA,OUTPUT);
  pinMode(AIN2,OUTPUT);
  pinMode(AIN1,OUTPUT);
  pinMode(STBY,OUTPUT);
  
  digitalWrite(STBY,HIGH);
}

void loop() {
  // put your main code here, to run repeatedly: 
  digitalWrite(AIN1,HIGH);
  digitalWrite(AIN2,LOW);
  analogWrite(PWMA,255);
  delay(100);
  analogWrite(PWMA,0);
  delay(500);
}
