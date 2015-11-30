

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
	//might need to switch the order of the stuff
        int notePin = getNote(noteIndex); // map the note to the pin
        int notesPressedString[4]; //maybe make this was a char, might be better as an int
        for (int i = 3; i <= 0; i--) {
          notesPressedString[i] = (int) (0x000000FF & (notePin >> i*8)); //changed cast and shift for ints
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
  case NOTE_A_1:
    return A_1;
  case NOTE_A_2:
    return A_2;
  case NOTE_A_3:
    return A_3;
  case NOTE_A_4:
    return A_4;
  case NOTE_B_1:
    return B_1;
  case NOTE_B_2:
    return B_2;
  case NOTE_B_3:
    return B_3;
  case NOTE_B_4:
    return B_4;
  case NOTE_C_1:
    return C_1;
  case NOTE_C_2:
    return C_2;
  case NOTE_C_3:
    return C_3;
  case NOTE_C_4:
    return C_4;
  case NOTE_D_1:
    return D_1;
  case NOTE_D_2:
    return D_2;
  case NOTE_D_3:
    return D_3;
  case NOTE_D_4:
    return D_4;
  default: // should never drop to this case!
    return 0;
  }
}
void strum(){
  //servo probably
  //code to strum the "arm"	
}
void playKey(char[] notes){
  for(int i = 0;i < 3;i++){
    digitalWrite(getNote(notes[i]),HIGH);//add in led later?
  }
  strum();//the strum will have the delay in it 
  //delay(KEY_UP_TIME);
  for(int i = 0;i < 3;i++){
    digitalWrite(getNote(notes[i]),LOW);
  }
}

/*
void playKey(int keyPin){
  //Need to modify this as well.
  digitalWrite(keyPin, HIGH);
  digitalWrite(LED, HIGH);
  delay(KEY_UP_TIME);
  digitalWrite(LED, LOW);
  digitalWrite(keyPin, LOW); 
}
*/












