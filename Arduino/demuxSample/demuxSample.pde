#define BIN0 13
#define BIN1 12
#define BIN2 11
#define BIN3 10


void setup() {
  pinMode(BIN0,OUTPUT);
  pinMode(BIN1,OUTPUT);
  pinMode(BIN2,OUTPUT);
  pinMode(BIN3,OUTPUT);
}


void loop() {
  while(1){
    digitalWrite(BIN0,LOW);
    digitalWrite(BIN1,LOW);
    digitalWrite(BIN2,LOW);
    digitalWrite(BIN3,LOW);
    delay(1000);
    digitalWrite(BIN0,LOW);
    digitalWrite(BIN1,LOW);
    digitalWrite(BIN2,LOW);
    digitalWrite(BIN3,HIGH);
    delay(1000);
    digitalWrite(BIN0,LOW);
    digitalWrite(BIN1,LOW);
    digitalWrite(BIN2,HIGH);
    digitalWrite(BIN3,LOW);
    delay(1000);
    digitalWrite(BIN0,LOW);
    digitalWrite(BIN1,LOW);
    digitalWrite(BIN2,HIGH);
    digitalWrite(BIN3,HIGH);
    delay(1000);
    digitalWrite(BIN0,LOW);
    digitalWrite(BIN1,HIGH);
    digitalWrite(BIN2,LOW);
    digitalWrite(BIN3,LOW);
    delay(1000);
    digitalWrite(BIN0,LOW);
    digitalWrite(BIN1,HIGH);
    digitalWrite(BIN2,LOW);
    digitalWrite(BIN3,HIGH);
    delay(1000);
    digitalWrite(BIN0,LOW);
    digitalWrite(BIN1,HIGH);
    digitalWrite(BIN2,HIGH);
    digitalWrite(BIN3,LOW);
    delay(1000);
    digitalWrite(BIN0,LOW);
    digitalWrite(BIN1,HIGH);
    digitalWrite(BIN2,HIGH);
    digitalWrite(BIN3,HIGH);
    delay(1000);
    digitalWrite(BIN0,HIGH);
    digitalWrite(BIN1,LOW);
    digitalWrite(BIN2,LOW);
    digitalWrite(BIN3,LOW);
    delay(1000);
    digitalWrite(BIN0,HIGH);
    digitalWrite(BIN1,LOW);
    digitalWrite(BIN2,LOW);
    digitalWrite(BIN3,HIGH);
    delay(1000);
    digitalWrite(BIN0,HIGH);
    digitalWrite(BIN1,LOW);
    digitalWrite(BIN2,HIGH);
    digitalWrite(BIN3,LOW);
    delay(1000);
    digitalWrite(BIN0,HIGH);
    digitalWrite(BIN1,LOW);
    digitalWrite(BIN2,HIGH);
    digitalWrite(BIN3,HIGH);
    delay(1000);
    digitalWrite(BIN0,HIGH);
    digitalWrite(BIN1,HIGH);
    digitalWrite(BIN2,LOW);
    digitalWrite(BIN3,LOW);
    delay(1000);
    digitalWrite(BIN0,HIGH);
    digitalWrite(BIN1,HIGH);
    digitalWrite(BIN2,LOW);
    digitalWrite(BIN3,HIGH);
    delay(1000);
    digitalWrite(BIN0,HIGH);
    digitalWrite(BIN1,HIGH);
    digitalWrite(BIN2,HIGH);
    digitalWrite(BIN3,LOW);
    delay(1000);
    digitalWrite(BIN0,HIGH);
    digitalWrite(BIN1,HIGH);
    digitalWrite(BIN2,HIGH);
    digitalWrite(BIN3,HIGH);
    delay(1000);
  }


}
