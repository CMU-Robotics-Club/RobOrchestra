#include <Pixy2.h>
#include <math.h>
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
  int volume = 0;
  
  if (area < bounds[0]) {
    note = 60;
    volume = 10;
  }
  else if (area < bounds[1]) {
    note = 61;
    volume = 20;
  }
  else if (area < bounds[2]) {
    note = 62;
    volume = 30;
  }
  else if (area < bounds[3]) {
    note = 63;
    volume = 40;
  }
  else if (area < bounds[4]) {
    note = 64;
    volume = 50;
  }
  else if (area < bounds[5]) {
    note = 65;
    volume = 60;
  }
  else if (area < bounds[6]) {
    note = 66;
    volume = 70;
  }
  else if (area < bounds[7]) {
    note = 67;
    volume = 80;
  }
  else if (area < bounds[8]) {
    note = 68;
    volume = 90;
  }
  else if (area < bounds[9]) {
    note = 69;
    volume = 100;
  }
  else if (area < bounds[10]) {
    note = 70;
    volume = 110;
  }
  else {
    note = 71;
    volume = 120;
  }

//  A = 2.124;
//  B = 5.439*pow(10,9);
//  note = A*log(B*area);

  // 115200 baud
  Serial.println(volume);
}
