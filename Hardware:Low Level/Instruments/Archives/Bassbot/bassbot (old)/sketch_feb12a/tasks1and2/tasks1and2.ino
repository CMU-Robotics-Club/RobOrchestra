int currentLight = 9;
int currentState = 0;
int previousState = 255;

void setup() {
  pinMode(9, OUTPUT);
  pinMode(10, OUTPUT);
  pinMode(11, OUTPUT);
  pinMode(2, INPUT);
  pinMode(3, INPUT);
  Serial.begin(9600);
}

void loop() {
  
  previousState = analogRead(A0);
    
  previousState = map(previousState,0,1023,0,255);
  
  if (digitalRead(2) == HIGH && currentState == 0) {
    currentState = previousState;
  } else if (digitalRead(2) == HIGH) {
    previousState = currentState;
    currentState = 0;
  }
  
  if (currentState != 0) currentState = previousState;
  
  if (digitalRead(3) == HIGH && currentLight == 11) {
    currentLight = 9;
  } else if (digitalRead(3) == HIGH) {
    currentLight++;
  }
  
  digitalWrite(9, LOW);
  digitalWrite(10, LOW);
  digitalWrite(11, LOW);
  analogWrite(currentLight, currentState);
  delay(100);
}

