import themidibus.*; //Import midi library
import java.lang.Math; //To get random numbers
import java.io.*; //For outputting stuff

//Phrases to be played
//Positive numbers mean make a new phrase of that many measures
//Non-positive numbers mean absolute value and grab the phrase at that index
//So 0 grabs the first phrase, -1 grabs the second, etc.
int[] input = {1, 0, 1, -2, 0};

MidiBus myBus; //Creates a MidiBus object
MidiBus compBus;
int noteLen = 1000; //set chord length in milliseconds
int tonic = 60; //set key to C major
int next = 0; //keeps track of next chord. Always start with tonic. Updates in generateChord()
int[] divisions = {1, 2, 4}; //Possible number of melody nodes per chord(quarter, 2 eighths, 4 sixteenths)
int tonicCount = 0; //How many times a tonic chord has been played with a quarter note melody
int tonicTotal = 4; //Music stops when we reach this number of tonic chord/quarter note melodies (-1 for infinite loop)

//Chord attributes relocated to make them global
int channel = 0; //set channel. 0 for speakers
int pchannel1 = 1; //Percussion channel 1 (snare drum)
int pchannel2 = 2; //Percussion channel 2 (bass drum)
int velocity = 80; //chord volume
int melVelocity = 120; //melody note volume
int ticks = noteLen; //length in milliseconds
int nbeats = 4; //Beats per measure
int trackBeat = 1;

//General logistics stuff
int fudgetime = 200; //Delay between computer and xylobot (computer plays first); set to 0 if no computer
boolean printstuff = false;

//Moving drum patterns up here
float thresh = 0.01;
float[] bassbeats = new float[]{4};
float[] snarebeats = new float[]{1, 2, 2.5, 3, 4, 4.5};
float[] pattern1 = new float[]{1.0, 2.0, 3.0, 4.0};
float[] pattern2 = new float[]{1.0, 2.0, 2.5, 3.0, 4.0, 4.5};
float[] pattern3 = new float[]{1.0, 2.0, 3.0, 3.5, 4.0};
float[] pattern4 = new float[]{1.0, 1.5, 2.0, 2.5, 3.0, 4.0};
float[][] snareOptions = new float[][]{pattern1, pattern2, pattern3, pattern4};

//Variables for each individual subbeat
int i = -1; //Counts current subbeat; incremented first and zero-indexed, so start at -1;
final int nsubbeats = lcm(divisions, beatsToNBeats(bassbeats), beatsToNBeats(snarebeats)); //Constant
int randNum; //Random index used in the divisions array to get the number of beats per measure; global because it's a placeholder for tonic quarter notes
int melnote; //Stores the next melody note to be added; global so it can act as a placeholder for forced tonic notes
int beatIndex = -1;
int measureIndex = -1;
ArrayList<Measure> piece;

//Display info
PImage roboLogo;
ArrayList<String> toDisplay = new ArrayList();
int offset = 0;
String header = "NOTE: This is one beat behind what the orchestra is doing"; //Displays when offset==2
int generalLine = 0+offset;
int melodyLine = 6+offset;
int snareLine = 10+offset;
int bassLine = 15+offset;

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

//Flag that toggles as the code runs; starts true so a forced quarter note doesn't fire immediately
boolean disableTonic = true;

//IO stuff
File outputFile = new File("RobOrchestra/output.txt");
FileWriter writer;

//sets up screen
void setup() {
  size(325, 400);
  background(0);

  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!

  myBus = new MidiBus(this, 0, 1); 
  compBus = new MidiBus(this, 0, 0);
  initializeText();
  roboLogo = loadImage("rc_logo.png");
  println("Starting");
  
  try{
    writer = new FileWriter(outputFile);
    //Input settings for piece here:
    //Put in a list of integers
    //Positive numbers are the phrase lengths of new phrases
    //Non-positive numbers copy previous phrases (0 grabs first phrase, -1 grabs second, etc.)
    piece = generatePiece(input);
    writer.close();    
  }
  catch(IOException e){
     System.out.println("File IO error");
     exit();
  }
  finally{
  
  }
}

