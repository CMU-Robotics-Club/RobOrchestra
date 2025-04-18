import processing.sound.*; //Input from computer mic
import themidibus.*; //MIDI output to instruments/SimpleSynth
import java.util.ArrayList;
import javax.sound.midi.*; //For reading MIDI file
import Jama.*; //Matrix math

String fileName = "WWRY3.mid";
//String fileName = "GoT6.mid";
public static final int NOTE_ON = 0x90;
public static final int NOTE_OFF = 0x80;

AudioIn in; //Raw sound input
PitchDetector pd; //Get pitches from input. Doesn't currently do anything, but we might use this eventually to grab pitch info from a human
Amplitude amp; //Get amplitudes from input
MidiBus myBus; //Pass MIDI to instruments/SimpleSynth

double minBeatThresh = 0.1;
double beatThresh = 0.01; //Amplitude threshold to be considered a beat. NEED TO TUNE THIS when testing in new environment/with Xylobot (also adjust down SimpleSynth volume if necessary)
//Want to automatically adjust this based on background volume
//Median is just bad (probably more non-beats than beats, so it'll be too low)
//Mean is maybe okay, probably want a little higher
//Really need to also make sure we don't pick up ourself, though hopefully a mean thing will catch that
//Pretty sure we can just keep a bunch of recent measurements and gradually forget the old stuff. Will this forget how loud we are???

int bucketsPerRhythm = 48; //Pick something reasonably large (but not so large that it makes computations slow)
int bucketsPerMeasure = 96; //Same idea. This should only be used in NoteArray to get a bucketed rhythm pattern, which we then resample to length bucketsPerRhythm
int nTempoBuckets = 64; //Same idea

//Upper and lower bounds on tempo.
int minBPM = 60;
int maxBPM = 120;

//We'll compute these
float minMsPerRhythm;
float maxMsPerRhythm;

//Gaussian parameters. Hopefully don't need changing anymore
double beatprobamp = 4; //How confident we are that when we hear a beat, it corresponds to an actual beat. (As opposed to beatSD, which is how unsure we are that the beat is at the correct time.) 
double beatSD = bucketsPerRhythm/320.0; //SD on Gaussians for sensor model (when we heard a beat) in # time buckets
double posSD = bucketsPerRhythm/64.0/2; //SD on Gaussians for motion model (time since last measurement) in # time buckets
double tempoSD = nTempoBuckets/16.0;//1; //SD on tempo changes (# tempo buckets) - higher means we think weird stuff is more likely due to a tempo change than bad execution of same tempo

//These get filled in later
ArrayList<ArrayList<Integer>> notes; //Gets populated when we read the MIDI file
Matrix probs;
Matrix probsonemat;
Matrix probs2;
Matrix beatProbs; //P(location | heard a beat)
Matrix tempoGaussMat = new Matrix(nTempoBuckets, nTempoBuckets);
Matrix msPerRhythm = new Matrix(nTempoBuckets, 1); //This actually ends up storing msPerBucket...


int oldtime = millis(); //Time between code start and last beat check/update. Processing has 64 bit integers, so we probably don't overflow - max is about 2 billion milliseconds, so about 500 hours
ArrayList<Integer> pitch = new ArrayList<Integer>(); //All notes currently playing

