import themidibus.*; //Import midi library
import java.lang.Math; //To get random numbers

MidiBus myBus; //Creates a MidiBus object
int noteLen = 1000; //set chord length in milliseconds
int tonic = 60; //set key to C major
int next = 0; //keeps track of next chord. Always start with tonic
int[] divisions = {1,2,4}; //Possible number of melody nodes per chord(quarter, 2 eights, 4 sixteenths)
int tonicCount = 0; //How many times a tonic chord has been played with a quarter note melody
int tonicTotal = 3; //Music stops when we reach this number of tonic chord/quarter note melodies

//Chord attributes relocated to make them global
int channel = 1; //set channel. 0 for speakers
int pchannel1 = 0; //Percussion channel 1 (snare drum)
int pchannel2 = 0; //Percussion channel 2 (bass drum)
int velocity = 80; //chord volume
int melVelocity = 120; //melody note volumn
int ticks = noteLen; //length in milliseconds

//Moving drum patterns up here
float thresh = 0.01;
float[] bassbeats = new float[]{4};
float[] snarebeats = new float[]{1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5};

//Adding beat info
int nbeats = 4;
int beat = 0; //Increments first, so start at 0

                        //I   no    ii    no    no    IV    no    V     no    vi    no    viid
float[][] chords = {{0.20, 0.00, 0.10, 0.00, 0.00, 0.30, 0.00, 0.15, 0.00, 0.20, 0.00, 0.05}, //I
                    {0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00}, //no
                    {0.00, 0.00, 0.05, 0.00, 0.00, 0.00, 0.00, 0.90, 0.00, 0.00, 0.00, 0.05}, //ii
                    {0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00}, //no
                    {0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00}, //iii but no
                    {0.20, 0.00, 0.20, 0.00, 0.00, 0.10, 0.00, 0.45, 0.00, 0.00, 0.00, 0.05}, //IV
                    {0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00}, //no
                    {0.50, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.20, 0.00, 0.15, 0.00, 0.15}, //V
                    {0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00}, //no
                    {0.10, 0.00, 0.10, 0.00, 0.00, 0.20, 0.00, 0.50, 0.00, 0.05, 0.00, 0.05}, //vi
                    {0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00}, //no
                    {0.95, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.05}};//vii(dim)

float[] probstuff = {0.2, 0, 0.1, 0, 0.2, 0.1, 0, 0.2, 0, 0.1, 0, 0.1}; //To determine whether you want an in-chord tone or not

//sets up screen
void setup() {
  size(200,200);
  background(0);

  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
   
  myBus = new MidiBus(this, 0, 1); //Sends midi output to speakers
  System.out.println("Starting");
}

//this function repeats indefinitely
//note that the output displayed in the window is one chord behind what is being played
void draw() {
  //System.out.println("Starting draw");
  beat = beat % nbeats + 1; //Ranges from 1 to nbeats
  //Note: we pass beat through the chooseChord function into the playChord function so the percussion and counter know what beat it is
  
  //If we haven't reached our tonic total, continue melody
  if(tonicCount < tonicTotal) {
    background(0); //clear screen
    next = chooseChord(next, beat);
    text("Tonic Count: " + tonicCount, 20, 80); //prints to screen
  }
}

//Beat gets passed through to playChord
int chooseChord(int currChord, int beat){
  //System.out.println("Choosing chord");
  
  double randomNum = Math.random();
  double sum = 0;
  int base, third, fifth, oct, i=0;
  
  //Chooses next chord based off probabilities in transition Matrix
  //determines chord notes to be played
  for(i = 0; i < chords[currChord].length; i++) {
    sum += chords[currChord][i];
    
    if(randomNum < sum) {
      base = i+tonic; //root
      
      //major chords
      if(i == 0 || i == 5 || i == 7) {
        third = base+4; //3rd
        fifth = base+7; //5th
      }
      
      //minor chords
      else if(i == 2 || i == 9) {
        third = base+3; //3rd
        fifth = base+7; //5th
      }
      
      //dimished chords
      else {
        third = base+3; //3rd
        fifth = base+6; //5th
      }
      
      oct = base + 12; //root octave
      
      playChord(base, third, fifth, oct, beat);
      
      break;
    }
  }
  
  //returns index in matrix to the draw function to find next chord
  return i;
}

