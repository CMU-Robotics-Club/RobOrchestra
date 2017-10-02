int solenoidPin = 3; //change to output pin connected on the Arduino
int solenoidPin2 = 5;
int solenoidPin3 = 7;

void setup() {
  pinMode(solenoidPin, OUTPUT); //sets pin to receive output
  pinMode(solenoidPin2, OUTPUT);
  digitalWrite(solenoidPin, LOW);
  digitalWrite(solenoidPin2, LOW);
  digitalWrite(solenoidPin3, LOW);
 
}

void loop() {
  digitalWrite(solenoidPin, HIGH); //pushes solenoid out
  digitalWrite(solenoidPin2, HIGH);
  digitalWrite(solenoidPin3, HIGH);
  delay(500); //Wait 1000 milliseconds
  digitalWrite(solenoidPin, LOW); //releases push force
  digitalWrite(solenoidPin2, LOW);
  digitalWrite(solenoidPin3, LOW);
  delay(500); //Wait 1000 milliseconds

}
