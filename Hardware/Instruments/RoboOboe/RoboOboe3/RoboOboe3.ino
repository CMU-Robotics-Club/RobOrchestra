#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>
#include <Servo.h>

MIDI_CREATE_DEFAULT_INSTANCE();

const int mychannel = 1; //Only respond to messages with this channel number

//Delays (in milliseconds) after pressing keys and stopping air, respectively)
//Turned these off
//int key_delay = 1;
//int air_delay = 1;//250;

//Ports for keys. Naming: K is "key" (one of the six main keys, actuated by solenoid), S is "servo" (other stuff, actuated by servo)
//Elements: Port, down position, up position, index in servo array, reset position. -1 if not applicable
int nokey[5] = {-1, -1, -1, -1, -1};
int BK[5] = {35, -1, -1, -1, -1};
int AK[5] = {34, -1, -1, -1, -1};
int GK[5] = {33, -1, -1, -1, -1};
int FsK[5] = {32, -1, -1, -1, -1};
int EK[5] = {31, -1, -1, -1, -1};
int DK[5] = {30, -1, -1, -1, -1};
int BfS[5] = {45, 80, 90, 0, 165}; //L3; reversed {45, 80, 90, 0, 165}
int BS[5] = {46, 100, 90, 1, 15}; //R4 {46, 100, 90, 1, 15}
int CS[5] = {42, 115, 90, 2, 16}; //R3 {44, 110, 90, 2, 15}
int CsS[5] = {44, 115, 85, 3, 20}; //R2 {42, 130, 100, 3, 25}
int EfS[5] = {47, 95, 75, 4, 10}; //L4 {47, 95, 75, 4, 10}
int AfS[5] = {43, 100, 90, 5, 15}; //L2 {43, 110, 90, 5, 15}
int BOS[5] = {50, 25, 50, 6, 65}; //R1; reversed {49, 40, 50, 6, 65}
int SOS[5] = {41, 115, 95, 7, 20}; //L1 {41, 115, 95, 7, 20}
//Port, down, up, index, reset

int airport = 36;

//General arrays so I can loop through stuff during setup
int *keyarray[14] = {BK, AK, GK, FsK, EK, DK, BfS, BS, CS, CsS, EfS, AfS, BOS, SOS};
const int nkeys = 14;
const int solenoidarray[] = {BK[0], AK[0], GK[0], FsK[0], EK[0], DK[0]};
const int nsolenoids = 6;
const int servoportarray[] = {BfS[0], BS[0], CS[0], CsS[0], EfS[0], AfS[0], BOS[0], SOS[0]};
Servo BfSO; Servo BSO; Servo CSO; Servo CsSO; Servo EfSO; Servo AfSO; Servo BOSO; Servo SOSO;
Servo servoarray[] = {BfSO, BSO, CSO, CsSO, EfSO, AfSO, BOSO, SOSO};

//Random parameters we might use somewhere
int nservos = 8;
const int fingeringlen = 8;
const int minpitch = 58;
const int maxpitch = 84; //Could theoretically go higher
const int numfingerings = maxpitch - minpitch + 1;

//Fingering chart
int *fingerings[numfingerings][fingeringlen] = 
{ {BK, AK, GK, FsK, EK, DK, CS, BfS}, //Low B flat
  {BK, AK, GK, FsK, EK, DK, CS, BS}, //Low B
  {BK, AK, GK, FsK, EK, DK, CS, nokey}, //Low C (middle C, MIDI value 60)
  {BK, AK, GK, FsK, EK, DK, CsS, nokey}, //Low C sharp
  {BK, AK, GK, FsK, EK, DK, nokey, nokey}, //Low D
  {BK, AK, GK, FsK, EK, DK, EfS, nokey}, //Low E flat
  {BK, AK, GK, FsK, EK, nokey, nokey, nokey}, //Low E
  {BK, AK, GK, FsK, DK, nokey, nokey, nokey}, //Low F (using forked F because minimality)
  {BK, AK, GK, FsK, nokey, nokey, nokey, nokey}, //F sharp
  {BK, AK, GK, nokey, nokey, nokey, nokey}, //G
  {BK, AK, GK, AfS, nokey, nokey, nokey, nokey}, //A flat
  {BK, AK, nokey, nokey, nokey, nokey, nokey, nokey}, //A
  {BK, AK, FsK, nokey, nokey, nokey, nokey, nokey}, //B flat
  {BK, nokey, nokey, nokey, nokey, nokey, nokey, nokey}, //B
  {BK, FsK, nokey, nokey, nokey, nokey, nokey, nokey}, //C (one octave above middle C, MIDI value 72)
  //{nokey, nokey, nokey, nokey, nokey, nokey, nokey, nokey}, //C sharp (probably need an alternate fingering, no half-hole because minimality)
  {BK, AK, GK, FsK, EK, DK, CsS, BOS}, //Another fingering for C sharp (probably need an alternate fingering, no half-hole because minimality)
  {BK, AK, GK, FsK, EK, DK, BOS, nokey}, //D (using back octave instead of half-hole, probably works)
  {BK, AK, GK, FsK, EK, DK, EfS, BOS}, //E flat (back octave not half-hole)
  {BK, AK, GK, FsK, EK, BOS, nokey, nokey}, //E
  {BK, AK, GK, FsK, DK, BOS, nokey, nokey}, //F (using forked F because minimality)
  {BK, AK, GK, FsK, BOS, nokey, nokey, nokey}, //High F sharp
  {BK, AK, GK, BOS, nokey, nokey, nokey, nokey}, //High G
  {BK, AK, GK, AfS, BOS, nokey, nokey, nokey}, //High A flat
  {BK, AK, SOS, nokey, nokey, nokey, nokey, nokey}, //High A (start using side octave key here, as a human would)
  {BK, AK, FsK, SOS, nokey, nokey, nokey, nokey}, //High B flat
  {BK, SOS, nokey, nokey, nokey, nokey, nokey, nokey}, //High B
  {BK, FsK, SOS, nokey, nokey, nokey, nokey, nokey}, //High C (two octaves above middle C, MIDI value 84). Any higher is non-trivial for a human and probably out of scope
};

