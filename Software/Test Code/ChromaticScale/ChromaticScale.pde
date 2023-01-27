//Xylobot Testing Code
//Plays through a chromatic scale on loop
//Used to test functionality of solenoids(they break randomly)

import themidibus.*; //Library documentation: http://www.smallbutdigital.com/themidibus.php

MidiBus myBus; //Creates a MidiBus object
int channel = 0; //channel xylobot is on
int noteLen = 100; //set note length in milliseconds

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

  myBus = new MidiBus(this, 0, 1); //Creates bus to send MIDI data to xylobot

}

//loops
void draw() {
  //for(int x = lo; x < hi; x++){
  for(int x = lo; x <= hi; x++){
    System.out.println("Testing note with MIDI value " + x);
    
    //creates a note object
    Note mynote = new Note(channel, x, 100, noteLen);
    
    //sends note to Xylobot 
    myBus.sendNoteOn(mynote);
    double legato = 0.5;
    delay((int)(legato*noteLen));
    myBus.sendNoteOff(mynote);
    delay((int)((1-legato)*noteLen));
    
    /*delay(1);
    
    //creates a note object
    mynote = new Note(channel, x+4, 100, noteLen);
    
    //sends note to Xylobot 
    myBus.sendNoteOn(mynote);
    
    delay(1);
    
    //creates a note object
    mynote = new Note(channel, x+7, 100, noteLen);
    
    //sends note to Xylobot 
    myBus.sendNoteOn(mynote);//*/
  }

}
