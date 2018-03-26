#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>


#include <Servo.h>

MIDI_CREATE_DEFAULT_INSTANCE();

////// 50 regular   100: minor   120 7
//Currently listens on channel 10??

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

 int C[] = {SOL_15};
 int D[] = {SOL_2, SOL_6,SOL_10 };
 int E[] = { SOL_4, SOL_8,SOL_12,SOL_14};
 int F[] = { SOL_4, SOL_8,SOL_12,SOL_14};
 int G[] = {SOL_6, SOL_11, SOL_14};
 int A[] = {SOL_2, SOL_5};
 int B[] = {SOL_4, SOL_7,SOL_10,SOL_14};


 int Cm[] = {SOL_7,SOL_11,SOL_15};
 int Dm[] = {SOL_2, SOL_6, SOL_9 };
 int Em[] = { SOL_8,SOL_11,SOL_14 };
 int Fm[] = {SOL_1, SOL_9,SOL_15};
 int Gm[] = {SOL_6,SOL_11,SOL_13 };
 int Am[] = {SOL_2};
 int Bm[] = { SOL_4, SOL_6,SOL_10,SOL_14};

 int C7[] = {13}; //Should this be SOL_13 (which is also just 13)??
 int D7[] = {SOL_2,SOL_10};
 int E7[] = { SOL_10,SOL_14 };
 int F7[] = { SOL_2,SOL_7,SOL_9};
 int G7[] = {SOL_6,SOL_9,SOL_14 };
 int CORD_A7[] = {SOL_5 }; //Why is this not just called A7??
 int B7[] = {SOL_2,SOL_7,SOL_10,SOL_14};


 int* major[][4] = {C,D,E,F,G,A,B};
 int* minor[][4] = {Cm,Dm,Em,Fm,Gm,Am,Bm};
 int* other[][4] = {C7,D7,E7,F7,CORD_A7,B7};

/*  note number
 *  C = 60
 *  D = 62
 *  E = 64
 *  F = 65
 *  G = 67
 *  A = 79
 *  B = 71  
 */

//I'm going to comment this out and steal the code and try to make it make sense
/*
int getNote(int pitch, int velocity) { //NOT COMPILING!!! Return an array??

  int Note;
  if(pitch == 60){
    Note = 0;
  }else if(pitch == 62){
    Note == 1; //Why double-equals??
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
*/

int which = 0; //Next direction to sweep the arm

void play(int note[]){
  int len = sizeof(note);
  
  for(int i=0;i<len;i++){
    digitalWrite(note[i],HIGH);
  }
  
  delay(50);

  if(which == 1){
    hit();
    delay(50);
    which = -1;
  }else{
    hit2();
     delay(50);
     which = 1;
   }
  
  
  
  for(int i=0;i<len;i++){
    digitalWrite(note[i],LOW);
  }
}


void handleNoteOn(byte channel, byte pitch, byte velocity)
{
  int note;
  if(channel == 10) {
    //My attempt to fix this
    int Note; //C is case sensitive, I hope...
    if(pitch == 60){
      Note = 0;
    }else if(pitch == 62){
      Note = 1; //Why double-equals??
    }else if(pitch == 64){
      Note = 2;
    }else if(pitch == 65){
      Note = 3;
    }else if(pitch == 67){
      Note = 4;
    }else if(pitch == 67){
      Note = 5;
    }else if(pitch == 71){
      Note = 6;
    }
     int* chord[4] = {0, 0, 0, 0}; //This cannot possibly be right...
    if(velocity == 50){
      for(int x = 0; x < 4; x++){
        chord[x] = minor[Note][x];
      }
    } else if (velocity == 100){
      for(int x = 0; x < 4; x++){
        chord[x] = major[Note][x];
      }
    } else if (velocity == 120){
      for(int x = 0; x < 4; x++){
        chord[x] = other[Note][x]; //7th??
      }
    }
    play(*chord);

    //Original code
    //note = getNote(pitch,velocity);
    //play(note);
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


void hit() {
  servo1.write(100);
  delay(100);
}

void hit2() {
  servo1.write(10);
  delay(100);
}