void airOn(int pitch){
  digitalWrite(airport, HIGH);
}

void airOff(){
  digitalWrite(airport, LOW);
}

void keyDown(int key[]){
  if(key[0] == -1){
    //Dummy case for not doing anything
    return;
  }
  if(key[1] == -1){
      digitalWrite(key[0], HIGH); //Low voltage stops pressing down
  }
  else{
    for(int i = 0; i < nservos; i++){
      if(key[0] == servoportarray[i]){
        servoarray[key[3]].write(key[1]);
        return;
      }
    }
  }
}

void keyUp(int key[]){
  if(key[0] == -1){
    //Dummy case for not doing anything
    return;
  }
  if(key[2] == -1){
      digitalWrite(key[0], LOW); //Low voltage stops pressing down
  }
  else{
    for(int i = 0; i < nservos; i++){
      if(key[0] == servoportarray[i]){
        servoarray[key[3]].write(key[2]);
        return;
      }
    }
  }
}

void keyReset(int key[]){
  if(key[0] == -1){
    //Dummy case for not doing anything
    return;
  }
  if(key[4] == -1){
      digitalWrite(key[0], LOW); //Low voltage stops pressing down
  }
  else{
    for(int i = 0; i < nservos; i++){
      if(key[0] == servoportarray[i]){
        servoarray[key[3]].write(key[4]);
        return;
      }
    }
  }
}

void play(int pitch){
  for(int i=0;i<fingeringlen;i++){
    keyDown(fingerings[pitch-minpitch][i]);
  }/**/
  airOn(pitch);
}

void stopPlaying(){
  airOff();
  
  //And raise all keys (cutting power to solenoids is good)
  for(int i=0;i<nkeys;i++){
    keyUp(keyarray[i]);
  }
}

void handleNoteOff(byte channel, byte pitch, byte velocity)
{
  if(channel == mychannel){
    stopPlaying();
  }
}

void handleNoteOn(byte channel, byte pitch, byte velocity)
{
  int mypitch = pitch + 0;
  //If wrong channel, ignore
  if(channel != mychannel) {
    return;
  }
  
  //If it's actually a stop command, stop
  if(velocity == 0){
    stopPlaying();
    return;
  }/**/

  for(int i=0;i<nkeys;i++){
    keyUp(keyarray[i]);
  }
  
  //Else play the pitch
  while(mypitch < minpitch/**/) {
    mypitch += 12;
  }
  while(mypitch > maxpitch/**/) {
    mypitch -= 12;
  }/**/
  play(mypitch);
}


void setup()
{
  for(int x = 0; x < nservos; x++){
    servoarray[x].attach(servoportarray[x]);
  }
  for(int x = 0; x < nsolenoids; x++){
    pinMode(solenoidarray[x], OUTPUT);
    digitalWrite(solenoidarray[x], LOW);
  }
  for(int i=0;i<nkeys;i++){
    keyReset(keyarray[i]);
  }/**/
  pinMode(airport, OUTPUT);
  digitalWrite(airport, LOW);
  Serial.begin(115200);
  MIDI.setHandleNoteOn(handleNoteOn);
  MIDI.setHandleNoteOff(handleNoteOff);
  MIDI.begin(MIDI_CHANNEL_OMNI);
  MIDI.turnThruOn();
}

void loop()
{
  MIDI.read();
  //keyUp(CsS);
  /*for(int i=0;i<nkeys;i++){
    keyUp(keyarray[i]);
  }
  delay(1000);
  for(int i=0;i<nkeys;i++){
    keyUp(keyarray[i]);
  }
  delay(1000);/**/
}

