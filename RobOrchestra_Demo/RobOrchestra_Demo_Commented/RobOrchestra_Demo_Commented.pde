//IMPORT HELPFUL LIBRARIES
import themidibus.*; //Import midi library
import java.lang.Math; //To get random numbers

//INITIALIZE LOTS OF VARIABLES; GENERALLY NOT IMPORTANT
MidiBus myBus; //Creates a MidiBus object
MidiBus compBus;
int noteLen = 1000; //set chord length in milliseconds
int tonic = 60; //set key to C major
int next = 0; //keeps track of next chord. Always start with tonic
int[] divisions = {1, 2, 4}; //Possible number of melody nodes per chord(quarter, 2 eighths, 4 sixteenths)
int tonicCount = 0; //How many times a tonic chord has been played with a quarter note melody
int tonicTotal = 4; //Music stops when we reach this number of tonic chord/quarter note melodies (-1 for infinite loop)

//Chord attributes relocated to make them global
int channel = 0; //set channel. 0 for speakers
int pchannel1 = 0; //Percussion channel 1 (snare drum)
int pchannel2 = 0; //Percussion channel 2 (bass drum)
int velocity = 80; //chord volume
int melVelocity = 120; //melody note volume
int ticks = noteLen; //length in milliseconds
int trackBeat = 1;

//General logistics stuff
int fudgetime = 200; //Delay between computer and xylobot (computer plays first)
boolean printstuff = false;

//Moving drum patterns up here
float thresh = 0.01; //Tolerance for math stuff so you don't need infinitely many decimal places
float[] bassbeats = new float[]{4}; //Have the bass drum only play on 4
float[] snarebeats = new float[]{1, 2, 2.5, 3, 4, 4.5}; //Have the snare drum play on these subbeats

//New snare code to pick one of these four patterns at random
float[] pattern1 = new float[]{1.0, 2.0, 3.0, 4.0};
float[] pattern2 = new float[]{1.0, 2.0, 2.5, 3.0, 4.0, 4.5};
float[] pattern3 = new float[]{1.0, 2.0, 3.0, 3.5, 4.0};
float[] pattern4 = new float[]{1.0, 1.5, 2.0, 2.5, 3.0, 4.0};
float[][] snareOptions = new float[][]{pattern1, pattern2, pattern3, pattern4};


//Adding beat info
int nbeats = 4;
int beat = 0; //Increments first and one-indexed, so start at 0

//Variables for each individual subbeat
int i = -1; //Increments first and zero-indexed, so start at -1
int nsubbeats = lcm(divisions, beatsToNBeats(bassbeats), beatsToNBeats(snarebeats)); //Constant
int randNum;
int melnote;
ArrayList<Note> toPlayEarly = new ArrayList();
ArrayList<Note> toPlay = new ArrayList();

//Display info
PImage roboLogo;
ArrayList<String> toDisplay = new ArrayList();
int offset = 0;
String header = "NOTE: This is one beat behind what the orchestra is doing"; //Displays when offset==2
int generalLine = 0+offset;
int melodyLine = 6+offset;
int snareLine = 10+offset;
int bassLine = 15+offset;

//Flag that toggles as the code runs; starts true so a forced quarter note doesn't fire immediately
boolean disableTonic = true;

//TRANSITION MATRIX AND OTHER PROBABILITY STUFF
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

float[] probstuff = {0.2, 0.1, 0.2, 0.1, 0.2, 0.1, 0.1}; //To determine whether you want an in-chord tone or not
int[] degreeToNote = {tonic, tonic + 2, tonic + 4, tonic + 5, tonic + 7, tonic + 9, tonic + 11};

//END INITIALIZATION



//sets up screen
//Processing runs this function first; do all the setup here
void setup() {
  size(325, 400);
  background(0);

  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!

  myBus = new MidiBus(this, 0, 4); 
  compBus = new MidiBus(this, 0, 1);
  initializeText();
  roboLogo = loadImage("rc_logo.png");
  System.out.println("Starting");
}

//Helper function for displaying text
void initializeText(){
  //Initialize stuff to be displayed
  display("General", generalLine);
  display("Tonic Count: 0", generalLine+1);
  display("Subbeat Length: " + noteLen, generalLine+2);
  display("Chord Notes: " + degreeToNote[0] + " " + degreeToNote[2] + " " + degreeToNote[4], generalLine+3);
  display("Beat: 1", generalLine+4);
  
  display("Melody", melodyLine);
  display("Melody Notes: " + tonic, melodyLine+1);
  
  display("Snare Drum", snareLine);
  String temp = "Snare Beats:";
  for(int x = 0; x < snarebeats.length; x++){
    temp+=" " + snarebeats[x];
    if(x < snarebeats.length-1) temp+=",";
  }
  display(temp, snareLine + 1);
  
  temp = "Bass Beats:";
  for(int x = 0; x < bassbeats.length; x++){
    temp+=" " + bassbeats[x];
    if(x < bassbeats.length-1) temp+=",";
  }
  //display(temp, bassLine + 1);
  //display("Bass Drum", bassLine);
  
  //If there's an offset, display a header
  if(offset == 2){
     //display(header, 0); 
  }
}

