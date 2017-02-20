//Test Code for Ukulelebot Circuit

import themidibus.*; //Library documentation: http://www.smallbutdigital.com/themidibus.php

MidiBus myBus; //Creates a MidiBus object
int channel = 0; //channel Ukulelebot is on
int noteLen = 1000; //set note length in milliseconds

//Parameters for directing stream of MIDI data
int input = 0;
int output = 1;

//For testing Ukulelebot chords
int chord = 60;
int chordSpec = 100;

//Reference
String[] notes = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};

//initialization
void setup() {
  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  System.out.println("");

  myBus = new MidiBus(this, input, output); //Creates bus to send MIDI data to Ukulelebot

}

//loops
void draw() {
    System.out.println("C chord note on");
    
    //creates a note object
    Note mynote = new Note(channel, chord, chordSpec, noteLen);
    
    //sends note to Xylobot 
    myBus.sendNoteOn(mynote);
    
    //time between each note
    delay(noteLen);
    
    System.out.println("C chord note off");
    
    myBus.sendNoteOff(mynote);
    myBus.sendNoteOn(new Note(channel, chord, 0));
    
    delay(noteLen);

}