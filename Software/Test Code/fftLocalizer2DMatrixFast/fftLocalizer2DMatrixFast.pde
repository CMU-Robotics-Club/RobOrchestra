import processing.sound.*; //Input from computer mic
import themidibus.*; //MIDI output to instruments/SimpleSynth
import java.util.ArrayList;
import java.text.*;
import javax.sound.midi.*; //For reading MIDI file
import Jama.*; //Matrix math

String fileName = "WWRY.mid";
public static final int NOTE_ON = 0x90;
public static final int NOTE_OFF = 0x80;

AudioIn in; //Raw sound input
PitchDetector pd; //Get pitches from input. Doesn't currently do anything, but we might use this eventually to grab pitch info from a human
Amplitude amp; //Get amplitudes from input
MidiBus myBus; //Pass MIDI to instruments/SimpleSynth

double beatThresh = 0.5; //Amplitude threshold to be considered a beat; TODO tune (also adjust down SimpleSynth volume if necessary)

int bucketsPerMeasure = 64; //Pick something reasonably large (but not so large that it makes computations slow)
int nTempoBuckets = 64; //Same idea
int bucketsPerRhythm;

//Upper and lower bounds on tempo. TODO: These probably change based on length of "measure" (AKA rhythm sequence)
int minMsPerMeasure = 500;
int maxMsPerMeasure = 8000;

int minBPM = 30;
int maxBPM = 200;

//Gaussian parameters. Hopefully don't need changing anymore
double beatprobamp = 4; //How confident we are that when we hear a beat, it corresponds to an actual beat. (As opposed to beatSD, which is how unsure we are that the beat is at the correct time.) 
double beatSD; //SD on Gaussians for sensor model (when we heard a beat) in # time buckets
double posSD; //SD on Gaussians for motion model (time since last measurement) in # time buckets
double tempoSD = nTempoBuckets/32.0;//1; //SD on tempo changes (# tempo buckets) - higher means we think weird stuff is more likely due to a tempo change than bad execution of same tempo

//These get filled in later
ArrayList<ArrayList<Integer>> notes; //Gets populated when we read the MIDI file
Matrix probs;
Matrix probsonemat;
Matrix probs2;
Matrix beatProbs; //P(location | heard a beat)
Matrix tempoGaussMat = new Matrix(nTempoBuckets, nTempoBuckets);
Matrix msPerBucket = new Matrix(nTempoBuckets, 1);


int oldtime = millis(); //Time between code start and last beat check/update. Processing has 64 bit integers, so we probably don't overflow - max is about 2 billion milliseconds, so about 500 hours
ArrayList<Integer> pitch = new ArrayList<Integer>(); //All notes currently playing

//Where we think we are in the song
int measure = 0; //Again, this is actually counting instances of the rhythm pattern, which may not line up with actual measures as written
int bucket = 0;

