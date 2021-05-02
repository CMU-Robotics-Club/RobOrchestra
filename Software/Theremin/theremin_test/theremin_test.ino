#include <Pixy2.h>
// This is the main Pixy object
Pixy2 pixy;

void setup()
{
  Serial.begin(115200);
  Serial.print("Starting...\n");
  pixy.init();
}
 
void loop()
{
  // grab blocks!
  pixy.ccc.getBlocks();
  int width = pixy.ccc.blocks[i].m_width; //from 1 to 316
  int height = pixy.ccc.blocks[i].m_height; //from 1 to 208

  int inc = 900;
  
  int bounds[] = {inc, 2*inc, 3*inc, 4*inc, 5*inc, 6*inc, 7*inc, 8*inc, 9*inc, 10*inc, 11*inc, 12*inc};
  int area = width * height;

  int note = 0;
  
  if (area < bounds[0]) note = 60;
  else if (area < bounds[1]) note = 61;
  else if (area < bounds[2]) note = 62;
  else if (area < bounds[3]) note = 63;
  else if (area < bounds[4]) note = 64;
  else if (area < bounds[5]) note = 65;
  else if (area < bounds[6]) note = 66;
  else if (area < bounds[7]) note = 67;
  else if (area < bounds[8]) note = 68;
  else if (area < bounds[9]) note = 69;
  else if (area < bounds[10]) note = 70;
  else note = 71;

  Serial.println(note);
}