//plays the chord, and melody notes an octave higher
void playChord(int base, int third, int fifth, int oct, int beat) {
  //System.out.println("Playing chord");
  
  //Create the midi notes
  Note note1 = new Note(channel, base, velocity, ticks);
  Note note2 = new Note(channel, third, velocity, ticks);
  Note note3 = new Note(channel, fifth, velocity, ticks);
  Note note4 = new Note(channel, oct, velocity, ticks);
  
  int[] notes= {base, third, fifth, oct};
  text("Chord notes: " + base + " " + third + " " + fifth, 20, 20); //prints to screen
  
  int randNum = (int)(Math.random() * divisions.length);
  int nsubbeats = lcm(divisions, beatsToNBeats(bassbeats), beatsToNBeats(snarebeats));

  //nsubbeats is the largest possible number of subbeats one might need, given the possible melody subdivision and the percussion subdivisions
  
  //check if tonic chord and quarter note melody combination
  if(randNum == 0 && base == tonic) {
    //Note: This increments tonic count based on whether we do a quarter note for the right chord (melody note irrelevant)
    //I'm not sure we want to do that with more variance on the melody, but I'll leave it for now
    tonicCount++;
  }
  
  int subBeat = noteLen / nsubbeats; //Define the length of a sub-beat (now less than (or equal to) the length of the actual melody note)
  
  text("subBeat length: " + subBeat, 20, 40); //prints to screen
  for(int i = 0; i < nsubbeats; i++){
    
    //Print count info
    //If it's a beat, just print "Bt" and the number
    if(i % nsubbeats == 0){
        println("");
        println("Bt " + beat);
        //text("Beat " + (i/nsubbeats+1), 20, 20);
        //text("", 20, 40);
      }
      //Otherwise, print an appropriate syllable for the sub-beat
      else{
        println(getCountSyllable(i % nsubbeats, nsubbeats));
        //text(getCountSyllable(i % nsubbeats, nsubbeats), 20, 40);
      }
    
    //play chord on downbeat
    if(i == 0) {
      System.out.println("Chord");
      myBus.sendNoteOn(note1);
      myBus.sendNoteOn(note2);
      myBus.sendNoteOn(note3);
      myBus.sendNoteOn(note4);
    }
    
    //play melody note on determined subbeat
    if(i % divisions[randNum]==0){
      System.out.println("Melody");
      int melnote = randMelodyNote2(probstuff, base);
      Note melody = new Note(channel, melnote + 12, melVelocity, subBeat);
      String space = "";
      for(int x = 0; x < i/divisions[randNum]; x++){
         space += "     "; 
      }
      text("Melody: " + space + melnote, 20, 60);
      myBus.sendNoteOn(melody);
    }
    
    //If the current sub-beat is in the snare drum list, play a snare drum note
    if(fuzzyContains(beat + (float)(i)/nsubbeats, snarebeats, thresh)){
        Note snareNote = new Note(pchannel1, 36, melVelocity, subBeat);
        myBus.sendNoteOn(snareNote);
        println("Snare: MIDI 36");
        //text("Snare", 20, 60);
      }
      else{
        //text("", 20, 60);
      }

      //Same for bass drum
      if(fuzzyContains(beat + (float)(i)/nsubbeats, bassbeats, thresh)){
        Note bassNote = new Note(pchannel2, 38, melVelocity, subBeat);
        myBus.sendNoteOn(bassNote);
        println("Bass drum: MIDI 38");
        //text("Bass", 20, 80);
      }
      else{
        //text("", 20, 80);
      }
  
      delay(subBeat); //waits for duration of subbeat before checking the next one
  }
}

//chooses a melody note from the current chord tones
int randMelodyNote(int[] options) {
  int randNum = (int)(Math.random() * 4);
  
  return options[randNum];
  
}

int randMelodyNote2(float[] options, int base){
  double rand = Math.random();
  for(int x = 0; x < options.length; x++){
    rand -= options[x];
    if(rand < 0) return base + x;
  }
  return -1;
}

//processes delay in milliseconds
void delay(int time) {
  int current = millis();
  while (millis () < current+time) Thread.yield();
}

