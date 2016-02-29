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

int x = 0;

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
  Note note = new Note(channel, degreeToNote[x%degreeToNote.length], velocity, ticks); 
  myBus.sendNoteOn(note); 
  
  x++;
  delay(noteLen); 
}

//processes delay in milliseconds
void delay(int time) {
  int current = millis();
  while (millis () < current+time) Thread.yield();
}