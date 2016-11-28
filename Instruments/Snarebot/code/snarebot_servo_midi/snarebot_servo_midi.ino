
#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>
#include <Servo.h>


MIDI_CREATE_DEFAULT_INSTANCE();

Servo servo_near;
Servo servo_middle;

int which = 0;
int hitting = 0;
int donthit = 0;

void handleNoteOn(byte channel, byte pitch, byte velocity)
{
  if (pitch == 36 && hitting == 0 && donthit == 0) {
    hitDrum();
  }
  else if (pitch == 37 && velocity == 0) {
    hitting = 0;
    donthit = 1;
  }
  else if (pitch == 37 && velocity != 0) {
    hitting = 1;
  }
}

void hitDrum() {
  if(which == 1){
    hit();
    which = -1;
  } else{
    hit2();
    which = 1;
  }
  donthit = 0;
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
  if (hitting == 1) {
    hitDrum();
  }
}

void hit() { 
  servo_near.write(106);
  delay(100);
  servo_near.write(90);
  delay(10);
}


void hit2() { 
  
  servo_middle.write(143);  //143  160   green red black     //
  delay(100);
  servo_middle.write(158);
  delay(10);

}
