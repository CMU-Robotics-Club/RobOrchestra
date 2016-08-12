#include "WProgram.h"
#include "ROQueue.h"

ROQueue::ROQueue(int initLength){
  length = 0;
  capacity = initLength;
  packets = (packet**)malloc(sizeof(packet*)*capacity);
  startIndex = 0;
  endIndex = 0;
}

ROQueue::ROQueue(){
  ROQueue(8);
}

byte ROQueue::enqueue(packet* toAdd){
  packets[endIndex] = toAdd;
  endIndex = (endIndex+1)%capacity;
  length++;
  if(capacity == length) return ROQUEUE_OUT_OF_SPACE;
  if(capacity - length < 15) return ROQUEUE_LOW_ON_SPACE;
  return 0;
}

packet* ROQueue::dequeue(){
  packet* toReturn = packets[startIndex];
  startIndex = (startIndex + 1)%capacity;
  length--;
  return toReturn;
}

packet* ROQueue::peek(){
  return packets[startIndex];
}

int ROQueue::getLength(){
  return length;
}