//After running setup, this function loops forever
//Processing updates the display at some point here
//So we run this every subbeat for real-time updates
void draw() {
  //LOOP THROUGH AND PLAY ALL THE NOTES WE DETERMINED PREVIOUSLY (important to keep the display up-to-date)
  
  //Computer notes (delay added)
  //PLAY THE NOTES FROM THE COMPUTER
  for(int x = 0; x < toPlayEarly.size(); x++){
     compBus.sendNoteOn(toPlayEarly.get(x)); 
  }
  toPlayEarly = new ArrayList<Note>(); //Clear the list of notes to play
  delay(fudgetime);
  
  //Instruments
  //PLAY THE NOTES ON XYLOBOT
  //(The computer lags, so when using it instead of an actual instrument, we need to add a delay, which we call fudgetime)
  for(int x = 0; x < toPlay.size(); x++){
     myBus.sendNoteOn(toPlay.get(x)); 
  }
  toPlay = new ArrayList<Note>();
  
  //Run the next subbeat
  i = (i+1)%nsubbeats;
  
  
  //CHECK IF WE START A NEW BEAT
  if(i == 0){
    //Starting a new beat; old draw code is now here
    beat = beat % nbeats + 1; //Increment the beat; ranges from 1 to nbeats
    display("Melody Notes:", melodyLine+1);
    display("Beat: " + beat, generalLine+4);
  
    //If we haven't reached our tonic total, continue melody
    if (tonicTotal == -1 || tonicCount < tonicTotal) {
      //Run algorithm
      qprint("Choosing chord");
      next = runChord(next); //Get the next chord
      double randomSnare = Math.random() * 4;
      snarebeats = snareOptions[(int)randomSnare]; //Pick a random snare pattern to use this measure
      
      //At the start of each measure, print whatever the snare drum is doing
      if(trackBeat == 1) {
        String temp = "Snare Beats:";
        for(int x = 0; x < snarebeats.length; x++){
          temp+=" " + snarebeats[x];
          if(x < snarebeats.length-1) temp+=",";
        }
        display(temp, snareLine + 1);
        trackBeat++;
      }
      else if(trackBeat == 4) {
        trackBeat = 1; //Only 4 beats to a measure; make that cycle
      }
      else{
        trackBeat++;
      }
      
      //Display stuff to the screen
      display("Tonic Count: " + tonicCount, generalLine+1); //prints to screen
      //refreshText();
    }
    
    //Otherwise add a delay so the last note comes out (hopefully), then stop
    else{
      delay(noteLen*4); //Make sure the quarter note isn't just getting cut off when the program stops
      println("Done");
      System.exit(0);
    }
  }
  
  runSubbeat(); //This function already waits for the end of the subbeat
  refreshText();
}


int runChord(int currChord) {
  double randomNum = Math.random(); //Generate a random number to determine the next chord
  double sum = 0;
  int base, third, fifth, oct, i=0;

  //Chooses next chord based off probabilities in transition Matrix
  //determines chord notes to be played
  //PICK THE NEXT CHORD AND FIGURE OUT WHAT NOTES ARE IN IT
  for (i = 0; i < chords[currChord].length; i++) {
    sum += chords[currChord][i];

    //randomNum is a random number between 0 and 1.
    //To figure out what the next chord is, we do a cumulative sum across the current row of the transition matrix
    //When the sum exceeds the random number, use that chord
    if (randomNum < sum) {
      base = i+tonic; //root

      //major chords
      if (i == 0 || i == 5 || i == 7) {
        third = base+4; //3rd
        fifth = base+7; //5th
      }

      //minor chords
      else if (i == 2 || i == 9) {
        third = base+3; //3rd
        fifth = base+7; //5th
      }

      //dimished chords
      else {
        third = base+3; //3rd
        fifth = base+6; //5th
      }

      oct = base + 12; //root octave

      playChord(base, third, fifth, oct); //Play the current chord
      break;
    }
  }

  //returns index in matrix to the draw function to find next chord
  return i;
}

