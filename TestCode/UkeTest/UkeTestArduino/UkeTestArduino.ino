#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>

MIDI_CREATE_DEFAULT_INSTANCE();

int solenoidPin = 50;
//int solenoidPin2 = 52;


void noteOn(byte channel, byte note, byte velocity)
{
  if(velocity>0){
    digitalWrite(solenoidPin, HIGH);
    //digitalWrite(solenoidPin2, HIGH);
  }
  
  else{
    digitalWrite(solenoidPin, LOW);
    //digitalWrite(solenoidPin2, LOW);
  }
}

void noteOff(byte channel, byte note, byte velocity)
{
    digitalWrite(solenoidPin, LOW);
    //digitalWrite(solenoidPin2, LOW);
}

void setup (){
  MIDI.begin(MIDI_CHANNEL_OMNI);
  MIDI.setHandleNoteOn(noteOn);
  MIDI.setHandleNoteOff(noteOff);
  pinMode(solenoidPin, OUTPUT);   
  //pinMode(solenoidPin2, OUTPUT);    
  digitalWrite(solenoidPin, LOW); 
  //digitalWrite(solenoidPin2, LOW);

}

void loop() {
  MIDI.read();
}

