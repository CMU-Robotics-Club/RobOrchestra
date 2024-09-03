import processing.sound.*;
import themidibus.*;;
import java.util.ArrayList;

import java.io.File;
import java.lang.*;
import java.util.Arrays;
import java.io.FileInputStream;

import javax.sound.midi.MetaMessage;
import javax.sound.midi.MidiEvent;
import javax.sound.midi.MidiMessage;
import javax.sound.midi.MidiSystem;
import javax.sound.midi.Sequence;
import javax.sound.midi.ShortMessage;
import javax.sound.midi.Track;
import javax.sound.midi.InvalidMidiDataException;

import Jama.*;

public static final int NOTE_ON = 0x90;
public static final int NOTE_OFF = 0x80;
public static final String[] NOTE_NAMES = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};

FFT fft; //Not used, we're using PitchDetector apparently
AudioIn in;
PitchDetector pd;
MidiBus myBus;
Amplitude amp;
int bands = 64;
float bpm = 188;
float x = 0;
float y = 0;
float yOld = 0;
float ampOld = 0;
int midi;
ArrayList<ArrayList<Integer>> notes;
int maxLength = 10;
float ampScale = 800;

float ampThreshold = 0.01;
//float[] spectrum = new float[bands];

Note oldNote = null;

SinOsc osc;
Sound s;

int measure = 0;
int bucket = 0;

int bucketsPerMeasure = 16; //Going to assume we're starting with We Will Rock You and listening for rhythm; have to adjust this (and probably everything) if we try to do something more general
int nTempoBuckets = 16;
Matrix probs = new Matrix(bucketsPerMeasure, 1);
Matrix probsonemat = new Matrix(nTempoBuckets, 1, 1);
Matrix probs2 = new Matrix(bucketsPerMeasure, nTempoBuckets);
Matrix beatProbs = new Matrix(bucketsPerMeasure, 1); //P(location | heard a beat)
Matrix playMe = new Matrix(bucketsPerMeasure, 1);

int minMsPerMeasure = 500;
int maxMsPerMeasure = 4000;
Matrix msPerBucket = new Matrix(nTempoBuckets, 1);

//int msPerMeasure = 1600; //Probably about 2000??
//int msPerBucket = msPerMeasure/bucketsPerMeasure;
double beatThresh = 0.1; //Amplitude threshold to be considered a beat; TODO tune (also adjust down SimpleSynth volume if necessary)

int oldtime = millis(); //Processing has 64 bit integers, so we probably don't overflow - max is about 2 billion milliseconds, so about 500 hours
ArrayList<Integer> pitch = new ArrayList<Integer>();

double beatprobamp = 4; //How confident we are that when we hear a beat, it corresponds to an actual beat. (As opposed to beatSD, which is how unsure we are that the beat is at the correct time.) 

double beatSD = 0.1; //SD on Gaussians for sensor model (when we heard a beat) in # time buckets
double tempoSD = 1; //SD on Gaussians for motion model (time since last measurement) in # time buckets
double dtempoSD = 2; //SD on tempo changes (# tempo buckets) - higher means we think weird stuff is more likely due to a tempo change than bad execution of same tempo

