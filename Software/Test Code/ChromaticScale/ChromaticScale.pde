//Xylobot Testing Code
//Plays through a chromatic scale on loop
//Used to test functionality of solenoids(they break randomly)

import themidibus.*; //Library documentation: http://www.smallbutdigital.com/themidibus.php

MidiBus[] myBus;
int[] toSend = {}; //Which MIDI output to send to - overwrites to everything in setup
int channel = 0; //channel xylobot is on
int noteLen = 1000; //set note length in milliseconds

//Bounds on range (MIDI values)
int lo = 60; //60 = middle C (C4)
int hi = 76; //76 = E5

//Parameters
int nreps = 1; //Number of times to repeat each note

//Reference
String[] notes = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};


//for making output readable
String midiToNote(int x){
   return notes[x%12] + " " + (x/12-1); 
}

//initialization
void setup() {
  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  System.out.println("");

  //Overwrite toSend to send to everything by default - block comment if you want to avoid sending everywhere
  toSend = new int[MidiBus.availableOutputs().length];
  for (int i = 0; i < MidiBus.availableOutputs().length; i++){
    toSend[i] = i;
  }
  
  //Use toSend - this looks silly, but splitting this out is more convenient if we don't want to blast MIDI everywhere
  myBus = new MidiBus[toSend.length];
  for (int i = 0; i < myBus.length; i++){
    myBus[i] = new MidiBus(this, 0, toSend[i]);
  }

}

//loops
void draw() {
  for(int x = lo; x <= hi; x++){
    System.out.println("Testing note with MIDI value " + x);
    
    //creates a note object
    Note mynote = new Note(channel, x, 100, noteLen);
    
    //sends note to Xylobot
    for (int i = 0; i < myBus.length; i++){
      myBus[i].sendNoteOn(mynote); 
    }
    double legato = 0.5;
    delay((int)(legato*noteLen));
    for (int i = 0; i < myBus.length; i++){
      myBus[i].sendNoteOff(mynote); 
    }
    delay((int)((1-legato)*noteLen));
  }

}