//plays the chord, and melody notes an octave higher
void playChord(int base, int third, int fifth, int oct) {
  //Create the midi notes and play the chord
  int[] notes= {base, third, fifth, oct};
  qprint("Chord");
  for (int x = 0; x < notes.length; x++) {
    storeNote(new Note(channel, notes[x], velocity, ticks), true);
  }

  display("Chord Notes: " + base + " " + third + " " + fifth, generalLine+3); //prints to screen
  
  //Initialize all the subbeat stuff you'll need for the beat and decide whether to force a tonic quarter note
  randNum = (int)(Math.random() * divisions.length); //Index of number of melody notes to play
  int subBeat = noteLen / nsubbeats; //Define the length of a sub-beat (now less than (or possibly equal to) the length of the actual melody note)

  melnote = -1;
  //check if tonic chord and quarter note melody combination
  //FORCE A TONIC QUARTER NOTE ON A I-CHORD IF YOU'RE PLAYING A QUARTER NOTE
  if (randNum == 0 && base == tonic) {
    if(!disableTonic){
      tonicCount++; //Add one to the number of times we've done this; this is used for termination
      melnote = tonic; //Set the note to the tonic note
      disableTonic = true; //Don't do forced tonic quarter notes repeatedly.
      qprint("Tonic count incremented");
    }
  }
  else{
     disableTonic = false; //Re-enable tonic quarter note forcing after not doing a forced tonic quarter note
  }
  display("Subbeat Length: " + subBeat*lcm(divisions, 1)/divisions[randNum], generalLine+2); //prints to screen
}

void runSubbeat(){
  int subBeat = noteLen/nsubbeats; //Get the subbeat length
  
  //Print count info
    //If it's a beat, just print "Bt" and the number
    if (i % nsubbeats == 0) {
      qprint("");
      qprint("Bt " + beat);
      display("Beat: " + beat, generalLine+4);
    }
    //Otherwise, print an appropriate syllable for the sub-beat
    else {
      qprint(getCountSyllable(i % nsubbeats, nsubbeats));
      addText(" " + getCountSyllable(i % nsubbeats, nsubbeats), generalLine+4);
    }
    
    //play melody note on determined subbeat
    if (i % (nsubbeats/divisions[randNum])==0) {
      qprint("Melody");
      if(melnote == -1 || randNum != 0){ //If neither is true, we've forced a tonic quarter note
        melnote = randMelodyNote2(probstuff); //If not forcing a tonic quarter note
      }
      else{
        qprint("Forcing tonic quarter note"); 
      }
      Note melody = new Note(channel, melnote, melVelocity, subBeat); //Generate the new note
      addText(" " + melnote, melodyLine+1);
      storeNote(melody); //Store the note to be played later
    }
    
    //If the current sub-beat is in the snare drum list, play a snare drum note
    //Check if the snare drum beat array contains the current subbeat
    if (fuzzyContains(beat + (float)(i)/nsubbeats, snarebeats, thresh)) {
      Note snareNote = new Note(pchannel1, 36, melVelocity, subBeat); //Generate a snare drum note
      storeNote(snareNote); //Store that snare drum note
      qprint("Snare: MIDI 36");
      display("Snare playing", snareLine+2);
    } else {
      display("", snareLine+2);
    }

    //Same for bass drum
    if (fuzzyContains(beat + (float)(i)/nsubbeats, bassbeats, thresh)) {
      Note bassNote = new Note(pchannel2, 38, melVelocity, subBeat);
      storeNote(bassNote);
      qprint("Bass drum: MIDI 38");
      //display("Bass playing", bassLine+2);
    } else {
      display("", bassLine+2);
    }

    delay(subBeat - fudgetime); //waits for remaining duration of subbeat before checking the next one
}

//chooses a melody note from the current chord tones
//(Might be obsolete)
int randMelodyNote(int[] options) {
  int randNum = (int)(Math.random() * 4);

  return options[randNum];
}

//Picks a random melody note based on the current chord
int randMelodyNote2(float[] options) {
  double rand = Math.random();
  //rand is between 0 and 1
  //Subtract stuff from the options array (which has probabilities for each scale degree)
  //When it gets negative, you have your note
  //(Same idea as picking a chord; not sure why I did subtraction here...)
  for (int x = 0; x < options.length; x++) {
    rand -= options[x];
    if (rand < 0) return degreeToNote[(x+7) % 7];
  }
  System.out.println("Total probabilities in the non-chord tone vector is less than 1?");
  return -1;
}

//UTILITY FUNCTIONS (from here until the end of the file; not important for big-picture stuff, but useful if you modify code)
//processes delay in milliseconds
void delay(int time) {
  int current = millis();
  while (millis () < current+time) Thread.yield();
}

//TEXT UTILITY FUNCTIONS (to keep the display from getting behind)
//Stores text you want displayed
void display(String text, int line){
  while(toDisplay.size() <= line){
     toDisplay.add(""); 
  }
  toDisplay.set(line, text); 
}

//Adds text to the text already being displayed
void addText(String text, int line){
   while(toDisplay.size() <= line){
     toDisplay.add(""); 
  }
  toDisplay.set(line, toDisplay.get(line) + text); 
}

