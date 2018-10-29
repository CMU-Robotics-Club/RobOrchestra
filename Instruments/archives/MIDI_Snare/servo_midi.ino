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

Servo myservo;


		    // LED pin on Arduino Uno
void setup()
{
  myservo.attach(10);
  MIDI.begin(3);          // Launch MIDI and listen to channel 1
}

void loop()
{ 
  if(MIDI.read()){
    int noteIndex = MIDI.getData1();
    if (noteIndex == 38 && MIDI.getType() != 0){  // bass drum index
      hit();
    }
  }
}

void hit() {
  
  myservo.write(85);
  delay(40);
  myservo.write(110);
  delay(40);

}
