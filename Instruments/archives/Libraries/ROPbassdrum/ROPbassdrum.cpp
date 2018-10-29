#include "WProgram.h"
#include "ROPbassdrum.h"

ROPbassdrum::ROPbassdrum() : ROPacket(0,0)
{
  hitType = 0;
}

ROPbassdrum::ROPbassdrum(byte myID, byte myType, byte myHitType) : ROPacket(myID, myType)
{
  hitType = myHitType;
}

byte ROPbassdrum::getHitType()
{
  return hitType;
}

char* ROPbassdrum::toString()
{
  str = (char*)malloc(5*sizeof(char));
  str[0] = type;
  str[1] = ID;
  str[2] = hitType;
  str[3] = type;
  str[4] = '\0';
}