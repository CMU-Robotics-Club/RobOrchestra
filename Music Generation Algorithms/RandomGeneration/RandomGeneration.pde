import themidibus.*; //Import midi library
import java.lang.Math; //To get random numbers
import controlP5.*; //For GUI stuff

ControlP5 cp5;

//Open SimpleSynth to play on Mac

MidiBus myBus; //Creates a MidiBus object
int channel = 0; //set channel. 0 for speakers
int velocity = 120; //melody note volume
int noteLen = 1000; //set chord length in milliseconds

int tonicCount = 10; //Number of whole-note tonics to play before stopping

int tonic = 60; //set key to C major
int[] scaleOffsets = {0, 2, 4, 5, 7, 9, 11, 12};
int[] majorOffsets = {0, 2, 4, 5, 7, 9, 11, 12};
int[] minorOffsets = {0, 2, 3, 5, 7, 8, 10, 12};
int[][] rhythms = {{1}, {2, 2}, {4, 4, 4, 4}};
int[] nextRhythm = {}; //Start on a whole note


//sets up screen
void setup() {

  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  myBus = new MidiBus(this, 0, 1);
  
  size(400, 600);
  cp5 = new ControlP5(this);
  
  cp5.addButton("Major")
    .setBroadcast(false)
    .setValue(0)
    .setPosition(100, 100)
    .setSize(200, 19)
    .setBroadcast(true)
  ;
  cp5.addButton("Minor")
    .setBroadcast(false)
    .setValue(0)
    .setPosition(100, 150)
    .setSize(200, 19)
    .setBroadcast(true)
  ;
  cp5.addSlider("tonic")
    .setPosition(100, 200)
    .setSize(200, 19)
    .setRange(48, 72)
  ;
  cp5.addSlider("noteLen")
    .setPosition(100, 250)
    .setSize(200, 19)
    .setRange(500, 2000) //I'd like a log scale...
    .setValue(1000)
  ;
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
  myBus.sendNoteOff(note);
}

public void Major(int val){
  //This magically runs when the button gets clicked. I'm not sure how.
  scaleOffsets = majorOffsets;
  println("In major");
}

public void Minor(int val){
  //This magically runs when the button gets clicked. I'm not sure how.
  scaleOffsets = minorOffsets;
  println("In minor");
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