/*
General Idea:

We want to generate a slightly randomized first species counterpoint by generating a bass line determined by allowable chord progressions
and then generating a melody line from choices which are given by filtering all possible
Generate Bass line:

Choose Chord Progressions repeatedly from a library and choose valid note for bass line (try to move by step or similar)

*/


import themidibus.*;
MidiBus myBus;
int channel = 0; //channel xylobot is on
int noteLen = 1000; //set note length in milliseconds

//Bounds on range (MIDI values)
int lo = 60; //middle C (C4)
int hi = 76; //E5

//Parameters for directing stream of MIDI data
int input = 0;
int output = 1 ;

//Reference
String[] notes = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};


//for making output readable
String midiToNote(int x){
   return notes[x%12] + " " + (x/12-1); 
}

CounterPointFirstSpecies mySong;

void setup(){
  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  System.out.println("");

  myBus = new MidiBus(this, input, output);
}


void draw() {
  
}