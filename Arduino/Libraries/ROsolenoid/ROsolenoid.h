/*
ROsolenoid.h - Library for RobOrchestra Solenoid Control
Created by Andrew Burks, Spring 2010
*/

#ifndef ROsolenoid_h
#define ROsolenoid_h

#include "WProgram.h"

class ROsolenoid
{
public:
	ROsolenoid();
	ROsolenoid(byte pin);
	void loop();
	void setState(byte state);
	void setTime(byte state, int duration);
	byte getState();
	int getTime();
private:
	byte _pin;
	byte _state;
	long _timer;
};

#endif
