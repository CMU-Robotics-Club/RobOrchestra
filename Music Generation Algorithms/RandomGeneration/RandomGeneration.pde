import themidibus.*; //Import midi library
import java.lang.Math; //To get random numbers
import controlP5.*; //For GUI stuff

ControlP5 cp5;

//Open SimpleSynth to play on Mac

MidiBus myBus; //Creates a MidiBus object
int channel = 0; //set channel. 0 for speakers
int velocity = 120; //melody note volume
float noteLen = 1000; //set chord length in milliseconds
boolean playing = true;
boolean isMajor = true;
boolean noteOff = false;

int tonicCount = -1; //Number of whole-note tonics to play before stopping; -1 for infinite loop

int tonic = 60; //set key to C major
int[] scaleOffsets = {0, 2, 4, 5, 7, 9, 11, 12};
int[] majorOffsets = {0, 2, 4, 5, 7, 9, 11, 12};
int[] minorOffsets = {0, 2, 3, 5, 7, 8, 10, 12};
int[][] rhythms = {{1}, {2, 2}, {4, 4, 4, 4}};
float[] rhythmProbs = {1.0, 0.0, 0.0};
float[] rhythmProbsSnare = {1.0, 0.0, 0.0};
float[] rhythmProbsTom = {1.0, 0.0, 0.0};
int[] nextRhythm = {}; //Start on a whole note
int[] nextRhythmSnare = {}; //Start on a whole note
int[] nextRhythmTom = {}; //Start on a whole note
float shortNoteBias = 0.0;
float shortNoteBiasSnare = 0.0;
float shortNoteBiasTom = 0.0;

float a = 1, b = 1, c = 1, d = 1, e = 1, f = 1, g = 1;
float[] p = {1/7, 1/7, 1/7, 1/7, 1/7, 1/7, 1/7};

float tol = 0.01; //Tolerance for equality checks and exp/log stuff

//sets up screen
void setup() {

  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  myBus = new MidiBus(this, 0, 1);
  
  size(400, 800);
  cp5 = new ControlP5(this);
  
  cp5.addButton("Pause")
    .setBroadcast(false)
    .setValue(0)
    .setPosition(100, 50)
    .setSize(200, 19)
    .setBroadcast(true)
  ;
  cp5.addToggle("isMajor")
    .setPosition(100, 150)
    .setSize(200, 19)
    .setValue(1)
  ;
  cp5.addSlider("tonic")
    .setPosition(100, 200)
    .setSize(200, 19)
    .setRange(36, 84)
    .setValue(60)
    .setSliderMode(0)
  ;
  
  //Log scales
  LogSlider ls = new LogSlider(cp5, "noteLen");
  ls.setPosition(100, 250)
    .setSize(200, 19)
    .setRange(log(500), log(2000))
    .setValue(log(1000))
    .setSliderMode(0)
  ;
  LogSlider ls2 = new LogSlider(cp5, "shortNoteBias");
  ls2.setPosition(100, 300)
    .setSize(200, 19)
    .setRange(log(0.01), log(100))
    .setValue(log(0.01))
    .setSliderMode(0)
  ;
  ls2 = new LogSlider(cp5, "shortNoteBiasTom");
  ls2.setPosition(100, 350)
    .setSize(200, 19)
    .setRange(log(0.01), log(100))
    .setValue(log(0.01))
    .setSliderMode(0)
  ;
  ls2 = new LogSlider(cp5, "shortNoteBiasSnare");
  ls2.setPosition(100, 400)
    .setSize(200, 19)
    .setRange(log(0.01), log(100))
    .setValue(log(0.01))
    .setSliderMode(0)
  ;
  thread("playMelody");
  thread("playSnare");
  thread("playTom");
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
  recomputeRhythmProbs();
}

void playMelody(){
  while(true){
    if(isMajor) scaleOffsets = majorOffsets; else scaleOffsets = minorOffsets;
    
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
      if(!noteOff){
        pitch = pitch%12 + 60; //For xylobot
      }
      nextRhythm = getNextRhythms(nextRhythm, rhythmProbs);
      int val = nextRhythm[0];
      nextRhythm = removeFirst(nextRhythm);
      int len = (int)(exp(noteLen)/val);
      
      Note note = new Note(channel, pitch, velocity, len);
      myBus.sendNoteOn(note);
      
      //Tonic count stuff
      if(pitch == tonic && abs(len - exp(noteLen)) < tol){
         tonicCount--;
         print("t");
         if(tonicCount == 0){
           exit();
         }
      }
      delay(len);
      if(noteOff){
        myBus.sendNoteOff(note);
      }
    }
    else{
      delay(10); //Stop looping infinitely fast when not playing; it causes problems
    }
  }
}

