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

#define LED 13  

MIDI_CREATE_DEFAULT_INSTANCE();

Servo myservo;

void handleNoteOn(byte channel, byte pitch, byte velocity)
{
  if (channel == 1) {
    hit();
  }
}


void setup()
{
  pinMode(LED, OUTPUT);
  Serial3.begin(115200);
  myservo.attach(10);
  MIDI.setHandleNoteOn(handleNoteOn);
  MIDI.begin(MIDI_CHANNEL_OMNI);
  MIDI.turnThruOn();
}

void loop()
{ 
  MIDI.read();
}

void hit() {
  
  myservo.write(80);
  delay(30);
  myservo.write(103);
  delay(30);

}