NoteArray nArr;
//Where we think we are in the song
int rhythmnum = 0; //Again, this is actually counting instances of the rhythm pattern, which may not line up with actual measures as written
int bucket = 0;
boolean beatReady = true; //Keep track of repeated beat detections so we can filter those out
long lastReady;


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
  notes = new ArrayList<ArrayList<Integer>>();

  nArr = new NoteArray(fileName, bucketsPerMeasure);
  
  
  notes = nArr.notes.get(0);

  ArrayList<ArrayList<Integer>> presampleRhythmPattern = nArr.pattern;
  ArrayList<ArrayList<Integer>> rhythmPattern = resample(presampleRhythmPattern, bucketsPerRhythm);
  float measuresPerRhythm = (float)presampleRhythmPattern.size() / bucketsPerMeasure; //(buckets/rhythm) / (buckets/measure)
  
  //Before resample, notes uses bucketsPerMeasure
  //Have bucketsPerMeasure, measuresPerRhythm, and bucketsPerRhythm
  notes = resampleBy(notes, 1.0/bucketsPerMeasure/measuresPerRhythm*bucketsPerRhythm);
  


  //bucketsPerRhythm = rhythmPattern.size();
  probs = new Matrix(bucketsPerRhythm, 1);
  probsonemat = new Matrix(nTempoBuckets, 1, 1);
  probs2 = new Matrix(bucketsPerRhythm, nTempoBuckets);
  beatProbs = new Matrix(bucketsPerRhythm, 1); //P(location | heard a beat)
  
  beatSD = bucketsPerRhythm/320.0;
  posSD = bucketsPerRhythm/64.0;
  
  
  maxMsPerRhythm = 60000 / minBPM * nArr.beatspermeasure*measuresPerRhythm;
  minMsPerRhythm = 60000 / maxBPM * nArr.beatspermeasure*measuresPerRhythm;
  float dMsPerRhythm = (maxMsPerRhythm - minMsPerRhythm)/(nTempoBuckets-1);

  for(int i = 0; i < nTempoBuckets; i++){
    msPerRhythm.set(i, 0, (minMsPerRhythm + dMsPerRhythm*i)/bucketsPerRhythm);
    assert(msPerRhythm.get(i, 0) > 0);
  }
  
  //for (int i = 0; i < 4; i ++)
  //{
  //  playRhythm(rhythmPattern, measuresPerRhythm);
  //} 

 for(int i = 0; i < bucketsPerRhythm; i++){
   probs.set(i, 0, 1.0/bucketsPerRhythm);
   for(int j = 0; j < nTempoBuckets; j++){
     probs2.set(i, j, Math.random());
   }
   beatProbs.set(i, 0, 0.01); //We'll normalize this later
 }
 
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
  //Want to stop tempo reverting to the middle, so we need to take the weight we're blurring out of bounds and add it back to the end elements
  //Note: We might start having the opposite problem (bias toward extreme tempos) if we have too few tempo buckets since I'm dumping all the overflow on the closest edge rather than splitting it properly
  //But hopefully this is fine - SD scales with number of buckets, and the far edge is at least 4 SDs out with default settings
  //UPDATE: Pretty sure correct answer is always add to diagonal element instead
  Matrix tempoGaussMatSums = tempoGaussMat.times(probsonemat);
  for(int k = 0; k < nTempoBuckets; k++){
    tempoGaussMat.set(k, k, tempoGaussMat.get(k, k) + 1-tempoGaussMatSums.get(k, 0));
  }
  oldtime = millis();
}      

