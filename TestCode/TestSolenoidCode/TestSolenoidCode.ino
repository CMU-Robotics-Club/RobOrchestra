int n = 31;

void setup() {
  // put your setup code here, to run once:
  pinMode(n, OUTPUT);
  digitalWrite(n, LOW);
}

void loop() {
  // put your main code here, to run repeatedly:
  digitalWrite(n, HIGH);
  delay(500);
  digitalWrite(n, LOW);
  delay(1000);
}
