//Percussion Testing Code

import themidibus.*; //Library documentation: http://www.smallbutdigital.com/themidibus.php

MidiBus myBus; //Creates a MidiBus object

//Parameters (CHANGE BEFORE USING):
//channels: Array of channels to send stuff over (for multiple instruments on one channel, repeat the channel)
//pitchvals: Array of pitch values that need to be sent for a given instrument to play
//minLen: Array of minimum note lengths that you want a given instrument to play
//Pitchvals and minLen set to use modular arithmetic on the index, but for more than one value, specify explicitly
int[] channels = {0};
int[] pitchvals = {36};
int[] minLen = {60};
int maxLen = 1000;

//Parameters
int nreps = 2; //Number of measures played for each length (one measure being one maxLen note)

//initialization
void setup() {
  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  System.out.println("");
  myBus = new MidiBus(this, 0, 1); //Creates bus to send MIDI data to xylobot
}

//loops
void draw() {
  
         //creates a note object
  Note mynote = new Note(0, 36, 100);
  
  myBus.sendNoteOn(mynote);
  delay(500);

}
