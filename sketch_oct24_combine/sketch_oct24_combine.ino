#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>
#include <Servo.h>


MIDI_CREATE_DEFAULT_INSTANCE();

Servo servo1;
Servo servo2;

int which = 0;

void handleNoteOn(byte channel, byte pitch, byte velocity)
{
  if(pitch == 37) {
    
     if(which == 1){
      hit();
      which = -1;
    }else{
      hit2();
      which = 1;
   }
    
  }
}


void setup()
{
  servo1.attach(10);
  servo2.attach(11);
  MIDI.setHandleNoteOn(handleNoteOn);
  MIDI.begin(MIDI_CHANNEL_OMNI);
  MIDI.turnThruOn();
}

void loop()
{ 
  MIDI.read();
}

void hit() {
  
  servo1.write(80);
  delay(70);
  servo1.write(98);
  delay(10);
}

void hit2() {
  
  servo2.write(80);
  delay(70);
  servo2.write(98);
  delay(10);

}
