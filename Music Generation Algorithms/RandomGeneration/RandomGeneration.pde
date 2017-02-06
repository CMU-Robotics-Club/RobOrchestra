import themidibus.*; //Import midi library
import java.lang.Math; //To get random numbers

//Open SimpleSynth to play on Mac

MidiBus myBus; //Creates a MidiBus object
int channel = 0; //set channel. 0 for speakers
int velocity = 120; //melody note volume
int noteLen = 1000; //set chord length in milliseconds

int tonicCount = 10; //Number of whole-note tonics to play before stopping

int tonic = 60; //set key to C major
int[] scaleOffsets = {0, 2, 4, 5, 7, 9, 11, 12};
int[][] rhythms = {{1}, {2, 2}, {4, 4, 4, 4}};
int[] nextRhythm = {}; //Start on a whole note


//sets up screen
void setup() {

  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  myBus = new MidiBus(this, 0, 1);
}


//this function repeats indefinitely
void draw() {
  int pitch = tonic + scaleOffsets[(int)(Math.random()*8)];
  int len = noteLen / getNextRhythm();
  Note note = new Note(channel, pitch, velocity, len);
  myBus.sendNoteOn(note);
  
  //Tonic count stuff
  if(pitch == tonic && len == noteLen){
     tonicCount--;
     print("t");
     if(tonicCount == 0){
       exit();
     }
  }
  delay(len);
}

int getNextRhythm(){
  int in = (int)(Math.random()*rhythms.length);
  
  int[] temp = new int[max(nextRhythm.length-1, 0) + rhythms[in].length];
  
  int index = 0;
  for(int x = 1; x < nextRhythm.length; x++){
     temp[index++] = nextRhythm[x]; 
  }
  for(int x = 0; x < rhythms[in].length; x++){
     temp[index++] = rhythms[in][x]; 
  }
  nextRhythm = temp;
  return nextRhythm[0];
}

//processes delay in milliseconds
void delay(int time) {
  int current = millis();
  while (millis () < current+time) Thread.yield();
}