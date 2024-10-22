import processing.sound.*; //Input from computer mic
import themidibus.*; //MIDI output to instruments/SimpleSynth
import java.util.ArrayList;
import java.text.*;
import javax.sound.midi.*; //For reading MIDI file
import Jama.*; //Matrix math

String fileName = "GoC.mid";
public static final int NOTE_ON = 0x90;
public static final int NOTE_OFF = 0x80;

AudioIn in; //Raw sound input
PitchDetector pd; //Get pitches from input. Doesn't currently do anything, but we might use this eventually to grab pitch info from a human
Amplitude amp; //Get amplitudes from input
MidiBus myBus; //Pass MIDI to instruments/SimpleSynth

double beatThresh = 0.5; //Amplitude threshold to be considered a beat; TODO tune (also adjust down SimpleSynth volume if necessary)
//Want to automatically adjust this based on background volume
//Median is just bad (probably more non-beats than beats, so it'll be too low)
//Mean is maybe okay, probably want a little higher
//Really need to also make sure we don't pick up ourself, though hopefully a mean thing will catch that
//Pretty sure we can just keep a bunch of recent measurements and gradually forget the old stuff. Will this forget how loud we are???

int bucketsPerRhythm = 64; //Pick something reasonably large (but not so large that it makes computations slow)
int bucketsPerMeasure = 96; //Same idea. This should only be used in NoteArray to get a bucketed rhythm pattern, which we then resample to length bucketsPerRhythm
int nTempoBuckets = 64; //Same idea

//Upper and lower bounds on tempo. TODO: These probably change based on length of "measure" (AKA rhythm sequence)
int minBPM = 60;
int maxBPM = 110;

//We'll compute these
float minMsPerRhythm;
float maxMsPerRhythm;

//Gaussian parameters. Hopefully don't need changing anymore
double beatprobamp = 4; //How confident we are that when we hear a beat, it corresponds to an actual beat. (As opposed to beatSD, which is how unsure we are that the beat is at the correct time.) 
double beatSD = bucketsPerRhythm/320.0; //SD on Gaussians for sensor model (when we heard a beat) in # time buckets
double posSD = bucketsPerRhythm/64.0/2; //SD on Gaussians for motion model (time since last measurement) in # time buckets
double tempoSD = nTempoBuckets/32.0;//1; //SD on tempo changes (# tempo buckets) - higher means we think weird stuff is more likely due to a tempo change than bad execution of same tempo

//These get filled in later
ArrayList<ArrayList<Integer>> notes; //Gets populated when we read the MIDI file
Matrix probs;
Matrix probsonemat;
Matrix probs2;
Matrix beatProbs; //P(location | heard a beat)
Matrix tempoGaussMat = new Matrix(nTempoBuckets, nTempoBuckets);
Matrix msPerRhythm = new Matrix(nTempoBuckets, 1);


int oldtime = millis(); //Time between code start and last beat check/update. Processing has 64 bit integers, so we probably don't overflow - max is about 2 billion milliseconds, so about 500 hours
ArrayList<Integer> pitch = new ArrayList<Integer>(); //All notes currently playing

//Where we think we are in the song
int rhythmnum = 0; //Again, this is actually counting instances of the rhythm pattern, which may not line up with actual measures as written
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
  ArrayList<ArrayList<Integer>> presampleRhythmPattern = nArr.pattern;
  println("AAAAAAAAAAAAAAAAAAAAAAAAAAAAAA");
  println(presampleRhythmPattern);
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
  System.out.println();  
  System.out.println(60000 / minBPM * nArr.beatspermeasure*measuresPerRhythm/bucketsPerRhythm);
  println(measuresPerRhythm);
  println(bucketsPerRhythm);
  
  maxMsPerRhythm = 60000 / minBPM * nArr.beatspermeasure*measuresPerRhythm;
  System.out.println(60000 / nArr.BPM * nArr.beatspermeasure*measuresPerRhythm/bucketsPerRhythm);
  System.out.println(60000 / maxBPM * nArr.beatspermeasure*measuresPerRhythm/bucketsPerRhythm);
  minMsPerRhythm = 60000 / maxBPM * nArr.beatspermeasure*measuresPerRhythm;
  float dMsPerRhythm = (maxMsPerRhythm - minMsPerRhythm)/(nTempoBuckets-1);

  for(int i = 0; i < nTempoBuckets; i++){
    msPerRhythm.set(i, 0, (minMsPerRhythm + dMsPerRhythm*i)/bucketsPerRhythm);
    assert(msPerRhythm.get(i, 0) > 0);
  }
 
 for(int i = 0; i < bucketsPerRhythm; i++){
   probs.set(i, 0, 1.0/bucketsPerRhythm);
   for(int j = 0; j < nTempoBuckets; j++){
     probs2.set(i, j, 1.0/bucketsPerRhythm/nTempoBuckets);
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
    ArrayList<Integer> newpitch = getNote(rhythmnum, newprobmaxind);
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
    rhythmnum++;
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
      out.get(x).add(0);
    }
    else{
      for(int y = (int)ceil(startbucket); y < endbucket; y++){
        for(Integer pitch: rhythmSeq.get(y)){
          out.get(x).add(pitch);
        }
      }
    }
  }
  return out;
}

//This function and getNote are just going to keep using ArrayLists, but should be self-contained so it should be fine
void noteArray()
{
try
  {
    File myFile = new File(dataPath(fileName));
    Sequence sequence = MidiSystem.getSequence(myFile);
    Track[] tracks = sequence.getTracks();
    double mspertick = (1.0*sequence.getMicrosecondLength()/sequence.getTickLength()/1000);
    int metaidx = 0;
    int beatspermeasure = 4;
    double msperbeat = 500;
    
    //Grab all the MetaMessage stuff from the start of the first track to get tempo and time signature information
    //Assumes tempo and time signature won't change later, should be fine if we stick to simple songs for now
    while (metaidx < tracks[0].size() && tracks[0].get(metaidx).getMessage() instanceof MetaMessage)
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
        //msperbeat = (b[3] << 16 | b[4] << 8 | b[5]) / 1000.0;
        int top = (b[3] & 0xff);
        int mid = (b[4] & 0xff);
        int bot = (b[5] & 0xff);
        msperbeat = ((top << 16) + (mid << 8) + bot) / 1000.0;
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
    
    int melodytrack = 0;
          
    for (int i = melodytrack; i < melodytrack+1; i++) // go through tracks, limited to track 0 for now
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
              //int measure = (int) (pos / beatspermeasure);
              //double beat = pos % beatspermeasure;
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
    //System.out.println(notes);
    //System.out.println("post pad buckets: " + notes.size());
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
ArrayList<Integer> getNote(int rhythmnum, int bucket){
  int ind = (rhythmnum * bucketsPerRhythm + bucket)%notes.size();
  return notes.get(ind);
}
