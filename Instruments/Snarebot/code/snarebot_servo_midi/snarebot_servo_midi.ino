
#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>
#include <Servo.h>


MIDI_CREATE_DEFAULT_INSTANCE();

Servo servo_near;
Servo servo_middle;

int which = 1;


void handleNoteOn(byte channel, byte pitch, byte velocity)
{
  if (pitch == 36) {
    hitDrum();
  }
}

void hitDrum() {
  if(which == 1){
    hit();
    which = 2;
  } else{
    hit2();
    which = 1;
  }
}

void setup()
{
  servo_near.attach(5);
  servo_middle.attach(4);
  MIDI.setHandleNoteOn(handleNoteOn);
  MIDI.begin(MIDI_CHANNEL_OMNI);
  MIDI.turnThruOn();
}

void loop()
{ 
  MIDI.read();
}

void hit() { 
  servo_near.write(106);
  delay(100);
  servo_near.write(90);
  delay(10);
}


void hit2() { 
  
  servo_middle.write(106);  //143  160   green red black     //
  delay(100);
  servo_middle.write(90);
  delay(10);

}
