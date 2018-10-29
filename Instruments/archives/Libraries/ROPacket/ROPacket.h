/*
ROPacket.h - Parent class for RobOrchestra Data Packets
*/

#ifndef ROPacket_h
#define ROPacket_h

#include "WProgram.h"

class ROPacket
{
  public:
    ROPacket(byte myID, byte myType);
    byte getID();
    byte getType();
    char* toString();
    void freePacket();
  protected:
    byte ID;
    byte type;
    char* str;
};

#endif