//this function repeats indefinitely
void draw() {
  //Run the next subbeat
  i = (i+1)%nsubbeats;
  
  if(i == 0){
    //Starting a new beat; old draw code is now here
    //beat = beat % nbeats + 1; //Increment the beat; ranges from 1 to nbeats
    beatIndex = (beatIndex + 1) % nbeats;
    display("Melody Notes:", melodyLine+1);
    display("Beat: " + (beatIndex+1), generalLine+4);
    
  
    //Run algorithm (create the next beat to run after generating percussion stuff)
    if(beatIndex == 0) {
      measureIndex++;
      //Check if you're done with the piece
      if(piece.size() <= measureIndex){
        //Add a delay so the last note comes out, then stop
        delay(noteLen*4); //Make sure the quarter note isn't just getting cut off when the program stops
        println("Done");
        System.exit(0);
      }
      
      //Display any measure-by-measure data (ex: snare drum pattern)
      for(int x = 0; x < piece.get(measureIndex).output.size(); x++){
        display(piece.get(measureIndex).output.get(x).message, piece.get(measureIndex).output.get(x).line);
      }
    }
    //Display any beat-by-beat data (ex: current chord)
    for(int x = 0; x < piece.get(measureIndex).beats[beatIndex].output.size(); x++){
      display(piece.get(measureIndex).beats[beatIndex].output.get(x).message, piece.get(measureIndex).beats[beatIndex].output.get(x).line);
    }
  }
   
  //Process current subbeat
  playSubbeat(piece.get(measureIndex).beats[beatIndex], i);
  
  //Print the next subbeat's notes
  printSubbeat(piece.get(measureIndex).beats[beatIndex], i);
  refreshText();
}

//Generate a piece based on a list of integers as input
//Positive integers create a new phrase of the given length
//Non-negative integers duplicate an existing phrase (0 grabs the 0th index, -1 the 1st, etc.)
ArrayList<Measure> generatePiece(int[] input){
  ArrayList[] phrases = new ArrayList[input.length];
  int[] phrasenums = new int[input.length];
  int temp = 1;
  ArrayList<Measure> output = new ArrayList();
  output.add(new Measure(nbeats));
  String toPrint = "";
  for(int x = 0; x < input.length; x++){
    if(input[x] > 0){
       phrases[x] = generatePhrase(input[x], 1);
       phrasenums[x] = temp;
       temp++;
    }
    else{
       phrases[x] = phrases[-1*input[x]];
       phrasenums[x] = phrasenums[-1*input[x]];
    }
    output = combinePhrases(output, phrases[x]);
    
    toPrint += "Phrase " + phrasenums[x] + ":\n\n";
    for(int y = 0; y < phrases[x].size(); y++){
       toPrint+=phrases[x].get(y).toString(); 
    }
  }
   
   
   try{
      writer.write(toPrint);
    }
    catch(IOException e){
       System.out.println("File IO error");
       exit();
    }
    finally{
    
    }
   
   return output;
}

//Combines multiple ArrayList<Measure> objects into a single one (without modifying the originals)
ArrayList<Measure> combinePhrases(ArrayList<Measure>... input){
  ArrayList<Measure> output = new ArrayList();
  for(int x = 0; x < input.length; x++){
      for(int y = 0; y < input[x].size(); y++){
         output.add(input[x].get(y)); 
      }
  }
  return output;
}

//Generate a phrase of the given number of tonics and measures
//Might infinite loop for impossible settings, though
ArrayList<Measure> generatePhrase(int numMeasures, int numTonics){
  ArrayList<Measure> phrase = new ArrayList();
  tonicCount = 0;
  while(tonicCount < numTonics){
     phrase.add(generateMeasure(numTonics)); 
  }
  if(phrase.size() != numMeasures){
     return generatePhrase(numMeasures, numTonics);
  }
  tonicCount = 0;
  return phrase;
}

