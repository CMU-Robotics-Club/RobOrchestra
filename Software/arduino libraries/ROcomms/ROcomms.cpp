#include "WProgram.h"
#include "ROcomms.h"

ROcomms::ROcomms()//non functional
{
	
}

ROcomms::ROcomms(byte* ID, byte numID, void (*dataFunc)(byte ID, int type, char* data, byte len))
{
	_ID = ID;
	_numID = numID;
	_dataFunc = dataFunc;
	_numFunc = 1;
	_buffer = (char*)malloc(bufferLen*sizeof(char));
	_data = (char*)malloc(dataLen*sizeof(char));
	Serial.begin(9600);
}

ROcomms::ROcomms(byte* ID, byte numID, void (*noteFunc)(byte ID, char* data, byte len), void (*adminFunc)(byte ID, char* data, byte len), void (*instFunc)(byte ID, char* data, byte len))
{ 
	_ID = ID;
	_numID = numID;
	_noteFunc = noteFunc;
	_adminFunc = adminFunc;
	_instFunc = instFunc;
	_numFunc = 3;
	_buffer = (char*)malloc(bufferLen*sizeof(char));
	_data = (char*)malloc(dataLen*sizeof(char));
	Serial.begin(9600);
}	


void ROcomms::loop()
{
	if(!Serial.available()) return;
	//this makes sure that there is something waiting

	long timeStamp;//checks for timeouts
	byte i = 0;
	while(i < bufferLen) {
		timeStamp = millis();
		while(!Serial.available()){
			if(timeStamp + timeOut < millis()) return;//timeout error
		}
		_buffer[i] = Serial.read();
		if(getPacType(_buffer[i]) != 0 && getPacType(_buffer[i]) == (-1)*getPacType(_buffer[0])) break;//end of packet
		if(i > 0 || getPacType(_buffer[i]) > 0) i++;//increments i while waiting for the beginning of the buffer to be the beginning of a packet
	}
	if(i+1 == bufferLen) return; //overflow error

	//now we know we have a good packet of length i
	byte temp = 0;
	for(byte j = 0; j < _numID; ++j){//test for appropriate ID
		if(_buffer[1]-'0' == _ID[j]) temp=1;
	}
	if(temp == 0) return; //packet not for me
	
	for(byte j = 0; j <= i-3; ++j){
		_data[j] = _buffer[j+2];
	}
	if(_numFunc == 1)
		_dataFunc(_buffer[1]-'0', getPacType(_buffer[0]), _data, i-2);
	if(_numFunc == 3){
		switch(getPacType(_buffer[0])){
		case PACNOTE:
			_noteFunc(_buffer[1]-'0', _data,i-2);
			return;
		case PACADMIN:
			_adminFunc(_buffer[1]-'0', _data,i-2);
			return;
		case PACINST:
			_instFunc(_buffer[1]-'0', _data,i-2);
			return;
		default:
			return;
		}
	}
}




int ROcomms::getPacType(char in)
{
	switch(in){
	case '[':
		return PACNOTE;
	case '{':
		return PACADMIN;
	case '(':
		return PACINST;
	case ']':
		return (-1)*PACNOTE;
	case '}':
		return (-1)*PACADMIN;
	case ')':
		return (-1)*PACINST;
	case '.':
		return PACREST;
	default:
		return PACNONE;
	}
}


long ROcomms::ourHexToLong(char* hex, byte len)
{
	long result = 0;
	for(int i = 0; i < len; ++i){
		result += (hex[i]-'A')*iPow(16,(len-i-1));
	}
	return result;
}
long ROcomms::iPow(int base, byte pow)
{
	long result = 1;
	for(byte i = 0; i < pow; ++i){
		result *= base;
	}
	return result;
}



void ROcomms::print(char* in)
{
	Serial.print(in);
}
void ROcomms::print(char in)
{
	Serial.print(in);
}
void ROcomms::print(byte in)
{
	Serial.print(in,DEC);
}
void ROcomms::print(int in)
{
	Serial.print(in,DEC);
}
void ROcomms::print(long in)
{
	Serial.print(in,DEC);
}
void ROcomms::println(char* in)
{
	Serial.println(in);
}
void ROcomms::println(char in)
{
	Serial.println(in);
}
void ROcomms::println(byte in)
{
	Serial.println(in,DEC);
}
void ROcomms::println(int in)
{
	Serial.println(in,DEC);
}
void ROcomms::println(long in)
{
	Serial.println(in,DEC);
}