#include "WProgram.h"
#include "ROPacket.h"

#ifndef ROQueue_h
#define ROQueue_h
#define packet ROPacket
#define ROQUEUE_OUT_OF_SPACE 2
#define ROQUEUE_LOW_ON_SPACE 1

class ROQueue{
  public:
    ROQueue(int initLength);
    ROQueue();
    byte enqueue(packet* toAdd);
    packet* dequeue();
    packet* peek();
    int getLength();
  private:
    packet** packets;
    int length;
    int capacity;
    int startIndex;
    int endIndex;
};

#endif