#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>

#include "xylo.h"

#define STARTNOTE 60
#define ENDNOTE 76 //Equal to the highest note
#define KEY_UP_TIME 40

MIDI_CREATE_DEFAULT_INSTANCE();

unsigned long startTime = 0;

int pinnumbers[] = {22, 50, 23, 38, 24, 25, 34, 26, 35, 27, 36, 28, 29, 37, 30, 51, 31}; //Ports for C, C#, D, ..., high D#, high E
unsigned long pintimes[] = {0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0}; //Time since turned on
bool toPlay[17] = {false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false, false}; //Stores whether we want to play the solenoids next cycle; updates as we run
int nPins = 17;

void handleNoteOn(byte channel, byte pitch, byte velocity){
  //This function queues up notes to be unplayed
  //if(channel != 1) return; //Only play channel 1
  if(velocity == 0) return; //Ignore velocity 0
  
  int noteIndex = pitch;
  //Rescale notes
  while(noteIndex < STARTNOTE){
    noteIndex += 12;
  }
  while(noteIndex > ENDNOTE){
    noteIndex -= 12;
  }

  digitalWrite(pinnumbers[noteIndex-STARTNOTE], HIGH);
  pintimes[noteIndex-STARTNOTE] = millis();
}

void setup()
{
  xylo_init();
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
  //Check for and process new MIDI messages, then if it's time to release notes, do that
  MIDI.read();

  for(int x = 0; x < nPins; x++){
    if(millis() - pintimes[x] > KEY_UP_TIME){
      int keyPin = pinnumbers[x]; // map the note to the pin
      digitalWrite(keyPin, LOW);
    }
  }
}
