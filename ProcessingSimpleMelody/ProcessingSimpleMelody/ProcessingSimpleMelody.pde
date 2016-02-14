import themidibus.*; //Import midi library
import java.lang.Math; //To get random numbers

MidiBus myBus; //Creates a MidiBus object
MidiBus chordBus;
int previous = 0;
int noteLen = 1000; //set chord length in milliseconds
int tonic = 60; //set key to C major
int next = 0; //keeps track of next chord. Always start with tonic
int[] divisions = {1,2,4}; //Possible number of melody nodes per chord(quarter, 2 eights, 4 sixteenths)
int tonicCount = 0; //How many times a tonic chord has been played with a quarter note melody
int tonicTotal = 3; //Music stops when we reach this number of tonic chord/quarter note melodies

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

//sets up screen
void setup() {
  size(200,200);
  background(0);

  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
   
  myBus = new MidiBus(this, 0, 1); //Sends midi output to speakers
  chordBus = new MidiBus(this, 0, 1);
  
  /*int status_byte = 0xC0;
  // This is the status byte for a program change
  int channel = 2;
  // We'll use channel 0
  int byte1 = 64;
  // This will be the preset you are sending with your program change
  int byte2 = 0;
  // This is not used for program change so ignore it and set it to 0

  myBus.sendMessage(status_byte, channel, byte1, byte2); */
 
}

//this function repeats indefinitely
//note that the output displayed in the window is one chord behind what is being played
void draw() {
  
  //If we haven't reached our tonic total, continue melody
  if(tonicCount < tonicTotal) {
    background(0); //clear screen
    next = chooseChord(next);
    text("Tonic Count: " + tonicCount, 20, 80); //prints to screen
  }
}

int chooseChord(int currChord){
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
      
      playChord(base, third, fifth, oct);
      
      break;
    }
  }
  
  //returns index in matrix to the draw function to find next chord
  return i;
}

//plays the chord, and melody notes an octave higher
void playChord(int base, int third, int fifth, int oct) {
  int channel = 0; //set channel. 0 for speakers
  int velocity = 80; //chord volume
  int melVelocity = 120; //melody note volumn
  int ticks = noteLen; //length in milliseconds
  
  
  //Create the midi notes
  Note note1 = new Note(channel, base, velocity, ticks);
  Note note2 = new Note(channel, third, velocity, ticks);
  Note note3 = new Note(channel, fifth, velocity, ticks);
  Note note4 = new Note(channel, oct, velocity, ticks);
  
  int[] notes= {base, third, fifth, oct};
  text("Chord notes: " + base + " " + third + " " + fifth, 20, 20); //prints to screen
  
  int randNum = (int)(Math.random() * divisions.length);
  
  //check if tonic chord and quarter note melody combination
  if(randNum == 0 && base == tonic) {
    tonicCount++;
  }
  
  int subBeat = noteLen / divisions[randNum]; //define length of melody note
  text("subBeat length: " + subBeat, 20, 40); //prints to screen
  for(int i = 0; i < divisions[randNum]; i++){
    
    //play chord on downbeat
    if(i == 0) {
      chordBus.sendNoteOn(note1);
      chordBus.sendNoteOn(note2);
      chordBus.sendNoteOn(note3);
      chordBus.sendNoteOn(note4);
    }
    
    //play melody note on determined subbeat
  //  Note melody = new Note(1, randMelodyNote(notes) + 12, melVelocity, subBeat);
    //myBus.sendNoteOn(melody);
    
    //myBus.sendMessage(0x8c, 0, previous, 0);
    //previous = randMelodyNote(notes);
    myBus.sendMessage(0x9c, 0, randMelodyNote(notes), melVelocity);
  
    delay(subBeat); //waits for duration of subbeat before playing next note
  }
}

//chooses a melody note from the current chord tones
int randMelodyNote(int[] options) {
  int randNum = (int)(Math.random() * 4);
  
  return options[randNum];
}

//processes delay
void delay(int time) {
  int current = millis();
  while (millis () < current+time) Thread.yield();
}
   
   