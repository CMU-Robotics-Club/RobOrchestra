int currentLight;
int currentState;
int previousState = HIGH;

void setup() {
  pinMode(9, OUTPUT);
  pinMode(10, OUTPUT);
  pinMode(11, OUTPUT);
  pinMode(2, INPUT);
  pinMode(3, INPUT);
  Serial.begin(9600);
}

void loop() {
  Serial.println(digitalRead(2));
  delay(1000);
/*
  if (digitalRead(2) == HIGH && currentState == 0) {
    currentState = previousState;
  } else if (digitalRead(2) == HIGH) {
    previousState = currentState;
    currentState = 0;
  }
  
  if (digitalRead(3) == HIGH && currentLight == 11) {
    currentLight = 9;
  } else {
    currentLight++;
  }
  digitalWrite(currentLight, currentState);
*/
}