//Refreshes the display by clearing everything, then writing the stored text (called every subbeat)
void refreshText(){
  background(0); //clear screen
  for(int line = 0; line < toDisplay.size(); line++){
    if(toDisplay.get(line) == null) toDisplay.set(line, "");
    text(toDisplay.get(line), 20, 20*(line+1)); 
  }
  image(roboLogo, 275, 10);
}

//NOTE UTILITY FUNCTIONS
//Stores a note to be played (use this rather than sending the note on directly so the display is accurate)
//Assumes you don't want the note early
void storeNote(Note n){
   toPlay.add(n); 
}

//Overloaded to allow for early notes
void storeNote(Note n, boolean early){
   if(early){
     toPlayEarly.add(n);
   }
   else{
     toPlay.add(n); 
   }
}

//Returns the syllable one would count on a given sub beat (1 e + a 2 e + a; 1 trip let 2 trip let; 1 2 3 4 5 2 2 3 4 5; etc.)
//Count: Number of subdivided beats so far (not zero-indexed)
//Res: Number of subdivisions per beat
//Don't call this function for count==1, since then it'll print 1 instead of the current beat number
String getCountSyllable(int count, int res) {
  double frac = 1.0*count/res;

  //Sixteenths
  if (frac == 1.0/4) {
    return "e";
  }
  if (frac == 1.0/2) {
    return "+";
  }
  if (frac == 3.0/4) {
    return "a";
  }

  //Triplets
  if (frac == 1.0/3) {
    return "trip";
  }
  if (frac == 2.0/3) {
    return "let";
  }
  return "" + count + "/" + res;
}

//DEBUGGING FUNCTIONS
//Prints all the elements in an array
//Not disabled by printstuff since you'd only use this in debugging
void printArray(Object[] A) {
  System.out.print("{");
  for (int x = 0; x < A.length; x++) {
    System.out.print(A[x]); 
    if (x < A.length - 1) System.out.print(", ");
  }
  System.out.println("}");
}

void qprint(Object s){
   if(printstuff)println(s); 
}

//NUMERICAL UTILITY FUNCTIONS (that hopefully no one actually has to look at):

//Utility function to see if a list has anything close to the input
//Essentially, just abs(y - x) < epsilon, but for a full array
//Mostly used so I can just throw constants in to 2 decimal places if I want the percussion to play triplets

//x: Value being checked
//myList: List being checked
//res: Allowed difference between x and elements of myList
boolean fuzzyContains(float x, float[] myList, double res) {
  for (int n = 0; n < myList.length; n++) {
    if (abs((float)(myList[n]-x)) <= res) { //Why does abs only accept floats?
      return true;
    }
  }
  return false;
}

//Gets greatest common factor (GCF)of two ints 
//Uses the Euclidean algorithm
//Basic idea: If a number d is a common divisor of a and b, it must also divide a - b (which is less than a or b)
//So recurse down until a or b is 0, and then the other is the GCF
int gcf(int a, int b) {
  //Make a >= b
  if (a < b) {
    int temp = a;
    a = b;
    b = temp;
  }
  if (b == 0) {
    return a;
  }
  return gcf(a-b, b);
}

//Gets least common multiple (LCM) for an array and multiple ints
//Basic idea: Keep a temporary LCM and multiply in each new value
//But at each step, also divide by the GCF so you don't unnecessarily duplicate factors
int lcm(int[] B, int... A) {
  int temp = 1;
  //Go through all the elements
  for (int x = 0; x < A.length; x++) {
    temp = temp*A[x]/gcf(temp, A[x]);
  }
  for (int x = 0; x < B.length; x++) {
    temp = temp*B[x]/gcf(temp, B[x]);
  }
  return temp;
}

//Same as above but for multiple arrays
//Literally just calls the above function on my temporary LCM and each array in turn
int lcm(int[]... A) {
  int temp = 1;
  for (int x = 0; x < A.length; x++) {
    temp = lcm(A[x], temp);
  }
  return temp;
}

//Converts my decimals (play on beat 4.5) to a number of sub-beats needed to make that happen (need 2 subbeats)
//Basic idea: Keep trying denominators until something works
int beatToNBeat(float d) {
  for (int x = 1; x <= (int)(1/thresh); x++) {
    if (min(abs(d*x%1), abs(1 - (abs(d*x)%1))) < thresh) {
      return x;
    }
  }
  return (int)(1/thresh);
}

//Same as above, but with full arrays
//Literally just calls the above on each element of the array
//Returns an array that I can plug into LCM (though maybe I should have just done that calculation in here anyway)
int[] beatsToNBeats(float[] D) {
  //System.out.println("Converting decimals to ints:");
  int[] temp = new int[D.length];
  for (int x = 0; x < D.length; x++) {
    temp[x] = beatToNBeat(D[x]);
  }
  return temp;
}