//Returns the syllable one would count on a given sub beat (1 + 2 + 3 + 4 +; 1 trip let 2 trip let; 1 2 3 4 5 2 2 3 4 5; etc.)

//Count: Number of subdivided beats so far (not zero-indexed)
//Res: Number of subdivisions per beat
//Don't call this function for count==1, since then it'll print 1 instead of the current beat number
String getCountSyllable(int count, int res){
  double frac = 1.0*count/res;
  
  //Sixteenths
  if(frac == 1.0/4){
    return "e";
  }
  if(frac == 1.0/2){
    return "+";
  }
  if(frac == 3.0/4){
    return "a";
  }
  
  //Triplets
  if(frac == 1.0/3){
    return "trip";
  }
  if(frac == 2.0/3){
    return "trip";
  }
  return "" + count + "/" + res;
}

//For utility/debugging
//Prints all the elements in an array
void printArray(Object[] A){
  System.out.print("{");
  for(int x = 0; x < A.length; x++){
     System.out.print(A[x]); 
     if(x < A.length - 1) System.out.print(", ");
  }
  System.out.println("}");
}

//NUMERICAL UTILITY FUNCTIONS (that hopefully no one actually has to look at):

//Utility function to see if a list has anything close to the input
//Essentially, just abs(y - x) < epsilon, but for a full array
//Mostly used so I can just throw constants in to 2 decimal places if I want the percussion to play triplets

//x: Value being checked
//myList: List being checked
//res: Allowed difference between x and elements of myList
boolean fuzzyContains(float x, float[] myList, double res){
  for(int n = 0; n < myList.length; n++){
    if(abs((float)(myList[n]-x)) <= res){ //Why does abs only accept floats? Why not doubles (what's the difference?)? And why not ints?
      return true;
    }
  }
  return false;
}

//Gets greatest common factor (GCF)of two ints 
//Uses the Euclidean algorithm
//Basic idea: If a number d is a common divisor of a and b, it must also divide a - b (which is less than a or b)
//So recurse down until a or b is 0, and then the other is the GCF
int gcf(int a, int b){
  //System.out.println("Starting GCF");
  //Make a >= b
  if(a < b){
    int temp = a;
    a = b;
    b = temp;
  }
  if(b == 0){
     return a; 
  }
  //System.out.println("Ending GCF");
  return gcf(a-b, b);
}

//Gets least common multiple (LCM) for an array and multiple ints
//Basic idea: Keep a temporary LCM and multiply in each new value
//But at each step, also divide by the GCF so you don't unnecessarily duplicate factors
int lcm(int[] B, int... A){
  //System.out.println("Getting mini-LCM:");
  int temp = 1;
  //Go through all the elements
  for(int x = 0; x < A.length; x++){
    temp = temp*A[x]/gcf(temp, A[x]);
  }
  for(int x = 0; x < B.length; x++){
    temp = temp*B[x]/gcf(temp, B[x]);
  }
  //System.out.println(temp);
  return temp;
}

//Same as above but for multiple arrays
//Literally just calls the above function on my temporary LCM and each array in turn
int lcm(int[]... A){
  //System.out.println("Getting LCM");
  int temp = 1;
  for(int x = 0; x < A.length; x++){
    temp = lcm(A[x], temp);
  }
  //System.out.println(temp);
  return temp;
}

//Converts my decimals (play on beat 4.5) to a number of sub-beats needed to make that happen (need 2 subbeats)
//Basic idea: Keep trying denominators until something works
int beatToNBeat(float d){
  for(int x = 1; x <= (int)(1/thresh); x++){
     if(min(abs(d*x%1), abs(1 - (abs(d*x)%1))) < thresh){
        return x; 
     }
  }
  return (int)(1/thresh);
}

//Same as above, but with full arrays
//Literally just calls the above on each element of the array
//Returns an array that I can plug into LCM (though maybe I should have just done that calculation in here anyway)
int[] beatsToNBeats(float[] D){
   //System.out.println("Converting decimals to ints:");
   int[] temp = new int[D.length];
   for(int x = 0; x < D.length; x++){
      temp[x] = beatToNBeat(D[x]); 
   }
   //printArray(temp);
   return temp;
}