void setup()
{
  size(1000, 800);
  background(255);
  
  // Create an Input stream which is routed into the Amplitude analyzer
  pd = new PitchDetector(this, 0.55); //Last arg is confidence - increase to filter out more garbage
  in = new AudioIn(this, 0);
  amp = new Amplitude(this);
  
  myBus = new MidiBus(this, 0, 2);
  MidiBus.list();
  in.amp(1);
  // start the Audio Input
  in.start();
  
  // patch the AudioIn
  pd.input(in);
  amp.input(in);
  background(255);
  //System.out.println(notes);
  

  NoteArray nArr = new NoteArray(fileName, bucketsPerMeasure);
  notes = nArr.notes.get(0);
  ArrayList<ArrayList<Integer>> rhythmPattern = nArr.pattern;
  bucketsPerRhythm = rhythmPattern.size();
  probs = new Matrix(bucketsPerRhythm, 1);
  probsonemat = new Matrix(nTempoBuckets, 1, 1);
  probs2 = new Matrix(bucketsPerRhythm, nTempoBuckets);
  beatProbs = new Matrix(bucketsPerRhythm, 1); //P(location | heard a beat)
  
  beatSD = bucketsPerRhythm/320.0;
  posSD = bucketsPerRhythm/64.0;
  System.out.println();
  maxMsPerMeasure = 60000 / minBPM * nArr.beatspermeasure;
  System.out.println(maxMsPerMeasure); // beat/mes * ms/beat
  minMsPerMeasure = 60000 / maxBPM * nArr.beatspermeasure;
  System.out.println(minMsPerMeasure);
  int dMsPerMeasure = (maxMsPerMeasure - minMsPerMeasure)/(nTempoBuckets-1);
  for(int i = 0; i < nTempoBuckets; i++){
    msPerBucket.set(i, 0, (minMsPerMeasure + dMsPerMeasure*i)/bucketsPerMeasure);
    assert(msPerBucket.get(i, 0) > 0);
  }
 
 for(int i = 0; i < bucketsPerRhythm; i++){
   probs.set(i, 0, 1.0/bucketsPerRhythm);
   for(int j = 0; j < nTempoBuckets; j++){
     probs2.set(i, j, 1.0/bucketsPerRhythm/nTempoBuckets);
   }
   beatProbs.set(i, 0, 0.01); //We'll normalize this later
 }
 
 //TODO read this from track 1 rather than hardcoding
 //That means replacing this chunk of code with something that gets the rhythmPattern as an ArrayList<ArrayList<Integer>> using Ryan's code
// int[] beatpositions = {bucketsPerMeasure*0/8, bucketsPerMeasure*1/8, bucketsPerMeasure*2/8, bucketsPerMeasure*4/8, bucketsPerMeasure*5/8, bucketsPerMeasure*6/8}; 
 int[] oldbeatpositions = {bucketsPerMeasure*0/4, bucketsPerMeasure*1/4, bucketsPerMeasure*2/4}; 
 
 //ArrayList<ArrayList<Integer>> rhythmPattern = new ArrayList<ArrayList<Integer>>();


 
 //for(int i = 0; i < bucketsPerMeasure; i++){
 //  rhythmPattern.add(new ArrayList<Integer>());
 //}
 //for(int i: oldbeatpositions){
 //  rhythmPattern.get(i).add(42); //Some non-zero number
 //}
 
 //End get rhythmPattern
 
 ArrayList<Integer> beatpositions = new ArrayList<Integer>();
 for(int i = 0; i < bucketsPerRhythm; i++){
   if(rhythmPattern.get(i).size() > 0 && rhythmPattern.get(i).get(0) > 0){
     beatpositions.add(i);
   }
 }
 
 for(int i:beatpositions){
   for(int j = 0; j < bucketsPerRhythm; j++){
     int disp = min(abs( (i-j)%bucketsPerRhythm), abs( (j-i)%bucketsPerRhythm));
     //disp = #buckets off from i that we are
     beatProbs.set(j, 0, beatProbs.get(j, 0) + beatprobamp * GaussPDF(disp, 0, beatSD));
   }
 }
 //Normalize beatProbs
 double beatProbSum = 0;
 for(int i = 0; i < bucketsPerRhythm; i++){
   beatProbSum += beatProbs.get(i, 0);
 }
 for(int i = 0; i < bucketsPerRhythm; i++){
   beatProbs.set(i, 0, beatProbs.get(i, 0) / beatProbSum);
 }
 
 //Set up tempoGaussMat
  for(int k = 0; k < nTempoBuckets; k++){
   for(int l = 0; l < nTempoBuckets; l++){
     //Overall plan is newprobs2[i][k] = adhocPosGaussMat[i][j] * probs2[j][l] * tempoGaussMat[l][k], summed over j and l, and then this is just matrix multiplication
     //But note that tempoGaussMat is symmetric so this won't end up mattering
     tempoGaussMat.set(l, k, GaussPDF(k-l, 0, tempoSD));
   }
  }
}      

