#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>

MIDI_CREATE_DEFAULT_INSTANCE();


//solenoids
int SOL_1 = 50;
int SOL_2 = 52;
int SOL_3 = 53;
int SOL_4 = 54;
int SOL_5 = 55;
int SOL_6 = 56;
int SOL_7 = 57;
int SOL_8 = 58;
int SOL_9 = 49;
int SOL_10 = 60;
int SOL_11 = 61;
int SOL_12 = 62;
int SOL_13 = 63;
int SOL_14 = 64;
int SOL_15 = 65;
int SOL_16 = 66;

//cord;  array
int len = 4;
const int C[] = {0,SOL_1,0,0};
const int D[] = {SOL_2, SOL_6,SOL_10,0};
const int E[] = { SOL_4, SOL_8,SOL_12,SOL_14};
const int F[] = { SOL_2, SOL_9,0,0};
const int G[] = {SOL_6, SOL_11, SOL_14,0};
const int A[] = {SOL_2, SOL_5,0,0};
const int B[] = {SOL_4, SOL_7,SOL_10,SOL_14};

const int Cm[] = {SOL_7,SOL_11,SOL_15,0};
const int Dm[] = {SOL_2, SOL_6, SOL_9 ,0};
const int Em[] = { SOL_8,SOL_11,SOL_14 ,0};
const int Fm[] = {SOL_1, SOL_9,SOL_15,0};
const int Gm[] = {SOL_6,SOL_11,SOL_13 ,0};
const int Am[] = {SOL_2,0,0,0};
const int Bm[] = { SOL_4, SOL_6,SOL_10,SOL_14};

const int C7[] = {SOL_13,0,0,0};
const int D7[] = {SOL_2,SOL_10,0,0};
const int E7[] = { SOL_10,SOL_14,0,0};
const int F7[] = { SOL_2,SOL_7,SOL_9,0};
const int G7[] = {SOL_6,SOL_9,SOL_14,0 };
const int CORD_A7[] = {SOL_5,0,0,0 };
const int B7[] = {SOL_2,SOL_7,SOL_10,SOL_14};

const int chords[][5] = {C,D,E,F,G,A,B};
const int chords_m[][5] = {Cm,Dm,Em,Fm,Gm,Am,Bm};
const int chords_7[][5] = {C7,D7,E7,F7,CORD_A7,B7};

int currentNote[] = {0,0,0,0};

void play1(){
     
  for(int i=0;i<len;i++){
    if (currentNote[i] != 0){
      digitalWrite(currentNote[i],HIGH);
    }
  }
  
}

void play2(){
  
  for(int i=0;i<len;i++){
    if (currentNote[i]!= 0){
      digitalWrite(currentNote[i],LOW);
      currentNote[i] = 0;
    }
  }
}


//minor - velocity 50
//major - velocity 100
//seventh - velocity 120

//pitch  C-61 D-62 E-63 F-64 G-65 A-66 B-67
void noteOn(byte channel, byte pitch, byte velocity)
{
    if(velocity == 120){
      for(int i = 0; i < len; i++){
        currentNote[i] = chords_7[pitch-60][i];
      }
    } else if (velocity == 100){
      if(pitch == 61){
        for (int i = 0; i<len;i++){
          currentNote[i] = C[i];
        }
      }
      if(pitch == 62){
        for (int i = 0; i<len;i++){
          currentNote[i] = D[i];
        }
      }
      if(pitch == 63){
        for (int i = 0; i<len;i++){
          currentNote[i] = E[i];
        }
      }
      if(pitch == 64){
        for (int i = 0; i<len;i++){
          currentNote[i] = F[i];
        }
      }
      if(pitch == 65){
        for (int i = 0; i<len;i++){
          currentNote[i] = G[i];
        }
      }
      if(pitch == 66){
        for (int i = 0; i<len;i++){
          currentNote[i] = A[i];
        }
      }
      if(pitch == 67){
        for (int i = 0; i<len;i++){
          currentNote[i] = B[i];
        }
      }
    } else if (velocity == 50){
      for(int i = 0; i < len; i++){
        currentNote[i] = chords_m[pitch-60][i];
      }
    }
  
   
    if (velocity>0){
      play1();
    } else{
      play2();
      }
}


void noteOff(byte channel, byte pitch, byte velocity)
{
  
  play2();
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


}

void loop()
{ 
  MIDI.read();
}


