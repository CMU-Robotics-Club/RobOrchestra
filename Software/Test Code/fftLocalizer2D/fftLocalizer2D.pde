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
ArrayList<Integer> notes;
int maxLength = 10;
float ampScale = 800;

float ampThreshold = 0.01;
//float[] spectrum = new float[bands];

Note oldNote = null;

SinOsc osc;
Sound s;

int measure = 0;
int bucket = 0;

int bucketsPerMeasure = 32; //Going to assume we're starting with We Will Rock You and listening for rhythm; have to adjust this (and probably everything) if we try to do something more general
int nTempoBuckets = 32;
double[] probs = new double[bucketsPerMeasure];
double[][] probs2 = new double[bucketsPerMeasure][nTempoBuckets];
double[] beatProbs = new double[bucketsPerMeasure]; //P(location | heard a beat)
int[] playMe = new int[bucketsPerMeasure];

int minMsPerMeasure = 800;
int maxMsPerMeasure = 6400;
int[] msPerBucket = new int[nTempoBuckets];

//int msPerMeasure = 1600; //Probably about 2000??
//int msPerBucket = msPerMeasure/bucketsPerMeasure;
double beatThresh = 0.1; //Amplitude threshold to be considered a beat; TODO tune (also adjust down SimpleSynth volume if necessary)

int oldtime = millis(); //Processing has 64 bit integers, so we probably don't overflow - max is about 2 billion milliseconds, so about 500 hours
int pitch = 0;

double beatprobamp = 4; //How confident we are that when we hear a beat, it corresponds to an actual beat. (As opposed to beatSD, which is how unsure we are that the beat is at the correct time.) 

double beatSD = 0.3; //SD on Gaussians for where we heard a beat (in #buckets)
double tempoSD = 0.3; //SD on Gaussians around moving through time (in #buckets)
double dtempoSD = 1;

double mspertick;




void setup()
{
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
  notes = new ArrayList<Integer>();
  noteArray();
  
  
  int minMsPerMeasure = 800;
  int maxMsPerMeasure = 3200;
  int dMsPerMeasure = (maxMsPerMeasure - minMsPerMeasure)/(nTempoBuckets-1);
  for(int i = 0; i < nTempoBuckets; i++){
    msPerBucket[i] = (minMsPerMeasure + dMsPerMeasure*i)/bucketsPerMeasure;
    assert(msPerBucket[i] > 0);
  }
 
 for(int i = 0; i < bucketsPerMeasure; i++){
   probs[i] = 1.0/bucketsPerMeasure;
   for(int j = 0; j < nTempoBuckets; j++){
     probs2[i][j] = 1.0/bucketsPerMeasure/nTempoBuckets;
     //println(probs2[i][j]);
   }
   playMe[i] = 0;
   beatProbs[i] = 0.01; //We'll normalize this later
 }
 
 //Tell it to play arpeggios
 playMe[0] = 60;
 playMe[bucketsPerMeasure/4] = 64;
 playMe[bucketsPerMeasure/2] = 67;
 playMe[bucketsPerMeasure*3/4] = 72;
 
 for(int i = 0; i < bucketsPerMeasure*3/4; i+=bucketsPerMeasure/4){
   for(int j = 0; j < bucketsPerMeasure; j++){
     int disp = min(abs( (i-j)%bucketsPerMeasure), abs( (j-i)%bucketsPerMeasure));
     //Disp = #buckets off from i that we are
     beatProbs[j] += beatprobamp * GaussPDF(disp, 0, beatSD);
   }
   /*beatProbs[i] = 10;
   //Add some probability for being adjacent to a beat when we hear something
   beatProbs[(i+1+bucketsPerMeasure)%bucketsPerMeasure] = 5;
   beatProbs[(i-1+bucketsPerMeasure)%bucketsPerMeasure] = 5;*/
 }
 //Normalize beatProbs
 double beatProbSum = 0;
 for(int i = 0; i < bucketsPerMeasure; i++){
   beatProbSum += beatProbs[i];
 }
 for(int i = 0; i < bucketsPerMeasure; i++){
   beatProbs[i] /= beatProbSum;
   //System.out.println(i);
   //System.out.println(beatProbs[i]);
 }
 //beatProbs should be normalized now
}      

