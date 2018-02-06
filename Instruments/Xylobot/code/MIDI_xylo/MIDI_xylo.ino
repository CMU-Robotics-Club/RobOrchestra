
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

//int played = 0; //Does nothing?
int toPlay[] = {};
int nToPlay = 0;
int startTime = 0;

void handleNoteOn(byte channel, byte pitch, byte velocity){
  //This function queues up notes to be played
  if(velocity == 0) return;
  
  int noteIndex = pitch;

  //Rescale notes
  while(noteIndex < STARTNOTE){
    noteIndex += 12;
  }
  while(noteIndex > ENDNOTE){
    noteIndex -= 12;
  }

  //Add noteIndex to toPlay (TODO: Make this less bad)
  int temp[nToPlay+1];
  for(int x = 0; x < nToPlay; x++){
    temp[x] = toPlay[x];
  }
  temp[nToPlay] = noteIndex;
  int toPlay[nToPlay+1];
  for(int x = 0; x < nToPlay+1; x++){
    toPlay[x] = temp[x];
    
  }
  nToPlay++;
  startTime += KEY_UP_TIME/5;
}

void playNotes(){
  //To move to whatever plays the notes
  int pinnumbers[] = {22, 13, 23, 38, 24, 25, 34, 26, 35, 27, 36, 28, 29, 37, 30, 39, 31};

  if(nToPlay > 0){
    Serial.println("a");
  }
  
  for(int x = 0; x < nToPlay; x++){
    int keyPin = pinnumbers[toPlay[x] - STARTNOTE];//getNote(noteIndex); // map the note to the pin
    digitalWrite(keyPin, HIGH);
    digitalWrite(LED, HIGH);
  }
  delay(KEY_UP_TIME);
  for(int x = 0; x < nToPlay; x++){
    int keyPin = pinnumbers[toPlay[x] - STARTNOTE];//getNote(noteIndex); // map the note to the pin
    digitalWrite(keyPin, LOW);
    digitalWrite(LED, LOW);
  }
  int toPlay[0] = {};
  nToPlay = 0;
}

void setup()
{
  xylo_init();
  pinMode(LED, OUTPUT);
  Serial.begin(115200);
  MIDI.setHandleNoteOn(handleNoteOn);
  MIDI.begin(MIDI_CHANNEL_OMNI);          // Launch MIDI and listen to channel 1
  MIDI.turnThruOn();
}

void loop()
{ 
  MIDI.read();

  int curTime = millis();
  if(curTime - startTime > 20*KEY_UP_TIME){
    startTime = curTime;
    playNotes();
  }

  //Old code, can be deleted if I didn't break everything...
  /*if(MIDI.read()){
      int noteIndex = MIDI.getData1();
      if(noteIndex >= STARTNOTE && noteIndex <= ENDNOTE){
        int notePin = getNote(noteIndex); // map the note to the pin
        playKey(notePin); // plays the key on the glockenspiel (xylobot)
      }  
    }  */
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

//Replaced by playNotes above
/*void playKey(int keyPin){
  digitalWrite(keyPin, HIGH);
  digitalWrite(LED, HIGH);
  delay(KEY_UP_TIME);
  digitalWrite(LED, LOW);
  digitalWrite(keyPin, LOW); 
}*/













