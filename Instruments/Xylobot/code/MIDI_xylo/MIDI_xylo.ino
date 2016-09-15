
#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>

#include "def.h"
#include "xylo.h"

#define STARTNOTE 60 //60
#define ENDNOTE 76 // 76
#define KEY_UP_TIME 50


#define LED 13
MIDI_CREATE_DEFAULT_INSTANCE();

int played = 0;

void setup()
{
  xylo_init();
  pinMode(LED, OUTPUT);
  Serial3.begin(115200);
  MIDI.begin(MIDI_CHANNEL_OMNI);          // Launch MIDI and listen to channel 1
}

void loop()
{ 
  if(MIDI.read()){
      int noteIndex = MIDI.getData1();
      if(noteIndex >= STARTNOTE && noteIndex <= ENDNOTE){
        int notePin = getNote(noteIndex); // map the note to the pin
        playKey(notePin); // plays the key on the glockenspiel (xylobot)
      }  
    }  
  //}
}

// maps the note index to the note pin
int getNote(int noteIndex){
  switch (noteIndex) {
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
  case NOTE_A:
    return N_A;
  case NOTE_A_S:
    return N_A_S;
  case NOTE_B:
    return N_B;
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
  default: // should never drop to this case!
    return 0;
  }
}

void playKey(int keyPin){
  digitalWrite(keyPin, HIGH);
  digitalWrite(LED, HIGH);
  delay(KEY_UP_TIME);
  digitalWrite(LED, LOW);
  digitalWrite(keyPin, LOW); 
}













