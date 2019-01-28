#include "WProgram.h"
#include "ROPacket.h"

ROPacket::ROPacket(byte myID, byte myType)
{
  ID=myID;
  type=myType;
}

byte ROPacket::getID()
{
  return ID;
}

byte ROPacket::getType()
{
  return type;
}

char* ROPacket::toString()
{
  str = (char*)malloc(4*sizeof(char));
  str[0] = type;
  str[1] = ID;
  str[2] = type;
  str[3] = '\0';
  return str;
}

void ROPacket::freePacket()
{
  if(str != NULL){
    free(str);
  }
}