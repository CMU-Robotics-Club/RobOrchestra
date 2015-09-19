/*
ROmotor.h - Library for RobOrchestra motor control
Created by Andrew Burks, Spring 2010
*/

#ifndef ROmotor_h
#define ROmotor_h

#include "WProgram.h"

class ROmotor
{
public:
	ROmotor(byte dirAPin, byte dirBpin, byte pwmPin);
	void loop();
	void setSpeed(int speed);
	void setTime(int speed, int duration);
	int getSpeed();
	int getTime();
private:
	void writeSpeed();
	byte _dirAPin;
	byte _dirBPin;
	byte _pwmPin;
	int _speed;
	long _timer;
};

#endif