//Generates a measure
Measure generateMeasure(int numTonic){
  
   Measure out = new Measure(nbeats);
   
   //Pick a snare pattern for the measure
   double randomSnare = Math.random() * 4;
   snarebeats = snareOptions[(int)randomSnare];
   String temp = "Snare Beats:";
   for(int x = 0; x < snarebeats.length; x++){
     temp+=" " + snarebeats[x];
     if(x < snarebeats.length-1) temp+=",";
   }
   out.addOutput(temp, snareLine + 1);
   Beat tempBeat = new Beat();
   //Generate the beats in the measure
   for(int x = 0; x < out.nbeats; x++){
     if (!(tonicTotal == -1 || tonicCount < numTonic)){
       //If you're done, just keep repeating tonic quarter notes for the rest of the measure
       //TODO: Make this do something a bit more interesting and/or intelligent instead
       beatIndex = x;
       tempBeat.forcedTonic = false;
       tempBeat.notes = new ArrayList[nsubbeats];
       for(int n = 0; n < nsubbeats; n++){
          tempBeat.notes[n] = new ArrayList(); 
       }
       switch((nbeats-x-1)%3){
          case 0:
            tempBeat.notes[0].add(new Note(channel, tonic, melVelocity, noteLen));
            break;
          case 1:
            tempBeat.notes[0].add(new Note(channel, tonic+7, melVelocity, noteLen));
            break;
          case 2:
            tempBeat.notes[0].add(new Note(channel, tonic+3, melVelocity, noteLen));
            break;
       }
       tempBeat.getTextFromNotes();
       out.setBeat(x, new Beat(tempBeat));
     }
     else {
       beatIndex = x;
       tempBeat = generateBeat(next);
       out.setBeat(x, new Beat(tempBeat));
     }
   }
   beatIndex = -1;
   return out;
}

 Beat generateBeat(int c){
   
    //GET SUBBEAT LENGTH
    randNum = (int)(Math.random() * divisions.length); //Index of number of melody notes to play
    int subbeatlen = noteLen / nsubbeats; //Define the length of a sub-beat (now less than (or possibly equal to) the length of the actual melody note)
    display("Subbeat Length: " + subbeatlen*lcm(divisions, 1)/divisions[randNum], generalLine+2); //prints to screen
    
    //INITIALIZE THE ARRAYLISTS FOR THE BEAT WE WANT TO RETURN
    ArrayList<Note>[] onotes = new ArrayList[nsubbeats];
    for(int x = 0; x < nsubbeats; x++){
       onotes[x] = new ArrayList<Note>(); 
    }
    ArrayList<Note>[] oenotes = new ArrayList[nsubbeats];
    for(int x = 0; x < nsubbeats; x++){
       oenotes[x] = new ArrayList<Note>(); 
    }
    ArrayList<String>[] onotetext = new ArrayList[nsubbeats];
    for(int x = 0; x < nsubbeats; x++){
       onotetext[x] = new ArrayList<String>(); 
    }
   
    //PICK AND STORE THE NEXT CHORD
    generateChord(c, oenotes);
    String toDisplay = "Chord Notes: " + oenotes[0].get(0).pitch + " " + oenotes[0].get(1).pitch + " " + oenotes[0].get(2).pitch; //prints to screen
      
    
    //DECIDE WHETHER TO STORE MELODY NOTES
    tonicCheck(oenotes[0].get(0).pitch);
    
    //GENERATE MELODY/PERCUSSION NOTES
    boolean temp = generateMelody(subbeatlen, onotes, onotetext);
   
   Beat output = new Beat(divisions[randNum], onotes, oenotes, onotetext);
   output.forcedTonic = temp;
   output.addOutput("Subbeat Length: " + subbeatlen*lcm(divisions, 1)/divisions[randNum], generalLine+2);
   output.addOutput(toDisplay, generalLine + 3);
   return output;
 }
 
 ArrayList<Note> generateChord(int c, ArrayList<Note>[] oenotes){
   ArrayList<Note> output = new ArrayList<Note>();
   
    double randomNum = Math.random();
    double sum = 0;
    int base=0, third=0, fifth=0, oct=0, i=0;
    
    //Chooses next chord based off probabilities in transition Matrix
    //determines chord notes to be played
    for (i = 0; i < chords[c].length; i++) {
      sum += chords[c][i];
      
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
      
        //STORE CHORD IN FIRST INDEX OF NOTES
        int[] notes= {base, third, fifth, oct};
        qprint("Chord");
        for (int x = 0; x < notes.length; x++) {
          oenotes[0].add(new Note(channel, notes[x], velocity, ticks));
          
        }
        
        next = i; //Store this as the new chord so we generate something that makes sense
        break;
      }
    }
    
    
    return output;
 }
 
 void tonicCheck(int base){
   //DECIDE WHETHER TO FORCE A TONIC QUARTER NOTE
    melnote = -1;
    //check if tonic chord and quarter note melody combination
    if (randNum == 0 && base == tonic) {
      if(!disableTonic){
        tonicCount++;
        melnote = tonic;
        disableTonic = true;
        qprint("Tonic count incremented");
      }
    }
    else{
       disableTonic = false; 
    }
 }
 
 //Return whether you forced a tonic note
 boolean generateMelody(int subbeatlen, ArrayList<Note>[] onotes, ArrayList<String>[] onotetext){
   //We're storing all the beats in the right places in this function; array(lists) are mutable
   boolean output = false;
   
  for(int i = 0; i < nsubbeats; i++){
    if (i % (nsubbeats/divisions[randNum])==0) {
      qprint("Melody");
      if(melnote == -1 || randNum != 0){ //If neither is true, we've forced a tonic quarter note
        melnote = randMelodyNote2(probstuff);
      }
      else{
        output = true;
        qprint("Forcing tonic quarter note"); 
      }
      Note melody = new Note(channel, melnote, melVelocity, subbeatlen);
      onotes[i].add(melody);
      onotetext[i].add("" + melnote);
    }
    
    //If the current sub-beat is in the snare drum list, play a snare drum note
    if (fuzzyContains(beatIndex + 1 + (float)(i)/nsubbeats, snarebeats, thresh)) {
      Note snareNote = new Note(pchannel1, 36, melVelocity, subbeatlen);
      onotes[i].add(snareNote);
      qprint("Snare: MIDI 36");
      display("Snare playing", snareLine+2);
    } else {
      display("", snareLine+2);
    }

    //Same for bass drum
    if (fuzzyContains(beatIndex + 1 + (float)(i)/nsubbeats, bassbeats, thresh)) {
      Note bassNote = new Note(pchannel2, 38, melVelocity, subbeatlen);
      onotes[i].add(bassNote);
      qprint("Bass drum: MIDI 38");
      display("Bass playing", bassLine+2);
    } else {
      display("", bassLine+2);
    } 
  }
  return output;
 }
 
 void playSubbeat(Beat b, int i){
     if(i >= b.notes.length) return;
     if(i < 0) return;
     
     qprint("Subbeat");
     ArrayList<Note> toPlay = b.earlynotes[i];
     for(int x = 0; x < toPlay.size(); x++){
       compBus.sendNoteOn(toPlay.get(x));
     }
     delay(fudgetime);
     toPlay = b.notes[i];
     boolean sclear = true;
     boolean bclear = true;
     for(int x = 0; x < toPlay.size(); x++){
       myBus.sendNoteOn(toPlay.get(x));
       
       //Check for percussion notes
       if(toPlay.get(x).channel == pchannel1 && toPlay.get(x).pitch == 36){
         display("Snare drum playing", snareLine + 2);
         sclear = false;
       }
       if(toPlay.get(x).channel == pchannel2 && toPlay.get(x).pitch == 38){
         display("Bass drum playing", bassLine + 2);
         bclear = false;
       }
     }
     if(sclear){
       display("", snareLine + 2);
     }
     if(bclear){
       display("", bassLine + 2);
     }
     
     delay(noteLen/nsubbeats-fudgetime);
 }
 
 void printSubbeat(Beat b, int i){
     if(i >= b.notetext.length) return;
     if(i < 0) return;
     
     qprint("Subbeat");
     //Do a tonic check again (when you actually play stuff)
     if (i == 0 && b.forcedTonic) {
      tonicCount++;
      display("Tonic Count: " + tonicCount, generalLine+1);
     }
     
     ArrayList<String> toPrint = b.notetext[i];
     for(int x = 0; x < toPrint.size(); x++){
       addText(" " + toPrint.get(x), melodyLine + 1);
     }
 }

//chooses a melody note from the current chord tones
int randMelodyNote(int[] options) {
  int randNum = (int)(Math.random() * 4);

  return options[randNum];
}

int randMelodyNote2(float[] options) {
  double rand = Math.random();
  for (int x = 0; x < options.length; x++) {
    rand -= options[x];
    if (rand < 0) return degreeToNote[(x+7) % 7];
  }
  System.out.println("Total probabilities in the non-chord tone vector is less than 1?");
  return -1;
}

//processes delay in milliseconds
void delay(int time) {
  int current = millis();
  while (millis () < current+time) Thread.yield();
}

//Initializes the display
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
  display(temp, bassLine + 1);
  display("Bass Drum", bassLine);
  
  //If there's an offset, display a header
  if(offset == 2){
     display(header, 0); 
  }
}

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

//For utility/debugging
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

//Gets greatest common factor (GCF) of two ints 
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
  int[] temp = new int[D.length];
  for (int x = 0; x < D.length; x++) {
    temp[x] = beatToNBeat(D[x]);
  }
  return temp;
}