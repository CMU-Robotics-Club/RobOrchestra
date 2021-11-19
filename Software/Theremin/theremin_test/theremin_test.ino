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
  pixy.ccc.getBlocks(true,1); // pitch (blue)
  unsigned int pitchWidth = pixy.ccc.blocks[0].m_width; //from 1 to 316
  unsigned int pitchHeight = pixy.ccc.blocks[0].m_height; //from 1 to 208

  pixy.ccc.getBlocks(true,2); // volume (red)
  unsigned int volumeWidth = pixy.ccc.blocks[0].m_width; //from 1 to 316
  unsigned int volumeHeight = pixy.ccc.blocks[0].m_height; //from 1 to 208

  unsigned int inc = 900;
  
  unsigned int bounds[] = {400, 700, 1000, 1400, 2000, 2800, 4000, 7000, 14000, 28000, 50000, 100000};
  unsigned int pitchArea = pitchWidth * pitchHeight;
  unsigned int volumeArea = volumeWidth * volumeHeight;

  int note = 0;
  int volume = 0;
  
  if (pitchArea < bounds[0]) {
    note = 60;
  }
  else if (pitchArea < bounds[1]) {
    note = 61;
  }
  else if (pitchArea < bounds[2]) {
    note = 62;
  }
  else if (pitchArea < bounds[3]) {
    note = 63;
  }
  else if (pitchArea < bounds[4]) {
    note = 64;
  }
  else if (pitchArea < bounds[5]) {
    note = 65;
  }
  else if (pitchArea < bounds[6]) {
    note = 66;
  }
  else if (pitchArea < bounds[7]) {
    note = 67;
  }
  else if (pitchArea < bounds[8]) {
    note = 68;
  }
  else if (pitchArea < bounds[9]) {
    note = 69;
  }
  else if (pitchArea < bounds[10]) {
    note = 70;
  }
  else {
    note = 71;
  }

  if (volumeArea < bounds[0]) {
    volume = 10;
  }
  else if (volumeArea < bounds[1]) {
    volume = 20;
  }
  else if (volumeArea < bounds[2]) {
    volume = 30;
  }
  else if (volumeArea < bounds[3]) {
    volume = 40;
  }
  else if (volumeArea < bounds[4]) {
    volume = 50;
  }
  else if (volumeArea < bounds[5]) {
    volume = 60;
  }
  else if (volumeArea < bounds[6]) {
    volume = 70;
  }
  else if (volumeArea < bounds[7]) {
    volume = 80;
  }
  else if (volumeArea < bounds[8]) {
    volume = 90;
  }
  else if (volumeArea < bounds[9]) {
    volume = 100;
  }
  else if (volumeArea < bounds[10]) {
    volume = 110;
  }
  else {
    volume = 120;
  }

//  A = 2.124;
//  B = 5.439*pow(10,9);
//  note = A*log(B*area);

  // 115200 baud
  Serial.print(note);
  Serial.print(" ");
  Serial.print(volume);
  Serial.print(" \n");
}
