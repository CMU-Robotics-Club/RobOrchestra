//Xylobot Testing Code
//Plays through a chromatic scale on loop
//Used to test functionality of solenoids(they break randomly)

import themidibus.*; //Library documentation: http://www.smallbutdigital.com/themidibus.php

MidiBus myBus; //Creates a MidiBus object
int channel = 0; //channel xylobot is on
int noteLen = 2000; //set note length in milliseconds

//Bounds on range (MIDI values)
int lo = 60; //60 = middle C (C4)
int hi = 84; //76 = E5

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

void playNote(int x, int noteLen){
  System.out.println("Playing note with MIDI value " + x);
    
  //creates a note object
  Note mynote = new Note(channel, x, 100, noteLen);
  
  //sends note to Xylobot 
  myBus.sendNoteOn(mynote);
  double legato = 0.95;
  delay((int)(legato*noteLen));
  myBus.sendNoteOff(mynote);
  delay((int)((1-legato)*noteLen));
}

//loops
void draw() {
  playNote(71, 1000);
  playNote(69, 1000);
  playNote(67, 2000);
  
  playNote(71, 1000);
  playNote(69, 1000);
  playNote(67, 2000);
  
  playNote(67, 500);
  playNote(67, 500);
  playNote(67, 500);
  playNote(67, 500);
  
  playNote(69, 500);
  playNote(69, 500);
  playNote(69, 500);
  playNote(69, 500);
  
  playNote(71, 1000);
  playNote(69, 1000);
  playNote(67, 2000);
  
  delay(4000);
}
