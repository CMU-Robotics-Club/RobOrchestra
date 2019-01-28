/*
ROservo.h - Library for RobOrchestra Servo Control
Created by Andrew Burks, Spring 2010
*/

#ifndef ROservo_h
#define ROservo_h

#include "WProgram.h"
#include "..\Servo\Servo.h"

class ROservo
{
public:
	ROservo();
	ROservo(byte pin, int dangle, int angles);
	void loop();
	void setAngle(int angle);
	void setDangle(int dangle);
	void setTime(int angle, int duration);
	int getTime();
	int getAngle();
	int getDangle();
private:
	byte _pin;
	int _angles;
	int _dangle;
	int _angle;
	long _timer;
	Servo _s;
};

#endif