double mspertick;
int starttime; //For debug only TODO delete
void setup()
{
  starttime = millis();
  size(1000, 800);
  background(255);
  
  // Create an Input stream which is routed into the Amplitude analyzer
  //fft = new FFT(this, bands);
  pd = new PitchDetector(this, 0.55); //Last arg is confidence - increase to filter out more garbage
  in = new AudioIn(this, 0);
  amp = new Amplitude(this);

  /*osc = new SinOsc(this);
  osc.freq(440);
  osc.play();*/
  
  myBus = new MidiBus(this, 0, 2);
  MidiBus.list();
  in.amp(1);
  // start the Audio Input
  in.start();
  
  // patch the AudioIn
  //fft.input(in);
  pd.input(in);
  amp.input(in);
  background(255);
  System.out.println("amp threshold is " + ampThreshold);
  notes = new ArrayList<ArrayList<Integer>>();
  noteArray();
  
  
  int dMsPerMeasure = (maxMsPerMeasure - minMsPerMeasure)/(nTempoBuckets-1);
  for(int i = 0; i < nTempoBuckets; i++){
    msPerBucket.set(i, 0, (minMsPerMeasure + dMsPerMeasure*i)/bucketsPerMeasure);
    assert(msPerBucket.get(i, 0) > 0);
  }
 
 for(int i = 0; i < bucketsPerMeasure; i++){
   probs.set(i, 0, 1.0/bucketsPerMeasure);
   for(int j = 0; j < nTempoBuckets; j++){
     probs2.set(i, j, 1.0/bucketsPerMeasure/nTempoBuckets);
     //println(probs2[i][j]);
   }
   beatProbs.set(i, 0, 0.01); //We'll normalize this later
 }
 
 //TODO read this from track 1 rather than hardcoding
// int[] beatpositions = {bucketsPerMeasure*0/8, bucketsPerMeasure*1/8, bucketsPerMeasure*2/8, bucketsPerMeasure*4/8, bucketsPerMeasure*5/8, bucketsPerMeasure*6/8}; 
 int[] beatpositions = {bucketsPerMeasure*0/4, bucketsPerMeasure*1/4, bucketsPerMeasure*2/4}; 
 
 for(int i:beatpositions){
   for(int j = 0; j < bucketsPerMeasure; j++){
     int disp = min(abs( (i-j)%bucketsPerMeasure), abs( (j-i)%bucketsPerMeasure));
     //Disp = #buckets off from i that we are
     beatProbs.set(j, 0, beatProbs.get(j, 0) + beatprobamp * GaussPDF(disp, 0, beatSD));
   }
   /*beatProbs[i] = 10;
   //Add some probability for being adjacent to a beat when we hear something
   beatProbs[(i+1+bucketsPerMeasure)%bucketsPerMeasure] = 5;
   beatProbs[(i-1+bucketsPerMeasure)%bucketsPerMeasure] = 5;*/
 }
 //Normalize beatProbs
 double beatProbSum = 0;
 for(int i = 0; i < bucketsPerMeasure; i++){
   beatProbSum += beatProbs.get(i, 0);
 }
 for(int i = 0; i < bucketsPerMeasure; i++){
   beatProbs.set(i, 0, beatProbs.get(i, 0) / beatProbSum);
   //System.out.println(i);
   //System.out.println(beatProbs[i]);
 }
 
}      

