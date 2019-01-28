//This 4 lines must be included to properly reference the MIDI library
#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>

//Sets up the MIDI environment
MIDI_CREATE_DEFAULT_INSTANCE();


//This function is called everytime a MIDI note message is received
//Fill in with how the instrument should handle MIDI messages
void handleNoteOn(byte channel, byte pitch, byte velocity) {

}

//This function runs once automatically when the Arduino is turned on
void setup() {

  //Sets handleNoteOn function to be called when a MIDI note message is received
  MIDI.setHandleNoteOn(handleNoteOn);

  //Begin listening for MIDI messages on all channels
  MIDI.begin(MIDI_CHANNEL_OMNI);

  //Sends all MIDI messages received through to the next instrument in the chain
  MIDI.turnThruOn();
}

//This function runs continuosly after setup() has finished running
void loop() { 
  //Continuously listen for MIDI messages
  MIDI.read();
}