void draw()
{
  int newtime = millis();
  int t = newtime - oldtime;
  oldtime = newtime;
  
  boolean isBeat = amp.analyze() > beatThresh;
  
  //Compute new probs
  double[][] newprobs2 = new double[bucketsPerMeasure][nTempoBuckets];
  double newprobsum = 0;
  
  for(int i = 0; i < bucketsPerMeasure; i++){
    for(int j = 0; j < nTempoBuckets; j++){
      newprobs2[i][j] = 0;
    }
  }

  //Going to bucket i from bucket j in time t (t is in buckets and likely small)
  for(int i = 0; i < bucketsPerMeasure; i++){
    for(int k = 0; k < nTempoBuckets; k++){
      for(int j = 0; j < bucketsPerMeasure; j++){
         for(int l = 0; l < nTempoBuckets; l++){
           
           //TODO t should be divided out by msPerBucket[k]
             //Ugly brute-force mod stuff because wraparound is annoying!
           float tbuckets = (float)t / msPerBucket[k]; 
           float[] stuffToTry = {abs( (i-(j+tbuckets)+bucketsPerMeasure)%bucketsPerMeasure), abs( ((j+tbuckets)-i+bucketsPerMeasure)%bucketsPerMeasure), abs( (i-(j+tbuckets)-bucketsPerMeasure)%bucketsPerMeasure), abs( ((j+tbuckets)-i-bucketsPerMeasure)%bucketsPerMeasure)};
           float disp = min(stuffToTry); //nBuckets you're off in the time direction
           
           //No need for fancy mod stuff with tempo; tempo doesn't wrap around!
           newprobs2[i][k] += probs2[j][l]*GaussPDF(disp, 0, tempoSD)*GaussPDF(k-l, 0, dtempoSD);
           
         }//end l
       }//end j
     //Disp = #buckets off from i that we are
      //newprobs[i] += probs[j]*GaussPDF(disp, 0, tempoSD);
      
      if(isBeat){
            newprobs2[i][k] *= beatProbs[i];
         }
         else{
           newprobs2[i][k] *= (1-beatProbs[i]);
         }
       newprobsum += newprobs2[i][k];
   } //end k
   
    
  } //end i
  
  //Normalize and get most likely
  double newprobmax = -1;
  int newprobmaxind = -1;
  for(int i = 0; i < bucketsPerMeasure; i++){
    //Normalize, then drop stuff back into probs
    probs[i] = 0;
    for(int k = 0; k < nTempoBuckets; k++){
      newprobs2[i][k] /= newprobsum;
      probs[i] += newprobs2[i][k];
    }
    
    if(probs[i] > newprobmax){
      newprobmax = probs[i];
      newprobmaxind = i;
    }
  }

  probs2 = newprobs2;
  dispProbArray(probs, isBeat);
  
  if(newprobmaxind > -1){ //Throw out cases where we're super non-confident about where we are
    int newpitch = getNote(measure, newprobmaxind); //playMe[newprobmaxind];
    if(newpitch > 0){ //So we stop each note when the next note starts
      if(pitch > 0){
        myBus.sendNoteOff(new Note(0, pitch, 100));
      }
      //Start new note
      pitch = newpitch; //Which we know is non-zero because of outer if statement
      myBus.sendNoteOn(new Note(0, pitch, 100));

    }
  }
  else{
    System.out.println("Help I'm lost");
  }
  
  System.out.println(newtime);
  System.out.println(oldtime);
  
  System.out.println(isBeat);
  
  //println(t);
  
  //No need to explicitly delay - code is slow enough already
  //delay(12); //Hardcoded to whatever worked in the continuous 1D version
  
  if(newprobmaxind + bucketsPerMeasure/4 < bucket){
    measure++;
  }
  bucket = newprobmaxind;
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


void dispProbArray(double[] A, boolean isBeat){
  background(255);
  
  int n = A.length;
  for(int i = 0; i < n; i++){
    //stroke(255, 0, 0);
    //line((float) (i*width/n), (float) (height), (float) ((i+1)*width/n - 1), (float) (height-A[i]*height));
    fill(0);
    if(isBeat){
      fill(200, 100, 0);
    }
    rect(i*width/n, (1- (float)A[i])*height, width/n, (float) A[i]*height); //Works
    //rect((float) (i*width/n), (float) (height), (float) width/n, (float) A[i]*height);
  }
}

double GaussPDF(double x, double mu, double sigma){
  float pi = 3.1415926; //But no one cares since it just shows up as a constant normalization factor anyway
  //mu = mean, sigma = st. dev.
  return 1.0/(sigma*sqrt(pi*2))*exp( (float) (-0.5*((x-mu)/sigma)*((x-mu)/sigma)));
}

void noteArray()
{
try
  {
    File myFile = new File(dataPath("WWRY.mid"));
    Sequence sequence = MidiSystem.getSequence(myFile);
    Track[] tracks = sequence.getTracks();
    mspertick = (1.0*sequence.getMicrosecondLength()/sequence.getTickLength()/1000);
    int metaidx = 0;
    int beatspermeasure = 4;
    double msperbeat = 500;
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
      for (int j = 0; j < tracks[i].size()/2; j++)
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
              double pos = ((tick * mspertick) / msperbeat) + 10e-8;
              //System.out.format("current position %f\n", pos);
              //System.out.format("milliseconds per beat %f\n", msperbeat);
              int measure = (int) (pos / beatspermeasure);
              double beat = pos % beatspermeasure;
              int bucket = (int) Math.round((pos * bucketsPerMeasure) / beatspermeasure);
              //System.out.println(buckets + "th bucket"); 
              
              while (notes.size() < bucket)
              {
                notes.add(0);
                //System.out.println("Add");
              }
              notes.add(key);

              //System.out.format("At measure %d with beat %f\n", measure, beat);
            }
          }
        }
      }
    }
    System.out.println("pre pad buckets: " + notes.size());
    while (notes.size() % bucketsPerMeasure != 0)
    {
      notes.add(0);
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
int getNote(int measure, int bucket){
  //Ignoring measure for now, it'll happen when we do a real song
  return notes.get(measure * bucketsPerMeasure + bucket);
}