void playSnare(){
  while(true){
    if(playing) {
      int pitch = 36;
      nextRhythmSnare = getNextRhythms(nextRhythmSnare, rhythmProbsSnare);
      int val = nextRhythmSnare[0];
      nextRhythmSnare = removeFirst(nextRhythmSnare);
      int len = (int)(exp(noteLen)/val);
      Note note = new Note(channel, pitch, velocity, len);
      myBus.sendNoteOn(note);
      delay(len);
      if(noteOff){
        myBus.sendNoteOff(note);
      }
    }
    else{
      delay(10); //Stop looping infinitely fast when not playing; it causes problems
    }
  }
}
void playTom(){
  while(true){
    if(playing) {
      int pitch = 37;
      nextRhythmTom = getNextRhythms(nextRhythmTom, rhythmProbsTom);
      int val = nextRhythmTom[0];
      nextRhythmTom = removeFirst(nextRhythmTom);
      int len = (int)(exp(noteLen)/val);
      Note note = new Note(channel, pitch, velocity, len);
      myBus.sendNoteOn(note);
      delay(len);
      if(noteOff){
        myBus.sendNoteOff(note);
      }
    }
    else{
      delay(10); //Stop looping infinitely fast when not playing; it causes problems
    }
  }
}

public void Pause(int val) {
  if(playing) {
   playing = false;
   println("Pausing");
  }
  
  else {
   playing = true; 
   println("Resuming");
  }
}

//Gets the next rhythm for use in the melody. Generates more if needed.
int[] getNextRhythms(int[] nextRhythms, float[] rhythmProbs){
  if(nextRhythms.length == 0){
    nextRhythms = rhythms[0]; //Failsafe in case some race condition messes up the probability array
    double rand = random(1);
    for(int x = 0; x < rhythmProbs.length; x++){
      rand -= (double)rhythmProbs[x];
      if(rand <= 0){
        nextRhythms = rhythms[x];
        break;
      }
    }
  }
  return nextRhythms;
  
}

int[] removeFirst(int[] nextRhythms){
  int[] temp = new int[nextRhythms.length-1];
  for(int x = 1; x < nextRhythms.length; x++){
    temp[x-1] = nextRhythms[x];
  }
  return temp;
}

//Updates rhythm probabilities depending on the shortNoteBias value
void recomputeRhythmProbs(){
  //noteVar to rhythm conversions
  //0 means all quarter notes
  //1 means equal probability of quarter, eighth, sixteenth
  //Above 1 makes 16ths more common, quarter/eighths equally likely but less common
  float k = exp(shortNoteBias); //Because log scale

  rhythmProbs[0] = 1; //Constant at 1
  rhythmProbs[1] = min(k, 1); //Linear scale, capped at 1
  rhythmProbs[2] = k*k; //Quadratic scale, no cap
  rhythmProbs = normalize(rhythmProbs);

  //Snare
  k = exp(shortNoteBiasSnare);
  
  rhythmProbsSnare[0] = 1; //Constant at 1
  rhythmProbsSnare[1] = min(k, 1); //Linear scale, capped at 1
  rhythmProbsSnare[2] = k*k; //Quadratic scale, no cap
  rhythmProbsSnare = normalize(rhythmProbsSnare);
  
  //Tom
  k = exp(shortNoteBiasTom);

  rhythmProbsTom[0] = 1; //Constant at 1
  rhythmProbsTom[1] = min(k, 1); //Linear scale, capped at 1
  rhythmProbsTom[2] = k*k; //Quadratic scale, no cap
  rhythmProbsTom = normalize(rhythmProbsTom);
}

//Normalizes an array to sum to 1
float[] normalize(float[] probs){
  float sum = 0;
  for(int x = 0; x < probs.length; x++){
    sum += probs[x];
  }
  if(sum == 0){
    println("Problem normalizing");
    //Then keep the array unchanged because something broke
    return probs;
  }
  else{
    for(int x = 0; x < probs.length; x++){
      probs[x] = probs[x]/sum;
    }
  }
  return probs;
}

//processes delay in milliseconds
void delay(int time) {
  int current = millis();
  while (millis () < current+time){
    Thread.yield();
  } 
}