void draw()
{
  int newtime = millis();
  int t = newtime - oldtime;
  //println(t);
  oldtime = newtime;
  
  boolean isBeat = (amp.analyze() > beatThresh) || keyPressed;
  
  //Compute new probs
  Matrix newprobs2 = new Matrix(bucketsPerRhythm, nTempoBuckets);
  double newprobsum = 0;
  

  //Get new position probabilities, based on time since last read and whether we heard a beat
  //Going to bucket i from bucket j in time t 
  Matrix prenewprobs2 = new Matrix(bucketsPerRhythm, nTempoBuckets);
  
  for(int i = 0; i < bucketsPerRhythm; i++){ //New pos
    for(int l = 0; l < nTempoBuckets; l++){ //Old tempo (okay, this gets weird because we're updating position with the old tempo now. Should be close though)
      float tbuckets = (float)t / (float)msPerBucket.get(l, 0); //tbuckets is time in buckets and likely small
      
      float tempil = 0;
      
      for(int j = 0; j < bucketsPerRhythm; j++){ //Old pos
        float[] stuffToTry = {abs( (float) ((i-(j+tbuckets)+bucketsPerRhythm)%bucketsPerRhythm)), abs( (float)(((j+tbuckets)-i+bucketsPerRhythm)%bucketsPerRhythm)), abs( (float)((i-(j+tbuckets)-bucketsPerRhythm)%bucketsPerRhythm)), abs( (float)(((j+tbuckets)-i-bucketsPerRhythm)%bucketsPerRhythm))};
         float disp = min(stuffToTry); //nBuckets you're off in the time direction
         double tempoPDF = GaussPDF(disp, 0, posSD);
         tempil += probs2.get(j, l)*tempoPDF;
      }
      if(isBeat){
        tempil *= beatProbs.get(i, 0);
      }
      else{
        tempil *= (1-beatProbs.get(i, 0));
      }
      prenewprobs2.set(i, l, tempil);
    }
  }
  newprobs2 = prenewprobs2.times(tempoGaussMat);
  newprobsum = new Matrix(1, bucketsPerRhythm, 1).times(newprobs2).times(new Matrix(nTempoBuckets, 1, 1)).get(0, 0);
        
  //Normalize and get most likely
  double newprobmax = -1;
  int newprobmaxind = -1;
  
  //We want to add across the rows of newprobs2 and dump that into probs. Can do that with matrix multiplication.
  newprobs2 = newprobs2.times(1/newprobsum);
  probs = newprobs2.times(probsonemat);
  
  for(int i = 0; i < bucketsPerRhythm; i++){
    if(probs.get(i, 0) > newprobmax){
      newprobmax = probs.get(i, 0);
      newprobmaxind = i;
    }
  }

  probs2 = newprobs2;
  dispProbArray(probs, isBeat);
  
  if(newprobmaxind > -1) { //Throw out cases where we're super non-confident about where we are. Negative to always assume the best guess is correct
    ArrayList<Integer> newpitch = getNote(measure, newprobmaxind);
    if(newpitch.size() > 0 && newpitch.get(0) > 0){ //So we stop each note when the next note starts
      for(Integer ppitch: pitch){
        myBus.sendNoteOff(new Note(0, ppitch.intValue(), 25));
      }
      //Start new note
      pitch = newpitch; //Which we know is non-zero because of outer if statement
      for(Integer ppitch: pitch){
        myBus.sendNoteOn(new Note(0, ppitch.intValue(), 25));
      }
    }
  }
  else{
    System.out.println("Help I'm lost");
    //exit();
  }
  
  if(newprobmaxind + bucketsPerRhythm/2 <= bucket){ //If we've backed up by more than half a measure, that probably means we skipped across to the next measure
    measure++;
  }
  bucket = newprobmaxind;
  
  //If things get weird, consider adding a small delay here. Seems fine for now though.
  //delay(25);
}

int MIDIfromPitch(double freq){
  if(freq <= 10){
    return 0;
  }
  
  double logfreq = Math.log(freq);
  double log12thrt2 = Math.log(Math.pow(2, 1.0/12));
  int freqA = 440;
  double logfreqA = Math.log(freqA);
  int midiA = 69;
  
  //Factors of 12thrt2 turn into multiples of log12thrt2 in log space
  //logfreq of 0 corresponds to freq of 1 (e^0 = 1)
  int midi = (int) Math.round(logfreq/log12thrt2 - logfreqA/log12thrt2 + midiA);
  
  //assert(midi == MIDIfromPitch(freq));
  return midi;
}

double pitchFromMIDI(int midi){
  if(midi <= 0){
    return 0;
  }
  
  // midi = logfreq/log12thrt2 - logfreqA/log12thrt2 + midiA
  //logfreq = (midi - midiA + logfreqA/log12thrt2)*log12thrt2
  
  double log12thrt2 = Math.log(Math.pow(2, 1.0/12));
  int freqA = 440;
  double logfreqA = Math.log(freqA);
  int midiA = 69;
  
  double logfreq = (midi - midiA + logfreqA/log12thrt2)*log12thrt2;
  double freq = Math.exp(logfreq);
  
  return freq;
}


void dispProbArray(Matrix A, boolean isBeat){
  background(255);
  
  int n = A.getRowDimension();
  for(int i = 0; i < n; i++){
    fill(0);
    if(isBeat){
      fill(200, 100, 0);
    }
    rect(i*width/n, (1- (float)A.get(i, 0))*height, width/n, (float) A.get(i, 0)*height);
  }
}

double GaussPDF(double x, double mu, double sigma){
  float pi = 3.1415926; //But no one cares since it just shows up as a constant normalization factor anyway
  //mu = mean, sigma = st. dev.
  return 1.0/(sigma*sqrt(pi*2))*exp( (float) (-0.5*((x-mu)/sigma)*((x-mu)/sigma)));
}

ArrayList<Integer> getNote(int measure, int bucket){
  int ind = (measure * bucketsPerRhythm + bucket)%notes.size();
  return notes.get(ind);
}
