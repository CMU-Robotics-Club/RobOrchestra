/*
ROcomms.h - Library for RobOrchestra Communication over
our standardized 4 prong square low power molex cables.
NOT FOR USE ON THE MASTER
Created by Andrew Burks, Spring 2010
*/

#ifndef ROcomms_h
#define ROcomms_h

#include "WProgram.h"

#define dataLen 10
#define bufferLen 15
#define timeOut 100

#define PACNOTE 1
#define PACADMIN 2
#define PACINST 3
#define PACREST 4
#define PACNONE 0

class ROcomms
{
public:
	ROcomms();
	ROcomms(byte* ID, byte numID, void (*dataFunc)(byte ID, int type, char* data, byte len));
	ROcomms(byte* ID, byte numID, void (*noteFunc)(byte ID, char* data, byte len), void (*adminFunc)(byte ID, char* data, byte len), void (*instFunc)(byte ID, char* data, byte len)); 
	void loop();
	long ourHexToLong(char* hex, byte len);
	void print(char* in);
	void print(char in);
	void print(byte in);
	void print(int in);
	void print(long in);
	void println(char* in);
	void println(char in);
	void println(byte in);
	void println(int in);
	void println(long in);
private:
	char* _data;
	char* _buffer;
	byte* _ID;
	byte _numID;
	byte _numFunc;
	void (*_dataFunc)(byte ID, int type, char* data, byte len);
	void (*_noteFunc)(byte ID, char* data, byte len);
	void (*_adminFunc)(byte ID, char* data, byte len);
	void (*_instFunc)(byte ID, char* data, byte len);
	int getPacType(char in);
	long iPow(int base, byte pow);
};
#endif