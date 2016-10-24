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
int[] minLen = {250};
int maxLen = 2000;

//Parameters
int nreps = 2; //Number of measures played for each length (one measure being one maxLen note)

//initialization
void setup() {
  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  System.out.println("");
  myBus = new MidiBus(this, 0, 3); //Creates bus to send MIDI data to xylobot
}

//loops
void draw() {
  
  //Loop through all instruments
  for(int x = 0; x < channels.length; x++){
    
    //Loop through all lengths (divide by 2 each time until you get below the minimum)
    for(int len = maxLen; len >= minLen[x%minLen.length]; len/=2){
       println("Note length: " + len);
       
       //Loop through and actually play the notes (y is just a dummy variable now)
       for(int y = 0; y < maxLen/len*nreps; y++){
         
         //creates a note object
         Note mynote = new Note(channels[x], pitchvals[x%pitchvals.length], 100, len);
    
         //sends note to Xylobot 
         myBus.sendNoteOn(mynote);
    
         //time between each note
         delay(len);
       }
    } 
  }
  
  exit();
}