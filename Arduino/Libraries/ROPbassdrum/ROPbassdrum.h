/*
ROPbassdrum.h - Subclass of ROPacket
*/

#ifndef ROPbassdrum_h
#define ROPbassdrum_h

#include "WProgram.h"
#include "ROPacket.h"

class ROPbassdrum : public ROPacket
{
  public:
    ROPbassdrum();
    ROPbassdrum(byte myID, byte myType, byte myHitType);
    byte getHitType();
    char* toString();
  private:
    byte hitType;
};

#endif