void draw()
{
  background(255);
  int newtime = millis();
  int t = newtime - oldtime;
  println(t);
  oldtime = newtime;
  
  boolean detectedBeat = (amp.analyze() > 0.7 * beatThresh) || keyPressed;
  if (amp.analyze() > beatThresh) beatThresh += 0.005;
  else beatThresh = beatThresh - 0.001;
  if (beatThresh < minBeatThresh)
  {
    beatThresh = minBeatThresh;
    background(127);
  }
  boolean isBeat = detectedBeat && beatReady;
  beatReady = !detectedBeat;
  //if (beatReady) lastReady = millis();
  //if (lastReady <= millis() - 50)
  //{
  //  beatThresh += 0.001;
  //  println(beatThresh);
  //}
  //beatThresh -= 10e-5;
  //Compute new probs
  Matrix newprobs2 = new Matrix(bucketsPerRhythm, nTempoBuckets);
  double newprobsum = 0;
  

  //Get new position probabilities, based on time since last read and whether we heard a beat
  //Going to bucket i from bucket j in time t 
  Matrix prenewprobs2 = new Matrix(bucketsPerRhythm, nTempoBuckets);
  
  for(int i = 0; i < bucketsPerRhythm; i++){ //New pos
    for(int l = 0; l < nTempoBuckets; l++){ //Old tempo (okay, this gets weird because we're updating position with the old tempo now. Should be close though)
      float tbuckets = (float)t / (float)msPerRhythm.get(l, 0); //tbuckets is time in buckets and likely small
      
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
  double newprobmax = -1; //Set this to min probability we're comfortable playing on, or negative if we always want to play
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
  
  if(newprobmaxind == bucket){
    //We haven't gotten to the next bucket yet, don't repeat the note
    return;
  }
  
  if(newprobmaxind <= bucket - 0.5*bucketsPerRhythm){
  //if(bucket >= 0.9*bucketsPerRhythm && newprobmaxind <= 0.1*bucketsPerRhythm && newprobmaxind > -1){
    rhythmnum++;
    //background(0, 255, 0); //Flashes screen on new measure
  }
  bucket = newprobmaxind;
  
  if(newprobmaxind > -1) { //Throw out cases where we're super non-confident about where we are. Negative to always assume the best guess is correct
    ArrayList<Integer> newpitch = getNote(rhythmnum, newprobmaxind);
    if(newpitch.size() > 0){ //So we stop each note when the next note starts
      for(Integer ppitch: pitch){
        if(ppitch > 0){
          myBus.sendNoteOff(new Note(0, ppitch.intValue(), 25));
        }
      }
      //Start new note
      pitch = newpitch; //Which we know is non-zero because of outer if statement
      for(Integer ppitch: pitch){
        if(ppitch > 0){
          myBus.sendNoteOn(new Note(0, ppitch.intValue(), 25));
        }
      }
    }
  }
  else{
    System.out.println("Help I'm lost");
    //exit();
  }
  
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

ArrayList<ArrayList<Integer>> resampleBy(ArrayList<ArrayList<Integer>> rhythmSeq, float factor){
  return resample(rhythmSeq, (int)(rhythmSeq.size()*factor));
}

ArrayList<ArrayList<Integer>> resample(ArrayList<ArrayList<Integer>> rhythmSeq, int newlen){
  int oldlen = rhythmSeq.size();
  ArrayList<ArrayList<Integer>> out = new ArrayList<ArrayList<Integer>>();
  for(int x = 0; x < newlen; x++){
    float startbucket = ((float)x/newlen * oldlen);
    float endbucket = ((float)(x+1)/newlen * oldlen);
    out.add(new ArrayList<Integer>());
    if(ceil(startbucket) >= endbucket){
      //Do nothing
    }
    else{
      for(int y = (int)ceil(startbucket); y < endbucket; y++){
        for(Integer pitch: rhythmSeq.get(y)){
          if(pitch > 0){
            out.get(x).add(pitch);
          }
        }
      }
    }
  }
  return out;
}
ArrayList<Integer> getNote(int rhythmnum, int bucket){
  int ind = (rhythmnum * bucketsPerRhythm + bucket)%notes.size();
  return notes.get(ind);
}

void playRhythm(ArrayList<ArrayList<Integer>> rhythmPattern, float measuresPerRhythm)
{
  double playMsPerRhythm = 60000.0 / nArr.BPM * nArr.beatspermeasure*measuresPerRhythm;
  double msPerBucket = playMsPerRhythm / bucketsPerRhythm;
  int i = 0;
  ArrayList<Integer> played = new ArrayList<Integer>();
  while (i < rhythmPattern.size())
  {
 
    if(rhythmPattern.get(i).size() > 0){ //So we stop each note when the next note starts
      for(Integer ppitch: played){
        if(ppitch > 0){
          myBus.sendNoteOff(new Note(0, ppitch.intValue(), 25));
        }
      }
      //Start new note
      played = rhythmPattern.get(i); //Which we know is non-zero because of outer if statement
      for(Integer ppitch: rhythmPattern.get(i)){
        if(ppitch > 0){
          myBus.sendNoteOn(new Note(0, ppitch.intValue(), 25));
        }
      }
    }
    i++;
    delay((int) msPerBucket);
  }
}
