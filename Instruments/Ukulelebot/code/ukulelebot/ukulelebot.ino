#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>
#include <Servo.h>

MIDI_CREATE_DEFAULT_INSTANCE();

Servo servo1;
int strum_delay = 50;
int sol_delay = 50;
int which = 0; //Next direction to sweep the arm

int SOL_1 = 22;
int SOL_2 = 23;
int SOL_3 = 24;
int SOL_4 = 25;
int SOL_5 = 26;
int SOL_6 = 27;
int SOL_7 = 28;
int SOL_8 = 29;
int SOL_9 = 30;
int SOL_10 = 31;
int SOL_11 = 32;
int SOL_12 = 33;
int SOL_13 = 34;
int SOL_14 = 35;
int SOL_15 = 36;
int SOL_16 = 37;

 int C[4] = {SOL_15,0,0,0};
 int D[4] = {SOL_2, SOL_6,SOL_10, 0};
 int E[4] = {SOL_4, SOL_8,SOL_12,SOL_14};
 int F[4] = {SOL_4, SOL_8,SOL_12,SOL_14};
 int G[4] = {SOL_6, SOL_11, SOL_14, 0};
 int A[4] = {SOL_2, SOL_5, 0, 0};
 int B[4] = {SOL_4, SOL_7,SOL_10,SOL_14};


 int Cm[4] = {SOL_7,SOL_11,SOL_15};
 int Dm[4] = {SOL_2, SOL_6, SOL_9 };
 int Em[4] = {SOL_8,SOL_11,SOL_14 };
 int Fm[4] = {SOL_1, SOL_9,SOL_15};
 int Gm[4] = {SOL_6,SOL_11,SOL_13 };
 int Am[4] = {SOL_2,0,0,0};
 int Bm[4] = {SOL_4, SOL_6,SOL_10,SOL_14};

 int C7[4] = {SOL_13,0,0,0}; //Should this be SOL_13 (which is also just 13)??
 int D7[4] = {SOL_2,SOL_10,0,0};
 int E7[4] = {SOL_10,SOL_14,0,0 };
 int F7[4] = {SOL_2,SOL_7,SOL_9,0};
 int G7[4] = {SOL_6,SOL_9,SOL_14,0};
 int CHORD_A7[4] = {SOL_5,0,0,0}; //Why is this not just called A7??
 int B7[4] = {SOL_2,SOL_7,SOL_10,SOL_14};


 int *major[7] = {C,D,E,F,G,A,B};
 int *minor[7] = {Cm,Dm,Em,Fm,Gm,Am,Bm};
 int *other[7] = {C7,D7,E7,F7,CHORD_A7,B7};

/*  note number */
  int C_midi = 60;
  int D_midi = 62;
  int E_midi = 64;
  int F_midi = 65;
  int G_midi = 67;
  int A_midi = 79;
  int B_midi = 71; 

void play(int note[]){
  int len = sizeof(note);
  
  for(int i=0;i<len;i++){
    digitalWrite(note[i],HIGH);
  }
  
  delay(sol_delay);

  if(which == 1){
    hit();
    which = -1;
  } else{
    hit2();
     which = 1;
  }
  
  
  
  for(int i=0;i<len;i++){
    digitalWrite(note[i],LOW);
  }
}


void handleNoteOn(byte channel, byte pitch, byte velocity)
{
  int note;
  pitch = pitch % 12 + 60;
  
  if(channel == 3) {
    int Note; 
    
    if(pitch == C_midi){
        Note = 0;
    } else if(pitch == D_midi){
      Note = 1; //Why double-equals??
    } else if(pitch == E_midi){
        Note = 2;
    } else if(pitch == F_midi){
        Note = 3;
    } else if(pitch == G_midi){
        Note = 4;
    } else if(pitch == A_midi){
        Note = 5;
    } else if(pitch == B_midi){
        Note = 6;
    }

    int chord[4] = {0,0,0,0};
    
    if(velocity == 50) {
      for(int x = 0; x < 4; x++){
        chord[x] = major[Note][x];
      }   
    } else if(velocity == 100) {
      for(int x = 0; x < 4; x++){
        chord[x] = minor[Note][x];
      }
    } else {
      for(int x = 0; x < 4; x++){
        chord[x] = other[Note][x];
      }
    }

    play(chord);
  }
}


void setup()
{
  servo1.attach(53);
  MIDI.setHandleNoteOn(handleNoteOn);
  MIDI.begin(MIDI_CHANNEL_OMNI);
  MIDI.turnThruOn();
}

void loop()
{ 
  MIDI.read();
}


void hit() {
  strummer.write(100);
  delay(strum_delay);
}

void hit2() {
  strummer.write(10);
  delay(strum_delay);
}

