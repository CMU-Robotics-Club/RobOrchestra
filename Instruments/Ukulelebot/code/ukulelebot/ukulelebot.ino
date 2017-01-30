#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>


#include <Servo.h>


//#include "def.h"
//#include "xylo.h"

MIDI_CREATE_DEFAULT_INSTANCE();

////// 50 regular   100: minor   120 7


int SOL_1 = 1;
int SOL_2 = 2;
int SOL_3 = 3;
int SOL_4 = 4;
int SOL_5 = 5;
int SOL_6 = 6;
int SOL_7 = 7;
int SOL_8 = 8;
int SOL_9 = 9;
int SOL_10 = 10;
int SOL_11 = 11;
int SOL_12 = 12;
int SOL_13 = 13;
int SOL_14 = 14;
int SOL_15 = 15;
int SOL_16 = 16;

const int C[] = {15};
const int D[] = {2, 6,10 };
const int E[] = { 4, 8,12,14};
const int F[] = { 4, 8,12,14};
const int G[] = {6, 11, 14};
const int A[] = {2, 5};
const int B[] = {4, 7,10,14};


const int Cm[] = {7,11,15};
const int Dm[] = {2, 6, 9 };
const int Em[] = { 8,11,14 };
const int Fm[] = {1, 9,15};
const int Gm[] = {6,11,13 };
const int Am[] = {2};
const int Bm[] = { 4, 6,10,14};

const int C7[] = {13};
const int D7[] = {2,10};
const int E7[] = { 10,14 };
const int F7[] = { 2,7,9};
const int G7[] = {6,9,14 };
const int CORD_A7[] = {5 };
const int B7[] = {2,7,10,14};


const int major[][4] = {C,D,E,F,G,A,B};
const int minor[][4] = {Cm,Dm,Em,Fm,Gm,Am,Bm};
const int other[][4] = {C7,D7,E7,F7,CORD_A7,B7};

/*  note number
 *  C = 60
 *  D = 62
 *  E = 64
 *  F = 65
 *  G = 67
 *  A = 79
 *  B = 71  
 */

int getNote(int pitch, int velocity) {

  int Note;
  if(pitch == 60){
    Note = 0;
  }else if(pitch == 62){
    Note == 1;
  }else if(pitch == 64){
    Note == 2;
  }else if(pitch == 65){
    Note == 3;
  }else if(pitch == 67){
    Note == 4;
  }else if(pitch == 67){
    Note == 5;
  }else if(pitch == 71){
    Note == 6;
  }

  if(velocity == 50){
    return minor[Note];
  } else if (velocity == 100){
    return major[Note];
  } else if (velocity == 120){
    return other[Note];
  }
}

void play(int note[]){
  int len = sizeof(note);
  
  for(int i=0;i<len;i++){
    digitalWrite(note[i],HIGH);
  }
  
  delay(50);
  
  for(int i=0;i<len;i++){
    digitalWrite(note[i],LOW);
  }
}


void handleNoteOn(byte channel, byte pitch, byte velocity)
{
  int note;
  if(channel == 10) {
    note = getNote(pitch,velocity);
    play(note);
    }
}


void setup()
{
  MIDI.setHandleNoteOn(handleNoteOn);
  MIDI.begin(MIDI_CHANNEL_OMNI);
  MIDI.turnThruOn();
}

void loop()
{ 
  MIDI.read();
}







