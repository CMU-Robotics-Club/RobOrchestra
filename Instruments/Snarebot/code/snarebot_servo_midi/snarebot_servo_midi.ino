#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>
#include <Servo.h>

#define STARTNOTE 35 //60
#define ENDNOTE 81 // 76
#define KEY_UP_TIME 50

#define SOL1 8
#define SOL2 9

// Simple tutorial on how to receive and send MIDI messages.
// Here, when receiving any message on channel 4, the Arduino 
// will blink a led and play back a note for 1 second.

#define LED 13  

MIDI_CREATE_DEFAULT_INSTANCE();

Servo myservo;


		    // LED pin on Arduino Uno

void handleNoteOn(byte channel, byte pitch, byte velocity)
{
  if(pitch == 38) {
    hit();
  }
}


void setup()
{
  pinMode(LED, OUTPUT);
  Serial3.begin(115200);
  myservo.attach(10);
  MIDI.setHandleNoteOn(handleNoteOn);
  MIDI.begin(MIDI_CHANNEL_OMNI);          // Launch MIDI and listen to channel 3
  MIDI.turnThruOn();
}

void loop()
{ 
  MIDI.read();
  /* if(MIDI.read()){
    hit();
    /*int noteIndex = MIDI.getData1();
    if (noteIndex == 38){  // snare drum index
      hit();
    } */
}

void hit() {
  
  myservo.write(80);
  delay(30);
  myservo.write(103);
  delay(300);

}
