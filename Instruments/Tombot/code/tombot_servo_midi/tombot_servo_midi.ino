#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>
#include <Servo.h>


MIDI_CREATE_DEFAULT_INSTANCE();

Servo servo_near;
Servo servo_middle;

long stickdown = 70;
long stickup = 10;
long clock1 = -1;
long clock2 = -1;

//For testing only
long lasttestmsg = 0;

void handleNoteOn(byte channel, byte pitch, byte velocity)
{
  if(pitch == 37 && velocity > 0) {
     hitDrum();
  }
}

void hitDrum() {
  if(millis() - clock1 >= stickdown + stickup && clock1 <= clock2){
    hit();
  }
  else if(millis() - clock2 >= stickdown + stickup){
    hit2();
  }
  else{
    //Neither stick is ready; ignore this message
    //I'd like to throw an error or print something or do something otherwise weird; not sure if I can do that
  }/**/
}


void setup()
{
  servo_near.attach(10);
  servo_middle.attach(11);
  MIDI.setHandleNoteOn(handleNoteOn);
  MIDI.begin(MIDI_CHANNEL_OMNI);
  MIDI.turnThruOn();
  clock1 = millis()-stickdown;
  clock2 = millis()-stickdown;
  lasttestmsg = millis();
}

void loop()
{ 
  MIDI.read();

  //Generate test messages every second
  /*if(millis() - lasttestmsg > 100){
    lasttestmsg = millis();
    hitDrum();
  }/**/

  if(millis() - clock1 > stickdown){
    servo_near.write(93);
  }
  if(millis() - clock2 > stickdown){
    servo_middle.write(93); //Second servo's reversed, so 120 is up
  }
}

void hit() {
  clock1 = millis();
  servo_near.write(80);
}

void hit2() {
  clock2 = millis();
  servo_middle.write(80);
}