void draw()
{
  int newtime = millis();
  int t = newtime - oldtime;
  oldtime = newtime;
  
  boolean isBeat = amp.analyze() > beatThresh;
  
  //Compute new probs
  Matrix newprobs2 = new Matrix(bucketsPerMeasure, nTempoBuckets);
  double newprobsum = 0;
  
  //Zeroing entries should get handled by the constructor
  /*for(int i = 0; i < bucketsPerMeasure; i++){
    for(int j = 0; j < nTempoBuckets; j++){
      newprobs2.set(i, j, 0);
    }
  }*/

  //Going to bucket i from bucket j in time t (t is in buckets and likely small)
  //TODO vectorize this somehow
  for(int i = 0; i < bucketsPerMeasure; i++){
    for(int k = 0; k < nTempoBuckets; k++){
      for(int j = 0; j < bucketsPerMeasure; j++){
         for(int l = 0; l < nTempoBuckets; l++){
           
             //Ugly brute-force mod stuff because wraparound is annoying!
           float tbuckets = (float)t / (float)msPerBucket.get(k, 0);
           float[] stuffToTry = {abs( (float) ((i-(j+tbuckets)+bucketsPerMeasure)%bucketsPerMeasure)), abs( (float)(((j+tbuckets)-i+bucketsPerMeasure)%bucketsPerMeasure)), abs( (float)((i-(j+tbuckets)-bucketsPerMeasure)%bucketsPerMeasure)), abs( (float)(((j+tbuckets)-i-bucketsPerMeasure)%bucketsPerMeasure))};
           float disp = min(stuffToTry); //nBuckets you're off in the time direction
           
           //No need for fancy mod stuff with tempo; tempo doesn't wrap around!
           newprobs2.set(i, k, newprobs2.get(i, k) + probs2.get(j, l)*GaussPDF(disp, 0, tempoSD)*GaussPDF(k-l, 0, dtempoSD));
           
         }//end l
       }//end j
     //Disp = #buckets off from i that we are
      //newprobs[i] += probs[j]*GaussPDF(disp, 0, tempoSD);
      
      if(isBeat){
        newprobs2.set(i, k, newprobs2.get(i, k) * beatProbs.get(i, 0));
      }
      else{
        newprobs2.set(i, k, newprobs2.get(i, k) * (1-beatProbs.get(i, 0)));
      }
       newprobsum += newprobs2.get(i, k);
   } //end k
   
    
  } //end i
  
  //Normalize and get most likely
  double newprobmax = -1;
  int newprobmaxind = -1;
  
  //We want to add across the rows of newprobs2 and dump that into probs. Can do that with matrix multiplication.
  newprobs2 = newprobs2.times(1/newprobsum);
  probs = newprobs2.times(probsonemat);
  
  //for(int i = 0; i < bucketsPerMeasure; i++){
  //  //Normalize, then drop stuff back into probs
  //  probs.set(i, 0, 0);
  //  for(int k = 0; k < nTempoBuckets; k++){
  //    newprobs2.set(i, k, newprobs2.get(i, k)/newprobsum);
  //    probs.set(i, 0, probs.get(i, 0) + newprobs2.get(i, k));
  //  }
    
  //  if(probs.get(i, 0) > newprobmax){
  //    newprobmax = probs.get(i, 0);
  //    newprobmaxind = i;
  //  }
  //}
  
  for(int i = 0; i < bucketsPerMeasure; i++){
    if(probs.get(i, 0) > newprobmax){
      newprobmax = probs.get(i, 0);
      newprobmaxind = i;
    }
  }

  probs2 = newprobs2;
  dispProbArray(probs, isBeat);
  
  if(newprobmaxind > -1){ //Throw out cases where we're super non-confident about where we are. Negative to always assume the best guess is correct
    ArrayList<Integer> newpitch = getNote(measure, newprobmaxind); //playMe[newprobmaxind];
    if(newpitch.size() > 0){ //So we stop each note when the next note starts
      for(Integer ppitch: pitch){
        myBus.sendNoteOff(new Note(0, ppitch.intValue(), 100));
      }
      //Start new note
      pitch = newpitch; //Which we know is non-zero because of outer if statement
      for(Integer ppitch: pitch){
        myBus.sendNoteOn(new Note(0, ppitch.intValue(), 100));
      }
    }
  }
  else{
    newprobs2.times(1e10).print(1,1); //0 everywhere
    System.out.println("Help I'm lost");
    println(newtime - starttime); //Somewhere between 7000 and 12000 before things break, seemingly regardless of whether I tap a beat or not
    exit();
  }
  
  //No need to explicitly delay - code is slow enough already
  //delay(12); //Hardcoded to whatever worked in the continuous 1D version
  
  if(newprobmaxind + bucketsPerMeasure/2 <= bucket){ //If we've backed up by more than half a measure, that probably means we skipped across to the next measure
    measure++;
  }
  bucket = newprobmaxind;
  
  
  delay(100);
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
    //stroke(255, 0, 0);
    //line((float) (i*width/n), (float) (height), (float) ((i+1)*width/n - 1), (float) (height-A.get(i, 0)*height));
    fill(0);
    if(isBeat){
      fill(200, 100, 0);
    }
    rect(i*width/n, (1- (float)A.get(i, 0))*height, width/n, (float) A.get(i, 0)*height); //Works
    //rect((float) (i*width/n), (float) (height), (float) width/n, (float) A.get(i, 0)*height);
  }
}

