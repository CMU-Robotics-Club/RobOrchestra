
#include "MIDI.h"

#define CHANNEL 2
#define STARTNOTE 60
#define ENDNOTE 76

#define BIN0 22
#define NUMBINS 17
#define ENABLE 13
#define LED 6
#define LED2 7

#define ONTIME 11
#define QUIETNOTE 32

byte pins[NUMBINS];
long stopTime;
byte numMap[17] = {0,10,1,11,2,3,12,4,13,5,14,6,7,15,8,16,9};
boolean ready;

void setup(){
  ready = true;
  for(byte i = 0; i < NUMBINS; ++i){
    pins[i] = BIN0+i;
    pinMode(pins[i],OUTPUT);
    digitalWrite(pins[i], HIGH);
    delay(50);
    digitalWrite(pins[i], LOW);
  }
  pinMode(ENABLE,OUTPUT);
  
  MIDI.begin(CHANNEL);
  writeNote(QUIETNOTE);
}

void loop(){
  
  if(MIDI.read() && ready){
    if(MIDI.getType() == NoteOn){
      if(MIDI.getData1() >= STARTNOTE && MIDI.getData1() <= ENDNOTE){
        stopTime = millis() + ONTIME;
        ready = false;
        writeNote(numMap[MIDI.getData1() - STARTNOTE]);
//          writeNote(MIDI.getData1() - STARTNOTE);
        }
    }
  }
  checkNote();
}

void writeNote(byte note){//note must be from 0 to 16
  for(byte i = 0; i < NUMBINS; ++i){
//    digitalWrite(pins[i],(note>>i)&1);
//      digitalWrite(pins[i], HIGH);
  }
  digitalWrite(note + BIN0,HIGH);
  digitalWrite(13, HIGH);

//  if(note < 16){
//    digitalWrite(ENABLE,LOW);
//    
//  } else {
//    digitalWrite(ENABLE,HIGH);
//  }
  delay(50);
  for(byte i = 0; i < NUMBINS; ++i){
//    digitalWrite(pins[i],(note>>i)&1);
//      digitalWrite(pins[i], LOW);
  }
  digitalWrite(note + BIN0,LOW);
  digitalWrite(13, LOW);


}

void checkNote(){
  if(!ready && stopTime < millis()){
    writeNote(QUIETNOTE);
    ready = true;
  }
}
