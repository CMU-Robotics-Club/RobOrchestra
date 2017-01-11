#include "WProgram.h"
#include "ROsolenoid.h"

ROsolenoid::ROsolenoid()
{
}

// initiates the object on the given pin, and sets it to LOW
ROsolenoid::ROsolenoid(byte pin)
{
	_pin = pin;
	pinMode(_pin, OUTPUT);
	_state = LOW;
	digitalWrite(_pin,_state);
	_timer = 0;
}

//if a timer expires, switch it off
void ROsolenoid::loop()
{
	if(_timer != 0 && _timer < millis()){
		_state = (_state==HIGH)?LOW:HIGH;
		digitalWrite(_pin,_state);
		_timer = 0;
	}
}

//set the state and turn off any timers
void ROsolenoid::setState(byte state)
{
	if(state != HIGH && state != LOW) return;
	_state = state;
	digitalWrite(_pin,_state);
	_timer = 0;
}

//set the state but set a timer
void ROsolenoid::setTime(byte state, int duration)
{
	if(state != HIGH && state != LOW) return;
	if(duration <= 0) return;
	_state = state;
	digitalWrite(_pin,_state);
	_timer = millis()+duration;
}

//get time remaining until toggle back
int ROsolenoid::getTime()
{
	return (_timer==0)?0:((int)(_timer-millis()));
}

//get current state
byte ROsolenoid::getState()
{
	return _state;
}