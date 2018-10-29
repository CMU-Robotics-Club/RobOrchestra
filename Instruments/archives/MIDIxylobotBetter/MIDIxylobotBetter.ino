
#include "MIDI.h"

#define NOTE_C 22
#define NOTE_C_SHARP 42
#define NOTE_D 23
#define NOTE_D_SHARP 38                           
#define NOTE_E 24
#define NOTE_F 25
#define NOTE_F_SHARP 34
#define NOTE_G 26
#define NOTE_G_SHARP 35
#define NOTE_A 27
#define NOTE_A_SHARP 36
#define NOTE_B 28
#define NOTE_C_HIGH 29
#define NOTE_C_SHARP_HIGH 37
#define NOTE_D_HIGH 30
#define NOTE_D_SHARP_HIGH 39
#define NOTE_E_HIGH 31

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

byte mapNote(byte note) {
  if (note <= 31) {
    return note;
  }
  else if (note == 32) {
    return NOTE_C_SHARP;
  }
  else if (note == 33) {
    return NOTE_D_SHARP;
  }
  else if (note == 34) {
    return NOTE_F_SHARP;
  }
  else if (note == 35) {
    return NOTE_G_SHARP;
  }
  else if (note == 36) {
    return NOTE_A_SHARP;
  }
  else if (note == 37) {
    return NOTE_C_SHARP_HIGH;
  }
  else if (note == 38) {
    return NOTE_D_SHARP_HIGH;
  }
}

void writeNote(byte note){//note must be from 0 to 16
  for(byte i = 0; i < NUMBINS; ++i){
//    digitalWrite(pins[i],(note>>i)&1);
//      digitalWrite(pins[i], HIGH);
  }
  byte newNote = mapNote(note + BIN0);
  digitalWrite(newNote,HIGH);
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
