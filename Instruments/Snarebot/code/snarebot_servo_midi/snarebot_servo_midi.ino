
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
  if (pitch == 36 && velocity > 0) {
    hitDrum();
  }
}

void hitDrum() {
  if(which == 1){
    hit();
<<<<<<< HEAD
    which = 0;
=======
    which = 2;
>>>>>>> origin/master
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
  hitDrum();
  delay(1000);
}

void hit() { 
  servo_near.write(120);
  delay(100);
  servo_near.write(95);
  delay(10);
}


void hit2() { 
  
<<<<<<< HEAD
  servo_middle.write(95);  //143  160   green red black     //
  delay(100);
  servo_middle.write(120);
=======
  servo_middle.write(90);  //143  160   green red black     //
  delay(100);
  servo_middle.write(106);
>>>>>>> origin/master
  delay(10);

}