double GaussPDF(double x, double mu, double sigma){
  float pi = 3.1415926; //But no one cares since it just shows up as a constant normalization factor anyway
  //mu = mean, sigma = st. dev.
  return 1.0/(sigma*sqrt(pi*2))*exp( (float) (-0.5*((x-mu)/sigma)*((x-mu)/sigma)));
}

//This function and getNote are just going to keep using ArrayLists, but should be self-contained so it should be fine
void noteArray()
{
try
  {
    File myFile = new File(dataPath("WWRY2.mid"));
    Sequence sequence = MidiSystem.getSequence(myFile);
    Track[] tracks = sequence.getTracks();
    mspertick = (1.0*sequence.getMicrosecondLength()/sequence.getTickLength()/1000);
    int metaidx = 0;
    int beatspermeasure = 4;
    double msperbeat = 500;
    
    //Grab all the MetaMessage stuff from the start of the first track to get tempo and time signature information
    //Assumes tempo and time signature won't change later, should be fine if we stick to simple songs for now
    while (tracks[0].get(metaidx).getMessage() instanceof MetaMessage)
    {
      MetaMessage mm = (MetaMessage) tracks[0].get(metaidx).getMessage();
      byte[] b = mm.getMessage();
      if (b[1] == 0x51)
      {
        if (b[2] != 3)
        {
          System.out.println("Bad meta message");
          assert(false);
        }
        msperbeat = (b[3] << 16 | b[4] << 8 | b[5]) / 1000.0;
      }
      else if (b[1] == 0x58)
      {
        if (b[2] < 4)
        {
          System.out.println("Bad meta message");
          assert(false);
        }
        beatspermeasure = b[3];
      }
      metaidx++;
    }
          
    for (int i = 0; i < 1; i++) // go through tracks, limited to track 0 for now
    {
      //System.out.println("Track " + i);
      for (int j = 0; j < tracks[i].size(); j++)
      {
        MidiEvent event = tracks[i].get(j);
        MidiMessage message = event.getMessage(); // get message
        if (message instanceof ShortMessage)
        {
          ShortMessage sm = (ShortMessage) message;
          if (sm.getCommand() == NOTE_ON) // note on
          {
            if (sm.getData2() > 0)
            {
              // if ShortMessage that actually sends a note, 
              int key = sm.getData1();
              long tick = event.getTick();
              //System.out.println("note " + j + " is " + key + " at timestamp " + newTick);
              double pos = ((tick * mspertick) / msperbeat) + 10e-5; //Number of beats into the piece (plus a little so it doesn't truncate to one beat early but this shouldn't matter now that we're just returning the bucket number)
              //System.out.format("current position %f\n", pos);
              //System.out.format("milliseconds per beat %f\n", msperbeat);
              int measure = (int) (pos / beatspermeasure);
              double beat = pos % beatspermeasure;
              int bucket = (int) Math.round((pos * bucketsPerMeasure) / beatspermeasure);
              //System.out.println(buckets + "th bucket"); 
              
              while (notes.size() <= bucket)
              {
                notes.add(new ArrayList<Integer>());
                //System.out.println("Add");
              }
              notes.get(bucket).add(key);

              //System.out.format("At measure %d with beat %f; bucket %d\n", measure, beat, bucket);
            }
          }
        }
      }
    }
    while (notes.size() % bucketsPerMeasure != 0)
    {
      notes.add(new ArrayList<Integer>());
    }
    System.out.println(notes);
    System.out.println("post pad buckets: " + notes.size());
  }
  catch (InvalidMidiDataException e)
  {
    System.out.println("Bad file input");
    exit();
  }
  catch (IOException e)
  {
    println("Bad file input");
    exit();
  }
}
ArrayList<Integer> getNote(int measure, int bucket){
  int ind = (measure * bucketsPerMeasure + bucket)%notes.size();
  return notes.get(ind);
}
