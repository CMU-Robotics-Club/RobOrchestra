
#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>

#include "xylo.h"

#define STARTNOTE 60
#define ENDNOTE 76 //1 above highest note (which is 75)
#define KEY_UP_TIME 50


#define LED 13
MIDI_CREATE_DEFAULT_INSTANCE();

//int played = 0; //Does nothing?
unsigned long startTime = 0;


int pinnumbers[] = {22, 13, 23, 38, 24, 25, 34, 26, 35, 27, 36, 28, 29, 37, 30, 39, 31}; //Ports for C, C#, D, ..., high D, high E
bool toPlay[17] = {false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false}; //Stores whether we want to play the solenoids next cycle; updates as we run
int nPins = 17;

void handleNoteOn(byte channel, byte pitch, byte velocity){
  //This function queues up notes to be played
  if(velocity == 0) return; //Ignore velocity 0
  
  int noteIndex = pitch;

  //Rescale notes
  while(noteIndex < STARTNOTE){
    noteIndex += 12;
  }
  while(noteIndex > ENDNOTE){
    noteIndex -= 12;
  }

  toPlay[noteIndex - 60] = true;

  //Add extra time delay any time we get new messages so chords don't get split
  startTime += 10;
  unsigned long curTime = millis();
  if(startTime > curTime){
    startTime = curTime;
  }
}

void playNotes(){
  //Plays any queued notes, then clears the queue
  for(int x = 0; x < nPins; x++){
    if(toPlay[x]){
      Serial.println("a");
      int keyPin = pinnumbers[x]; // map the note to the pin
      digitalWrite(keyPin, HIGH);
    }
  }
  //digitalWrite(LED, HIGH);
  delay(KEY_UP_TIME);
  for(int x = 0; x < nPins; x++){
    if(toPlay[x]){
      int keyPin = pinnumbers[x]; // map the note to the pin
      digitalWrite(keyPin, LOW);
    }
  }

  //Reset toPlay array to all false
  for(int x = 0; x < nPins; x++){
    toPlay[x] = false;
  }
}

void setup()
{
  xylo_init();
  pinMode(LED, OUTPUT);
  Serial.begin(115200);
  for(int x = 0; x < nPins; x++){
    pinMode(pinnumbers[x], OUTPUT);
    digitalWrite(pinnumbers[x], LOW);
  }
  MIDI.setHandleNoteOn(handleNoteOn);
  MIDI.begin(MIDI_CHANNEL_OMNI);          // Launch MIDI and listen to channel 1
  MIDI.turnThruOn();
  startTime = millis();
}

void loop()
{
  //Check for and process new MIDI messages, then if it's time to play notes, play notes
  MIDI.read();

  unsigned long curTime = millis();
  if(curTime - startTime > KEY_UP_TIME){
    startTime = curTime;
    playNotes();
  }
}













