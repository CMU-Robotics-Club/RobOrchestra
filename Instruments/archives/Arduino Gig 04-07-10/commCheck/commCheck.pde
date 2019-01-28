#include <ROcomms.h>

ROcomms c;

void setup()
{
  c = ROcomms(0,dataFunc);
}


void loop()
{
  c.loop();
  
}

void dataFunc(int type, char* data, byte len){
  Serial.println(type,DEC);
  for(int i = 0; i < len; ++i){
    Serial.print(data[i]);
  }
  Serial.println();
}

