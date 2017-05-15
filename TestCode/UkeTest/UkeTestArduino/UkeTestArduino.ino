#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>

MIDI_CREATE_DEFAULT_INSTANCE();

int solenoidPin = 52;
int solenoidPin2 = 50;
int solenoidPin3 = 48;
int solenoidPin4 = 46;


void noteOn(byte channel, byte note, byte velocity)
{
  if(velocity>0){
    if(note == 52) digitalWrite(solenoidPin, HIGH);
    else if(note == 50) digitalWrite(solenoidPin2, HIGH);
    else if(note == 48) digitalWrite(solenoidPin3, HIGH);
    else if(note == 46) digitalWrite(solenoidPin4, HIGH);
  }
  
  else{
    if(note == 52) digitalWrite(solenoidPin, LOW);
    else if(note == 50) digitalWrite(solenoidPin2, LOW);
    else if(note == 48) digitalWrite(solenoidPin3, LOW);
    else if(note == 46) digitalWrite(solenoidPin4, LOW);
  }
}

void noteOff(byte channel, byte note, byte velocity)
{
    if(note == 52) digitalWrite(solenoidPin, LOW);
    else if(note == 50) digitalWrite(solenoidPin2, LOW);
    else if(note == 48) digitalWrite(solenoidPin3, LOW);
    else if(note == 46) digitalWrite(solenoidPin4, LOW);
}

void setup (){
  MIDI.begin(MIDI_CHANNEL_OMNI);
  MIDI.setHandleNoteOn(noteOn);
  MIDI.setHandleNoteOff(noteOff);
  pinMode(solenoidPin, OUTPUT);   
  pinMode(solenoidPin2, OUTPUT);
  pinMode(solenoidPin3, OUTPUT);  
  pinMode(solenoidPin4, OUTPUT);  
  digitalWrite(solenoidPin, LOW); 
  digitalWrite(solenoidPin2, LOW);
  digitalWrite(solenoidPin3, LOW);
  digitalWrite(solenoidPin4, LOW);

}

void loop() {
  MIDI.read();
}

