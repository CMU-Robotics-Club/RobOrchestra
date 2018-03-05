int solenoidPin = 50; //change to output pin connected on the Arduino


void setup() {
  pinMode(solenoidPin, OUTPUT); //sets pin to receive output
  digitalWrite(solenoidPin, LOW);
 
}

void loop() {
  digitalWrite(solenoidPin, HIGH); //pushes solenoid out

  delay(500); //Wait 1000 milliseconds
  digitalWrite(solenoidPin, LOW); //releases push force
  delay(500); //Wait 1000 milliseconds

}
