#include <Pixy2.h>
// This is the main Pixy object
Pixy2 pixy;
float fx;
float fy;
float w = 0.98;
float oldx;
float oldoldx;
float oldy;
float oldoldy;

int cooldown = 0;

void setup()
{
  Serial.begin(115200);
  Serial.print("Starting...\n");
  pixy.init();

  fx = pixy.ccc.blocks[0].m_x; //from 1 to 316??
  oldx = fx; oldoldx = fx;
  fy = pixy.ccc.blocks[0].m_y; //from 1 to 208??
  oldy = fy; oldoldy = oldy;
}
 
void loop()
{
  cooldown--;
  // grab blocks!
  pixy.ccc.getBlocks(true,1);
  unsigned int width = pixy.ccc.blocks[0].m_width; //from 1 to 316
  unsigned int height = pixy.ccc.blocks[0].m_height; //from 1 to 208

  unsigned int x = pixy.ccc.blocks[0].m_x; //from 1 to 316??
  unsigned int y = pixy.ccc.blocks[0].m_y; //from 1 to 208??

  

  fx = w*fx + (1-w)*x;
  fy = w*fy + (1-w)*y;

  bool xmax = (oldx > oldoldx && oldx > fx);
  bool xmin = (oldx < oldoldx && oldx < fx);
  bool ymax = (oldy > oldoldy && oldy > fy);
  bool ymin = (oldy < oldoldy && oldy < fy);

  
  if( (xmax || xmin || ymax || ymin) && (width*height > 0 && cooldown <= 0) ){

    Serial.println("Beat");
    cooldown = 6;

  }
  else{
    Serial.println("");
  }

  oldoldx = oldx; oldx = fx;
  oldoldy = oldy; oldy = fy;
  delay(50);
}
