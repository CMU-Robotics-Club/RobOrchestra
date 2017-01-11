#include "WProgram.h"
#include "ROservo.h"
#include "..\Servo\Servo.h"

ROservo::ROservo()
{
}

// initiates the object on the given pin, sets a default angle, and lists highest potential angle
ROservo::ROservo(byte pin, int dangle, int angles)
{
	_pin = pin;
	_dangle = dangle;
	_angles = angles;
	_s.attach(_pin);
	_angle = _dangle;
	setAngle(_angle);
	_timer = 0;
}

//if a timer expires, switch it to default angle
void ROservo::loop()
{
	if(_timer != 0 && _timer < millis()){
		_angle = _dangle;
		setAngle(_angle);
		_timer = 0;
	}
}

//set the angle and turn off any timers
void ROservo::setAngle(int angle)
{
	if(angle < 0 || angle > _angles) return;
	_angle = angle;
	_s.write((_angle*180)/_angles);
	_timer = 0;
}

//set the default angle of the servo
void ROservo::setDangle(int dangle)
{
	if(dangle < 0 || dangle > _angles) return;
	_dangle = dangle;
}

//set the angle and set a timer
void ROservo::setTime(int angle, int duration)
{
	if(angle < 0 || angle > _angles) return;
	if(duration <= 0) return;
	_angle = angle;
	setAngle(angle);
	_timer = millis()+duration;
}

//get time remaining until toggle back
int ROservo::getTime()
{
	return (_timer==0)?0:((int)(_timer-millis()));
}

//get current state
int ROservo::getAngle()
{
	return _angle;
}

//get current defualt angle
int ROservo::getDangle()
{
	return _dangle;
}