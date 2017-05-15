int solenoidPin = 52; //change to output pin connected on the Arduino
int solenoidPin2 = 48;

void setup() {
  pinMode(solenoidPin, OUTPUT); //sets pin to receive output
  pinMode(solenoidPin2, OUTPUT);
  digitalWrite(solenoidPin, LOW);
  digitalWrite(solenoidPin2, LOW);
 
}

void loop() {
  digitalWrite(solenoidPin, HIGH); //pushes solenoid out
  digitalWrite(solenoidPin2, HIGH);
  delay(5000); //Wait 1000 milliseconds
  digitalWrite(solenoidPin, LOW); //releases push force
  digitalWrite(solenoidPin2, LOW);
  delay(2000); //Wait 1000 milliseconds

}
