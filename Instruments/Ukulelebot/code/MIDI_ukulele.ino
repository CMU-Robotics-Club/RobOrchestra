

/*
 * @file: 
 *
 *
 */
#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>

#include "def.h"
#include "ukulele.h"

#define KEY_UP_TIME 50 //Change this to be appropriate for ukulele

// Simple tutorial on how to receive and send MIDI messages.
// Here, when receiving any message on channel 4, the Arduino 
// will blink a led and play back a note for 1 second.

#define LED 13   		    // LED pin on Arduino Uno

int played = 0;

void setup()
{
  ukulele_init();
  pinMode(LED, OUTPUT);
  Serial3.begin(115200);
  MIDI.begin();          // Launch MIDI and listen to channel 1
}

void loop()
{ 
  if(MIDI.read()){
    // && MIDI.getData2() != 0 pokemon theme (bicycle)
   //  hall of fame
    if(MIDI.getType() > 0){ // note on
      int noteIndex = MIDI.getData1();
      //int note_2 = MIDI.getData2();
      if(noteIndex >= STARTNOTE && noteIndex <= ENDNOTE){
        /* The leftmost string should be the most significant byte in the int
         * Likewise, the rightmost string should be the least significant byte.
         * Then starting from 0 (Nothing pressed) to 4 (Press the highest note
         * of the string), that's how each byte of the int should be 
         * represented.
         */
        int notePin = getNote(noteIndex); // map the note to the pin
        char notesPressedString[4];
        for (int i = 3; i <= 0; i--) {
          notesPressedString[i] = (char) (0xFF & (notePin >> i*8));
        }
        playKey(notePin); // plays the key on the ukulele
      }  
    }  
  }
}

// maps the note index to the note pin
//Look at def.h to see how these should be modified.
int getNote(int noteIndex){
  switch (noteIndex) {
  case NOTE_A:
    return N_A;
  case NOTE_A_S:
    return N_A_S;
  case NOTE_B:
    return N_B;
  case NOTE_C:
    return N_C;
  case NOTE_C_S:
    return N_C_S;
  case NOTE_D:
    return N_D;
  case NOTE_D_S:
    return N_D_S;
  case NOTE_E:
    return N_E;
  case NOTE_F:
    return N_F;
  case NOTE_F_S:
    return N_F_S;
  case NOTE_G:
    return N_G;
  case NOTE_G_S:
    return N_G_S;
  case NOTE_HIGH_A:
    return N_HIGH_A;
  case NOTE_HIGH_A_S:
    return N_HIGH_A_S;
  case NOTE_HIGH_B:
    return N_HIGH_B;
  case NOTE_HIGH_C:
    return N_HIGH_C;
  case NOTE_HIGH_C_S:
    return N_HIGH_C_S;
  case NOTE_HIGH_D:
    return N_HIGH_D;
  case NOTE_HIGH_D_S:
    return N_HIGH_D_S;
  case NOTE_HIGH_E:
    return N_HIGH_E;
  case NOTE_HIGH_F:
    return N_HIGH_F;
  case NOTE_HIGH_F_S:
    return N_HIGH_F_S;
  case NOTE_HIGH_G:
    return N_HIGH_G;
  case NOTE_HIGH_G_S:
    return N_HIGH_G_S;
  case NOTE_HIGHER_A:
    return N_HIGHER_A;
  default: // should never drop to this case!
    return 0;
  }
}

void playKey(int keyPin){
  //Need to modify this as well.
  digitalWrite(keyPin, HIGH);
  digitalWrite(LED, HIGH);
  delay(KEY_UP_TIME);
  digitalWrite(LED, LOW);
  digitalWrite(keyPin, LOW); 
}













