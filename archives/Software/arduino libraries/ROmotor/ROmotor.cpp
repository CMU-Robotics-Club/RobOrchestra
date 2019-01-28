#include "WProgram.h"
#include "ROmotor.h"

ROmotor::ROmotor(byte dirAPin, byte dirBpin, byte pwmPin)
{
	_dirAPin = dirAPin;
	_dirBPin = dirBPin;
	_pwmPin = pwmPin;
	_speed = 0;
	_timer = 0;
	pinMode(dirAPin,OUTPUT);
	pinMode(dirBPin,OUTPUT);
	pinMode(pwmPin,OUTPUT);
	writeSpeed();
}

void ROmotor::loop()
{
	if(_timer != 0 && _timer < millis()){
		_speed = 0;
		writeSpeed();
		_timer = 0;
	}
}

void ROmotor::setSpeed(int speed)
{
	if(speed < -100 || speed > 100) return;
	_speed = speed;
	writeSpeed();
}

void ROmotor::setTime(int speed, int duration)
{
	if(speed < -100 || speed > 100) return;
	if(duration <= 0) return;
	_speed = speed;
	writeSpeed();
	_timer = duration + millis();
}

int ROmotor::getSpeed()
{
	return _speed;
}

int ROmotor::getTime()
{
	return (_timer==0)?0:((int)(_timer - millis()));
}

void writeSpeed()
{
	analogWrite(pwmPin,map(abs(_speed,0,100,0,255)));
	if(_speed > 0){
		digitalWrite(dirAPin,HIGH);
		digitalWrite(dirBPin,LOW);
	} else if(_speed < 0){
		digitalWrite(dirAPin,LOW);
		digitalWrite(dirBPin,HIGH);
	} else {
		digitalWrite(dirAPin,LOW);
		digitalWrite(dirBPin,LOW);
	}
}