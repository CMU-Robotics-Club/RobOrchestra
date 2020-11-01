#define REDPIN 11
#define BLUEPIN 10
#define GREENPIN 9

int rVal, gVal, bVal;
void setup()
{
  Serial.begin(9600);
  
  pinMode(REDPIN, OUTPUT);
  pinMode(BLUEPIN, OUTPUT);
  pinMode(GREENPIN, OUTPUT);
  
  attachInterrupt(0, inter, CHANGE);
  rVal, gVal, bVal = 0;
}

void loop()
{
  if (Serial.available())
  {
   // Serial.println(Serial.read());
   char byte1 = Serial.read();
   
   if(byte1 == 'r')
    {
      rVal = Serial.parseInt();
    }
    else if(byte1 == 'g')
    {
      gVal = Serial.parseInt();
    }
    else if (byte1 == 'b')
    {
      bVal = Serial.parseInt();
    }
  
  analogWrite(REDPIN,rVal);
  analogWrite(BLUEPIN,bVal);
  analogWrite(GREENPIN,gVal);
  
  }

}

void inter()//called when pin2 state changes
{
  digitalWrite(REDPIN, HIGH);
  digitalWrite(BLUEPIN, LOW);
  digitalWrite(GREENPIN, LOW);
}
