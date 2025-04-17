int note = 60;

void setup()
{
  Serial.begin(9600);
  Serial.print("Starting...\n");
  note = 60;
}
 
void loop()
{
  Serial.println(note);
  note++;
  if(note > 72) {
    note = 60;
  }
  delay(1000);
}
