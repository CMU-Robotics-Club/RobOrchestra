#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>

#include <Servo.h>

MIDI_CREATE_DEFAULT_INSTANCE();
Servo servo1;

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
int SOL_14 = 22;
int SOL_15 = 23;
int SOL_16 = 24;

const int C[] = {SOL_15};
const int D[] = {SOL_2, SOL_6,SOL_10 };
const int E[] = { SOL_4, SOL_8,SOL_12,SOL_14};
const int F[] = { SOL_4, SOL_8,SOL_12,SOL_14};
const int G[] = {SOL_6, SOL_11, SOL_14};
const int A[] = {SOL_2, SOL_5};
const int B[] = {SOL_4, SOL_7,SOL_10,SOL_14};


const int Cm[] = {SOL_7,SOL_11,SOL_15};
const int Dm[] = {SOL_2, SOL_6, SOL_9 };
const int Em[] = { SOL_8,SOL_11,SOL_14 };
const int Fm[] = {SOL_1, SOL_9,SOL_15};
const int Gm[] = {SOL_6,SOL_11,SOL_13 };
const int Am[] = {SOL_2};
const int Bm[] = { SOL_4, SOL_6,SOL_10,SOL_14};

const int C7[] = {13};
const int D7[] = {SOL_2,SOL_10};
const int E7[] = { SOL_10,SOL_14 };
const int F7[] = { SOL_2,SOL_7,SOL_9};
const int G7[] = {SOL_6,SOL_9,SOL_14 };
const int CORD_A7[] = {SOL_5 };
const int B7[] = {SOL_2,SOL_7,SOL_10,SOL_14};


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

int which = 0;

void play1(int note[]){
  int len = sizeof(note);
  
  for(int i=0;i<len;i++){
    digitalWrite(note[i],HIGH);
  }
}

void play2(int note[]){
  int len = sizeof(note);
  for(int i=0;i<len;i++){
    digitalWrite(note[i],LOW);
  }
}
void noteOn(byte channel, byte pitch, byte velocity)
{
  int note;
  if(channel == 10) {
    note = getNote(pitch,velocity);
    if (velocity>0){
      play1(note);
    }

    else{
      play2(note);
      }
    }
}


void noteOff(byte channel, byte pitch, byte velocity)
{
  int note;
  if(channel == 10) {
    note = getNote(pitch,velocity);
    }
  play2(note);
}

void setup()
{
  MIDI.begin(MIDI_CHANNEL_OMNI);
  MIDI.setHandleNoteOn(noteOn);
  MIDI.setHandleNoteOff(noteOff);
  pinMode(SOL_1, OUTPUT);   
  pinMode(SOL_2, OUTPUT); 
  pinMode(SOL_3, OUTPUT);   
  pinMode(SOL_4, OUTPUT); 
  pinMode(SOL_5, OUTPUT);   
  pinMode(SOL_6, OUTPUT); 
  pinMode(SOL_7, OUTPUT);   
  pinMode(SOL_8, OUTPUT); 
  pinMode(SOL_9, OUTPUT);   
  pinMode(SOL_10, OUTPUT); 
  pinMode(SOL_11, OUTPUT);   
  pinMode(SOL_12, OUTPUT); 
  pinMode(SOL_13, OUTPUT);   
  pinMode(SOL_14, OUTPUT); 
  pinMode(SOL_15, OUTPUT);   
  pinMode(SOL_16, OUTPUT);    
  digitalWrite(SOL_1, LOW); 
  digitalWrite(SOL_2, LOW);
  digitalWrite(SOL_3, LOW); 
  digitalWrite(SOL_4, LOW);
  digitalWrite(SOL_5, LOW); 
  digitalWrite(SOL_6, LOW);
  digitalWrite(SOL_7, LOW); 
  digitalWrite(SOL_8, LOW);
  digitalWrite(SOL_9, LOW); 
  digitalWrite(SOL_10, LOW);
  digitalWrite(SOL_11, LOW); 
  digitalWrite(SOL_12, LOW); 
  digitalWrite(SOL_13, LOW); 
  digitalWrite(SOL_14, LOW); 
  digitalWrite(SOL_15, LOW); 
  digitalWrite(SOL_16, LOW); 

}

void loop()
{ 
  MIDI.read();
}


void hit() {
  servo1.write(100);
  delay(100);
}

void hit2() {
  servo1.write(10);
  delay(100);
}

