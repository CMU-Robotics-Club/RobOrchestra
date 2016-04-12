//This should work on any single-note instrument
//To use:
//Set lo and hi to the appropriate MIDI bounds
//Set channel to whatever channel the instrument is on
//Adjust noteLen, numbeats, and nreps if desired

import themidibus.*; //Import midi library
import java.lang.Math; //To get random numbers

MidiBus myBus; //Creates a MidiBus object
int channel = 0;
int noteLen = 1000; //set chord length in milliseconds

//Bounds on range (MIDI values)
int lo = 60;
int hi = 76;

//Parameters
int nreps = 4; //Number of times to repeat each test
int[] numbeats = {1, 2, 4}; //Number of beats in each test

//Reference
String[] notes = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};

String midiToNote(int x){
   return notes[x%12] + " " + (x/12-1); 
}

//sets up screen
void setup() {
  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  System.out.println("");

  myBus = new MidiBus(this, 0, 3); //Sends midi output to speakers
  //System.out.println("Starting");
  //System.out.println(noteLen/1000.0 + " beats per second");
  delay(1000);

  for(int x = lo; x < hi; x++){
    //System.out.println("");
    System.out.println("Testing note with MIDI value " + x);
    //System.out.println("The corresponding note is " + midiToNote(x));
    //System.out.println("");
      for(int y: numbeats){ //y is a VALUE from numbeats!
      //  System.out.println("Testing " + y + " beat(s) per measure");
         for(int z = 0; z < nreps; z++){
        //   System.out.println("Repetition " + (z+1));
           for(int w = 0; w < y; w++){
          //   System.out.println("Sending");
             Note mynote = new Note(channel, x, 100, noteLen/y);
             myBus.sendNoteOn(mynote);
             delay(noteLen/y);
           }
         }
      }
  }
  System.out.println("Done testing");
  System.exit(0);
}

void draw() {
  //Does nothing
}