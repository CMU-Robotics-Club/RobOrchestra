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
  unsigned int width = pixy.ccc.blocks[0].m_width; //from 1 to 316
  unsigned int height = pixy.ccc.blocks[0].m_height; //from 1 to 208

  unsigned int inc = 900;
  
  unsigned int bounds[] = {400, 700, 1000, 1400, 2000, 2800, 4000, 7000, 14000, 28000, 50000, 100000};
  unsigned int area = width * height;

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

  // 115200 baud
  Serial.println(note);
}
