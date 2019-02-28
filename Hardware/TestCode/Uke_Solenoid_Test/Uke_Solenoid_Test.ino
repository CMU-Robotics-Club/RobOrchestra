//int solenoidPins[] = {23,45,27,29,31,33,37, 39,41,43,47};
//int numPins = 11;

int solenoidPins[] = {22,24,26,28, 23, 25, 27};
int numPins = 7;


void setup() {
  // put your setup code here, to run once:
 // for(int i = 0; i < numPins; i++) {
  //  pinMode(solenoidPins[i], OUTPUT);
   // digitalWrite(solenoidPins[i], LOW);
  //}
  pinMode(7, OUTPUT);
  digitalWrite(7, LOW);

}

void loop() {
  //for(int i = 0; i < numPins; i++) {
   
    //digitalWrite(solenoidPins[i], HIGH);
    digitalWrite(7, HIGH);
    delay(1000);
    //digitalWrite(solenoidPins[i], LOW);
    digitalWrite(7, LOW);
    delay(2000);
  //}

}
