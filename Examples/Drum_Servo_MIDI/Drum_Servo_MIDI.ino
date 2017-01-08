#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>
#include <Servo.h>

MIDI_CREATE_DEFAULT_INSTANCE();

Servo myServo;

//change 37 to the MIDI value for the type of drum(snare, bass etc)
void handleNoteOn(byte channel, byte pitch, byte velocity) {
  if(pitch == 37) {
    hit();    
  }
}

void setup() {

  //change 10 to pin servo is attached to on Arduino
  myServo.attach(10);

  MIDI.setHandleNoteOn(handleNoteOn);
  MIDI.begin(MIDI_CHANNEL_OMNI);
  MIDI.turnThruOn();
}

void loop() { 
  MIDI.read();
}

//numbers for write function are angles of servo.
//delay time is in milliseconds
//all numbers in this function can be changed to fine tune the hit
void hit() {
  myServo.write(80);
  delay(70);
  myServo.write(98);
  delay(10);
}
