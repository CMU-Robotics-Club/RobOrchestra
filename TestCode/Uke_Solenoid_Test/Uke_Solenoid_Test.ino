int solenoidPins[4] = {1,2,3,4};
int numPins = 4;



void setup() {
  // put your setup code here, to run once:
  for(int i = 0; i < numPins; i++) {
    pinMode(solenoidPins[i], OUTPUT);
    digitalWrite(solenoidPins[i], LOW);
  }

}

void loop() {
  for(int i = 0; i < numPins; i++) {
    digitalWrite(solenoidPins[i], HIGH);
    delay(500);
    digitalWrite(solenoidPins[i], LOW);
  }

}
