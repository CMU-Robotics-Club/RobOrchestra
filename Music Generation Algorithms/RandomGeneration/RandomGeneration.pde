import themidibus.*; //Import midi library
import java.lang.Math; //To get random numbers
import controlP5.*; //For GUI stuff

ControlP5 cp5;

//Open SimpleSynth to play on Mac

MidiBus myBus; //Creates a MidiBus object
int channel = 0; //set channel. 0 for speakers
int velocity = 120; //melody note volume
int noteLen = 1000; //set chord length in milliseconds
boolean playing = true;

int tonicCount = 10; //Number of whole-note tonics to play before stopping

int tonic = 60; //set key to C major
int[] scaleOffsets = {0, 2, 4, 5, 7, 9, 11, 12};
int[] majorOffsets = {0, 2, 4, 5, 7, 9, 11, 12};
int[] minorOffsets = {0, 2, 3, 5, 7, 8, 10, 12};
int[][] rhythms = {{1}, {2, 2}, {4, 4, 4, 4}};
int[] nextRhythm = {}; //Start on a whole note

float a = 1, b = 1, c = 1, d = 1, e = 1, f = 1, g = 1;
float[] p = {1/7, 1/7, 1/7, 1/7, 1/7, 1/7, 1/7};

//sets up screen
void setup() {

  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  myBus = new MidiBus(this, 0, 1);
  
  size(400, 800);
  cp5 = new ControlP5(this);
  
  cp5.addButton("Major")
    .setBroadcast(false)
    .setValue(0)
    .setPosition(100, 50)
    .setSize(200, 19)
    .setBroadcast(true)
  ;
  cp5.addButton("Minor")
    .setBroadcast(false)
    .setValue(0)
    .setPosition(100, 100)
    .setSize(200, 19)
    .setBroadcast(true)
  ;
  cp5.addButton("Start_Stop")
    .setBroadcast(false)
    .setValue(0)
    .setPosition(100, 150)
    .setSize(200, 19)
    .setBroadcast(true)
  ;
  cp5.addSlider("noteLen")
    .setPosition(100, 200)
    .setSize(200, 19)
    .setRange(500, 2000) //I'd like a log scale...
    .setValue(1000)
  ;

  thread("playMelody");
}


//this function repeats indefinitely
void draw() {
  float sum = a + b + c + d + e + f + g;
  if(sum == 0){
    println("Problem!!!");
    return;
  }
  p[0] = a/sum;
  p[1] = b/sum;
  p[2] = c/sum;
  p[3] = d/sum;
  p[4] = e/sum;
  p[5] = f/sum;
  p[6] = g/sum;
}

void playMelody(){
  while(true){
    if(playing) {
      int offset = 0;
      double r = Math.random();
      for(int x = 0; x < 7; x++){
        r -= p[x];
        if(r < 0){
          offset = x;
          break;
        }
      }
      int pitch = tonic + scaleOffsets[offset];
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
    else{
      delay(10); //Stop looping infinitely fast when not playing; it causes problems
    }
  }
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

public void Start_Stop(int val) {
  if(playing) {
   playing = false;
   println("Pausing");
  }
  
  else {
   playing = true; 
   println("Resuming");
  }
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
  while (millis () < current+time){
    Thread.yield();
  } 
}