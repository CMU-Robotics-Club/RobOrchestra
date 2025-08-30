import processing.sound.AudioIn; //Input from computer mic
import processing.sound.PitchDetector; //Input from computer mic
import processing.sound.Amplitude; //Input from computer mic
import processing.sound.FFT; //Input from computer mic
import themidibus.*; //MIDI output to instruments/SimpleSynth
import java.util.ArrayList;
import javax.sound.midi.*; //For reading MIDI file
import Jama.*; //Matrix math

//String fileName = "WorseApple.mid";
String fileName = "WWRY3.mid";
//String fileName = "GoT7.mid";
//String fileName = "ae_test3.mid";
//String fileName = "alt_test.mid";
public static final int NOTE_ON = 0x90;
public static final int NOTE_OFF = 0x80;
public final float[] PITCHES = { 41.2f, 43.7f, 46.2f, 49.0f, 51.9f, 55.0f, 58.3f, 61.7f, 65.4f, 69.3f, 
                                    73.4f, 77.8f, 82.4f, 87.3f, 92.5f, 98.0f, 103.8f, 110.0f, 116.5f, 123.5f, 
                                    130.8f, 138.6f, 146.8f, 155.6f, 164.8f, 174.6f, 185.0f, 196.0f, 207.7f, 220.0f, 
                                    233.1f, 246.9f, 261.6f, 277.2f, 293.7f, 311.1f, 329.6f, 349.2f, 370.0f, 392.0f, 
                                    415.3f, 440.0f, 466.2f, 493.9f, 523.3f, 554.4f, 587.3f, 622.3f, 659.3f, 698.5f, 
                                    740.0f, 784.0f, 830.6f, 880.0f, 932.3f, 987.8f, 1046.5f, 1108.7f, 1174.7f, 1244.5f, 
                                    1318.5f, 1396.9f, 1480.0f, 1568.0f, 1661.2f, 1760.0f, 1864.7f, 1979.5f, 2093.0f };
public final int[] pitch_offsets = {0, 12, 19, 24, 28, 31, 33, 36};
SpecWhitener sw;
//Minim minim;
//AudioInput in2;
PitchDetect pd2;

AudioIn in; //Raw sound input
PitchDetector pd; //Get pitches from input. Doesn't currently do anything, but we might use this eventually to grab pitch info from a human
Amplitude amp; //Get amplitudes from input
MidiBus myBus; //Pass MIDI to instruments/SimpleSynth
FFT fft;
int num_bands = 1024;
int timeSize = num_bands;
int sampleRate = 44100;
ArrayList<float[]> ref_freqs;
ArrayList<Integer> ref_freq_times;
long lastPlayedTime;

int playHarmony = 0;
double beatThreshScale = 0.7;
double minBeatThresh = 0.08; //0.08;
double beatThresh = 0.01; //Amplitude threshold to be considered a beat. NEED TO TUNE THIS when testing in new environment/with Xylobot (also adjust down SimpleSynth volume if necessary)
//Want to automatically adjust this based on background volume
//Median is just bad (probably more non-beats than beats, so it'll be too low)
//Mean is maybe okay, probably want a little higher
//Really need to also make sure we don't pick up ourself, though hopefully a mean thing will catch that
//Pretty sure we can just keep a bunch of recent measurements and gradually forget the old stuff. Will this forget how loud we are???

double measureRange = 0.5;
// how many measures we see on each side of current bucket

int bucketsPerRhythm = 96; //Pick something reasonably large (but not so large that it makes computations slow)
// total # of buckets for window (+1?)
// rhythmPattern.size() = bucketsPerRhythm + 1
int bucketsPerMeasure = (int) (bucketsPerRhythm/measureRange)/2; // dont touch, changed to line up w/ bucketsPerRhythm
// 
int nTempoBuckets = 36; //Same idea

//Upper and lower bounds on tempo.
int minBPM = 60;
int maxBPM = 180;

//We'll compute these
float minMsPerRhythm;
float maxMsPerRhythm;

