#include <Wire.h>
#include <SPI.h>
#include "outputVector.h"
#include <PIDLoop.h>
#include <Pixy2.h>
#include <Pixy2CCC.h>
#include <Pixy2I2C.h>
#include <Pixy2Line.h>
#include <Pixy2SPI_SS.h>
#include <Pixy2UART.h>
#include <Pixy2Video.h>
#include <TPixy2.h>
#include <ZumoBuzzer.h>
#include <ZumoMotors.h>
#include <stdio.h>
#define MAX 100
//
// begin license header
//
// This file is part of Pixy CMUcam5 or "Pixy" for short
//
// All Pixy source code is provided under the terms of the
// GNU General Public License v2 (http://www.gnu.org/licenses/gpl-2.0.html).
// Those wishing to use Pixy source code, software and/or
// technologies under different licensing terms should contact us at
// cmucam@cs.cmu.edu. Such licensing terms are available for
// all portions of the Pixy codebase presented here.
//
// end license header
// https://docs.pixycam.com/wiki/doku.php?id=wiki:v2:hooking_up_pixy_to_a_microcontroller_-28like_an_arduino-29
//

#include <Pixy2.h>

// This is the main Pixy object


Pixy2 pixy;

void setup()
{
  Serial.begin(9600);
  Serial.print("Starting...\n");
//  output = createWriter("positions.txt");
  pixy.init();
}

vect a = {0,0,0.0,0.0};
int prevx = 0;
int prevy = 0;
int prevTime = 0;

String toBePrinted; 
vect* getvect() {
  vect *output = &a;
  return output;
}

void loop()
{
  int i;
  // grab blocks!
  pixy.ccc.getBlocks();

  // If there are detect blocks, print them!
  if (pixy.ccc.numBlocks)
  {
       int x = pixy.ccc.blocks[0].m_x;
       int y = pixy.ccc.blocks[0].m_y;
       int newTime = millis();
       if(prevx == 0 && prevy == 0) {
          prevy = y;
          prevx = x;
       }
       float dx = ((float)x - (float)prevx)/((float)(newTime - prevTime));
       float dy = ((float)y - (float)prevy)/((float)(newTime - prevTime));
       a = {x, y, dx, dy};
       vect *curLocPoint = &a;


       char xnum[MAX];
       char ynum[MAX];
       itoa(curLocPoint->x, xnum, 10);
       itoa(curLocPoint->y, ynum, 10);
       prevx = x;
       prevy = y;
       prevTime = newTime;
       toBePrinted = String("");
       toBePrinted += xnum;
       toBePrinted += ", ";
       toBePrinted += ynum;
       toBePrinted += ", ";
       toBePrinted += dx;
       toBePrinted += ", ";
       toBePrinted += dy;
       toBePrinted += ", ";
       toBePrinted += newTime;
       Serial.println(toBePrinted);
       /*Serial.print(xnum);
       Serial.print(", ");
       Serial.print(ynum);
       Serial.print(", ");
       Serial.print(dx, 6);
       Serial.print(", ");
       Serial.print(dy, 6);
       Serial.print(", ");
       Serial.print(newTime, 6);
       Serial.println("");*/

//    void keyPressed()
//    {
//    	output.flush();
//	output.close();
//	exit();
//    }
  }
}
