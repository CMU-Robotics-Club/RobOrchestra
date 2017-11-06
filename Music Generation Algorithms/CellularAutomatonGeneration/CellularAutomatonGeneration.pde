import themidibus.*; //Import midi library
import java.lang.Math; //To get random numbers

//Open SimpleSynth to play on Mac

MidiBus myBus; //Creates a MidiBus object
int channel = 0; //set channel. 0 for speakers
int velocity = 120; //melody note volume
int noteLen = 1000; //set chord length in milliseconds

int tonicCount = 10; //Number of whole-note tonics to play before stopping

int tonic = 60; //set key to C major
boolean minor = true;
int[] scaleOffsets = {0, 2, 4, 5, 7, 9, 11, 12};
int[] minorOffsets = {0, 2, 3, 5, 7, 9, 10, 12};
int[][] rhythms = {{1}, {2, 2}, {4, 4, 4, 4}};
int[] nextRhythm = {}; //Start on a whole note

int[] ca = {1}; //Starting seed (overwritten by default)
int[] ca2 = {1}; //Starting seed (overwritten by default)
int buffer = 40; //Mostly for visuals

int rule = 150;
int rule2 = 150;
//18 for Sierpinski
//150 for stuff that supposedly sounds good
//30 is complicated

//With the rule: Sum the row, mod by 8, grab the right scale degree
//100 is totally trivial
//199 is a scale

//sets up screen
void setup() {
  //size(325, 400);
  //background(0);

  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  myBus = new MidiBus(this, 0, 1);
  
  //Overwrites starting seeds
  ca = generateSeed(0.9);
  ca2 = generateSeed(0.9);
  
  
  printArray(ca);
  printArray(ca2);
  //Might not want to randomize these...
  //rule = (int)(Math.random()*255);
  //rule2 =(int)(Math.random()*255);
  println(rule);
  println(rule2);
  println();
}

int[] generateSeed(double p){
  //Generate a random starting seed
  double rand = Math.random();
  int count = 1;
  while(rand < p){
     rand = Math.random();
     count++;
  }
  int[] ca = new int[count];
  for(int x = 0; x < count; x++){
    rand = Math.random();
    ca[x] = round((float)rand);
  }
  if(sum(ca) == 0){
     ca = generateSeed(p); //Throw out trivial 0 seeds
  }
  return ca;
}


//this function repeats indefinitely
void draw() {
  if(buffer > 0){
    print(nSpaces(--buffer));
    printArray(ca); 
  }
  if(buffer == 0){
    println("Stopped printing because the array is getting really long...");
    buffer--;
  }
  int pitch = getPitch(ca);
  int len = noteLen / getNextRhythm(ca2);
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
  
  ca = runCA(ca, rule);
  ca2 = runCA(ca2, rule2);
  delay(len);
  myBus.sendNoteOff(note);
}

void printArray(int[] out){
   for(int x = 0; x < out.length; x++){
      print(out[x]); 
   }
   print('\n');
}

int getPitch(int[] in){
   //Sum the row, mod by 8, get a number from 0 to 7, adjust and add to tonic
   int temp = (sum(in) + 1) % 8; //Always start with the tonic, but we seed with 1
   int pitch;
   if(!minor){
     pitch = tonic + scaleOffsets[temp];
   }
   else{
     pitch = tonic + minorOffsets[temp];
   }
   return pitch;
}

int getNextRhythm(int[] ca){
  int in = (sum(ca) + 2) % rhythms.length; //Start with a whole note
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

int[] runCA(int[] in, int rule){
  int[] out = new int[ca.length+2];
  int[] digits = getDigits(rule);
  for(int x = -1; x < ca.length+1; x++){ //x is the center of the relevant window on in
    int l = 0, m = 0, r = 0;
    if(x-1 >= 0 && x-1 < ca.length){
      l = ca[x-1];
    }
    if(x >= 0 && x < ca.length){
      m = ca[x];
    }
    if(x+1 >= 0 && x+1 < ca.length){
      r = ca[x+1];
    }
    int index = 4*l + 2*m + r;
    out[x+1] = digits[index]; //out is offset by 1 from ca
  }
  return out;
}

int[] getDigits(int in){
  //Gets the last 8 binary digits of the input number
  //Prints backward: out[0] is the ones place, out[7] is the 128s place, etc.
  int[] out = {0, 0, 0, 0, 0, 0, 0, 0};
  for(int x = 0; x < 8; x++){
    out[x] = (in % round(pow(2, 1+x))) / round(pow(2, x));
  }
  return out;
}

String nSpaces(int n){
  String temp = "";
  for(int x = 0; x < n; x++){
     temp += " "; 
  }
  return temp;
}

int valFromIndex(int[] A, int i){
   if(i >= 0 && i < A.length){
      return A[i]; 
   }
   return 0;
}

int sum(int[] A){
  int temp = 0;
  for(int x = 0; x < A.length; x++){
    temp += A[x];
  }
  return temp;
}

//processes delay in milliseconds
void delay(int time) {
  int current = millis();
  while (millis () < current+time) Thread.yield();
}