//Gaussian parameters. Hopefully don't need changing anymore
double beatprobamp = 4; //How confident we are that when we hear a beat, it corresponds to an actual beat. (As opposed to beatSD, which is how unsure we are that the beat is at the correct time.) 
double beatSD = bucketsPerRhythm/320.0; //SD on Gaussians for sensor model (when we heard a beat) in # time buckets
double posSD = bucketsPerRhythm/128.0; //SD on Gaussians for motion model (time since last measurement) in # time buckets
double tempoSD = nTempoBuckets/80.0;//1; //SD on tempo changes (# tempo buckets) - higher means we think weird stuff is more likely due to a tempo change than bad execution of same tempo

//These get filled in later
ArrayList<ArrayList<Integer>> notes; //Gets populated when we read the MIDI file
Matrix probs;
Matrix probsonemat;
Matrix probs2;
Matrix beatProbs; //P(location | heard a beat)
Matrix[] beatProbsArr;
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

ArrayList<ArrayList<Integer>> rhythmPattern;
int bucketShift = 0;
float measuresPerRhythm;
void setup()
{
  
  //println(bucketsPerMeasure);
  println("start");

  size(1000, 800);
  background(255);
  
  // Create an Input stream which is routed into the Amplitude analyzer
  pd = new PitchDetector(this, 0.55); //Last arg is confidence - increase to filter out more garbage
  in = new AudioIn(this, 0);
  amp = new Amplitude(this);
  
  fft = new FFT(this, num_bands);
  //fft = new FFT(timeSize, sampleRate);
  pd2 = new PitchDetect(timeSize*2, sampleRate);
  //minim = new Minim(this);
  
  //// use the getLineIn method of the Minim object to get an AudioInput

  //in2 = minim.getLineIn();
  //in2.enableMonitoring();


  myBus = new MidiBus(this, 0, 2);
  MidiBus.list();
  
  println(fft.getClass());
    
  in.amp(1);
  // start the Audio Input
  in.start();
  
  // patch the AudioIn
  pd.input(in);
  amp.input(in);
  fft.input(in);
  sw = new SpecWhitener(timeSize, sampleRate);
  
  notes = new ArrayList<ArrayList<Integer>>();

  nArr = new NoteArray(fileName, bucketsPerMeasure);
  
  
  notes = nArr.notes.get(playHarmony);
  println("melody size: " + nArr.notes.get(1-playHarmony).size());
  println("harmony size: " + notes.size());

  //rhythmPattern = sublist(nArr.notes.get(0), (int) (bucket - bucketsPerRhythm * 0.5), (int) (bucket + bucketsPerRhythm * 0.5));
  
  measuresPerRhythm = (1.0 * (bucketsPerRhythm+1)) / bucketsPerMeasure; //(buckets/rhythm) / (buckets/measure)
  
  //Before resample, notes uses bucketsPerMeasure
  //Have bucketsPerMeasure, measuresPerRhythm, and bucketsPerRhythm
  //notes = resampleBy(notes, 1.0/bucketsPerMeasure/measuresPerRhythm*(bucketsPerRhythm+1));
  //notes = resampleBy(notes, 1.0/bucketsPerMeasure*(bucketsPerRhythm+1));


  //bucketsPerRhythm = rhythmPattern.size();
  probs = new Matrix(bucketsPerRhythm+1, 1, 1.0/(bucketsPerRhythm+1));
  probsonemat = new Matrix(nTempoBuckets, 1, 1);
  probs2 = new Matrix(bucketsPerRhythm+1, nTempoBuckets);
  beatProbs = new Matrix(bucketsPerRhythm+1, 1, 0.01); //P(location | heard a beat)
  beatProbsArr = new Matrix[PITCHES.length];
  for (int i = 0; i < beatProbsArr.length; i++)
  {
    beatProbsArr[i] = new Matrix(bucketsPerRhythm+1, 1, 0.01);
  }
  
  
  maxMsPerRhythm = 60000 / minBPM * nArr.quarternotespermeasure*measuresPerRhythm;
  minMsPerRhythm = 60000 / maxBPM * nArr.quarternotespermeasure*measuresPerRhythm;
  float dMsPerRhythm = (maxMsPerRhythm - minMsPerRhythm)/(nTempoBuckets-1);

  for(int i = 0; i < nTempoBuckets; i++){
    msPerRhythm.set(i, 0, (minMsPerRhythm + dMsPerRhythm*i)/(bucketsPerRhythm+1));
    assert(msPerRhythm.get(i, 0) > 0);
  }

 for(int i = 0; i < bucketsPerRhythm+1; i++){
   for(int j = 0; j < nTempoBuckets; j++){
     if (i == bucketsPerRhythm/2)
     {
       probs2.set(i, j, 1);
     }
     else
     {
       probs2.set(i, j, 0);
     }
   }
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
  printMatrix(tempoGaussMat.times(probsonemat));
  printMatrix(tempoGaussMat);
  //assert(false);
}      

void draw()
{

  rhythmPattern = sublist(nArr.notes.get(1-playHarmony), (int) (bucket - bucketsPerRhythm * 0.5), (int) (bucket + bucketsPerRhythm * 0.5));

  beatProbs = new Matrix(bucketsPerRhythm+1, 1, 0.01); //P(location | heard a beat)
  for (int i = 0; i < beatProbsArr.length; i++)
  {
    beatProbsArr[i] = new Matrix(bucketsPerRhythm+1, 1, 0.01);
  }

  for(int i = 0; i < bucketsPerRhythm+1; i++){
   if(rhythmPattern.get(i).size() > 0 && rhythmPattern.get(i).get(0) > 0){
     //beatpositions.add(i);
     for(int j = 0; j < (bucketsPerRhythm+1); j++){
     int disp = min(abs( (i-j)%(bucketsPerRhythm+1)), abs( (j-i)%(bucketsPerRhythm+1)));
     //disp = #buckets off from i that we are
     beatProbs.set(j, 0, beatProbs.get(j, 0) + beatprobamp * GaussPDF(disp, 0, beatSD));
     for (int k = 0; k < rhythmPattern.get(i).size(); k++)
     {
       //if (!(rhythmPattern.get(i).get(k) >= 60 && rhythmPattern.get(i).get(k) <= 72)) continue;
       beatProbsArr[rhythmPattern.get(i).get(k)-28].set(j, 0, beatProbsArr[rhythmPattern.get(i).get(k)-28].get(j, 0) + beatprobamp * GaussPDF(disp, 0, beatSD));
     }
   }
   }
 }


 //Normalize beatProbs
 double beatProbSum = 0;
 for(int i = 0; i < (bucketsPerRhythm+1); i++){
   beatProbSum += beatProbs.get(i, 0);
 }
 for(int i = 0; i < (bucketsPerRhythm+1); i++){
   beatProbs.set(i, 0, beatProbs.get(i, 0) / beatProbSum);
 }
 for (int h = 0; h < beatProbsArr.length; h++)
 {
   beatProbSum = 0;
   for(int i = 0; i < (bucketsPerRhythm+1); i++){
     beatProbSum += beatProbsArr[h].get(i, 0);
   }
   for(int i = 0; i < (bucketsPerRhythm+1); i++){
     beatProbsArr[h].set(i, 0, beatProbsArr[h].get(i, 0) / beatProbSum);
   }
 }
 
 
  background(255);
  int newtime = millis();
  int t = newtime - oldtime;
  oldtime = newtime;
  
  
  float[] freqs = new float[num_bands];

  float[] buffer = new float[num_bands];
  fft.analyze(buffer);

  float[] pd2out = pd2.detect(buffer);
  int[] fzeros = pd2.fzeros;
  
  for (int i = 0; i < fzeros.length; i++)
  {
    if (fzeros[i] == 1)
    {
      println(PITCHES[i]);
    }
  }
  boolean hasPitch = false;
  int firstPitchIdx = 0;
  for (int i = 20; i < PITCHES.length; i++)
  {
    if (fzeros[i] == 1)
    {
      hasPitch = true;
      firstPitchIdx = i;
      //println(PITCHES[i]);
      break;
    }
  }
  println("first pitch = " + PITCHES[firstPitchIdx]);
  
  boolean keyPressedBeat = keyPressed;
  boolean detectedBeat = (amp.analyze() > 0.7 * beatThresh && hasPitch) || keyPressedBeat;
  
  if (amp.analyze() > beatThresh) beatThresh += 0.005;
  else beatThresh = beatThresh - 0.001;
  if (beatThresh < minBeatThresh)
  {
    beatThresh = minBeatThresh;
    background(127);
  }
  
  boolean isBeat = detectedBeat && beatReady;
  beatReady = !detectedBeat;
  if (isBeat) println("beat");
  //Compute new probs
  Matrix newprobs2 = new Matrix(bucketsPerRhythm+1, nTempoBuckets);
  double newprobsum = 0;
  

  //Get new position probabilities, based on time since last read and whether we heard a beat
  //Going to bucket i from bucket j in time t 
  Matrix prenewprobs2 = new Matrix(bucketsPerRhythm+1, nTempoBuckets);
  for(int i = 0; i < bucketsPerRhythm+1; i++){ //New pos
    if (i-bucketShift < 0 || i-bucketShift >= bucketsPerRhythm+1) continue;
    for(int l = 0; l < nTempoBuckets; l++){ //Old tempo (okay, this gets weird because we're updating position with the old tempo now. Should be close though)
      float tbuckets = (float)t / (float)msPerRhythm.get(l, 0); //tbuckets is time in buckets and likely small
      
      float tempil = 0;
      
      for(int j = 0; j < (bucketsPerRhythm+1); j++){ //Old pos
        //float[] stuffToTry = {abs( (float) ((i-(j+tbuckets)+bucketsPerRhythm+1)%(bucketsPerRhythm+1))), abs( (float)(((j+tbuckets)-i+bucketsPerRhythm+1)%(bucketsPerRhythm+1))), abs( (float)((i-(j+tbuckets)-(bucketsPerRhythm+1))%(bucketsPerRhythm+1))), abs( (float)(((j+tbuckets)-i-(bucketsPerRhythm+1))%(bucketsPerRhythm+1)))};
         float[] stuffToTry = {i-(j+tbuckets)};
         float disp = min(stuffToTry); //nBuckets you're off in the time direction
         double posPDF = GaussPDF(disp, 0, posSD);
         tempil += probs2.get(j, l)*posPDF;
      }
      if(isBeat){
        if (keyPressedBeat)
          tempil *= beatProbs.get(i, 0);
        else
        {
          for (int h = 0; h < fzeros.length; h++)
          {
            if (fzeros[h] == 1)
            {
              tempil *= beatProbsArr[h].get(i, 0);
            }
            else
              tempil *= 1-beatProbsArr[h].get(i,0);
          }
        }
      }
      else{
        tempil *= (1-beatProbs.get(i, 0));
      }
      
      prenewprobs2.set(i-bucketShift, l, tempil);
      
    }
  }

  newprobs2 = prenewprobs2.times(tempoGaussMat);
  
  //NOTE: msPerRhythm scales linearly with bucket index
  //This means a LOWER bucket index corresponds to a FASTER tempo!!
  //Also these tempo probs are unnormalized
  Matrix temp = new Matrix(1, bucketsPerRhythm+1, 1).times(newprobs2);
  printMatrix(temp);
  double maxval = 0;
  int maxind = 0;
  for (int i = 0; i < nTempoBuckets; i++){
    if(temp.get(0, i) > maxval){
      maxval = temp.get(0, i);
      maxind = i;
    }
  }
  println("maxval: " + maxval + ", maxind: " + maxind);
  double BPM = 60000 / (msPerRhythm.get(maxind, 0)*(bucketsPerRhythm+1)) * nArr.quarternotespermeasure*measuresPerRhythm; //remember msPerRhythm is actually storing ms per time-bucket
  println("BPM: " + BPM);
  
  newprobsum = new Matrix(1, bucketsPerRhythm+1, 1).times(newprobs2).times(new Matrix(nTempoBuckets, 1, 1)).get(0, 0);
        
  //Normalize and get most likely
  double newprobmax = -1; //Set this to min probability we're comfortable playing on, or negative if we always want to play
  int newprobmaxind = -1;
  
  
  //We want to add across the rows of newprobs2 and dump that into probs. Can do that with matrix multiplication.
  newprobs2 = newprobs2.times(1/newprobsum);
  probs = newprobs2.times(probsonemat);
  
  //printMatrix(probs.getArray());
  for(int i = 0; i < (bucketsPerRhythm+1); i++){
    if(probs.get(i, 0) > newprobmax){
      newprobmax = probs.get(i, 0);
      newprobmaxind = i;
    }
  }

  probs2 = newprobs2;
  //dispProbArray(probs, detectedBeat);

  if (!(hasPitch && !keyPressedBeat))
  {
    background(0,0,255);
    dispProbArray(beatProbs, detectedBeat);
  }
  else dispProbArray(beatProbsArr[firstPitchIdx], detectedBeat);
  //dispProbArray(new Matrix(test, cap), false);
  
  bucketShift = newprobmaxind - (bucketsPerRhythm/2);
  if(bucketShift == 0){
    //We haven't gotten to the next bucket yet, don't repeat the note
    return;
  }
  
  bucket += bucketShift;
  
  if(newprobmaxind > -1) { //Throw out cases where we're super non-confident about where we are. Negative to always assume the best guess is correct
    ArrayList<Integer> newpitch = notes.get((bucket + notes.size()) % notes.size());
    if(newpitch.size() > 0){ //So we stop each note when the next note starts
      for(Integer ppitch: pitch){
        if(ppitch > 0){
          
          myBus.sendNoteOff(new Note(0, ppitch.intValue(), 25));
        }
      }

      //Start new note
      pitch = newpitch; //Which we know is non-zero because of outer if statement
      //println(pitch);
      for(Integer ppitch: pitch){
        if(ppitch > 0){
          myBus.sendNoteOn(new Note(0, ppitch.intValue(), 25));
        }
      }
      lastPlayedTime = millis();
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
  
  double res = 1.0/(sigma*sqrt(pi*2))*exp( (float) (-0.5*((x-mu)/sigma)*((x-mu)/sigma)));
  //if (Double.isNaN(res)) println("NaN at " + x + " " + mu + " " + sigma);
  //if (res < 10e-5)
  //  res = 10e-5;
   
  return res;
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

void playRhythm(ArrayList<ArrayList<Integer>> rhythmPattern, float measuresPerRhythm)
{
  double playMsPerRhythm = 60000.0 / nArr.BPM * nArr.quarternotespermeasure*measuresPerRhythm;
  double msPerBucket = playMsPerRhythm / (bucketsPerRhythm+1);
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

  ArrayList<ArrayList<Integer>> sublist(ArrayList<ArrayList<Integer>> list, int start, int end)
  {
    ArrayList<ArrayList<Integer>> res = new ArrayList<ArrayList<Integer>>();
    for (int i = 0; i <= end - start; i++)
    {
      res.add(new ArrayList<Integer>());
      for (int j = 0; j < list.get((i + start + list.size()) % list.size()).size(); j++)
      {
        res.get(i).add(list.get((i + start + list.size()) % list.size()).get(j));
      }
    }
    return res;
  }
  
  void printMatrix(double[][] arr)
  {
    for (int i = 0; i < arr.length; i++)
    {
      for (int j = 0; j < arr[0].length; j++)
      {
        System.out.format("%2f ", arr[i][j]);
      }
      println();
    }
  }
  
  void printMatrix(Matrix arr)
  {
    for (int i = 0; i < arr.getRowDimension(); i++)
    {
      for (int j = 0; j < arr.getColumnDimension(); j++)
      {
        System.out.format("%2f ", arr.get(i, j));
      }
      println();
    }
  }
  
  void printArray(double[] arr)
  {
    for (int i = 0; i < arr.length; i++)
    {
        System.out.format("%2f ", arr[i]);

    }
    println();
  }
  
  void printArray(int[] arr)
  {
    for (int i = 0; i < arr.length; i++)
    {
        System.out.format("%2d ", arr[i]);

    }
    println();
  }
