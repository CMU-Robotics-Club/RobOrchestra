import processing.sound.*; //Input from computer mic
import themidibus.*; //MIDI output to instruments/SimpleSynth
import java.util.ArrayList;
import javax.sound.midi.*; //For reading MIDI file
import Jama.*; //Matrix math

//String fileName = "twinkle_twinkle2.mid";
String fileName = "GoT7.mid";
//String fileName = "ae_test.mid";
public static final int NOTE_ON = 0x90;
public static final int NOTE_OFF = 0x80;

AudioIn in; //Raw sound input
PitchDetector pd; //Get pitches from input. Doesn't currently do anything, but we might use this eventually to grab pitch info from a human
Amplitude amp; //Get amplitudes from input
MidiBus myBus; //Pass MIDI to instruments/SimpleSynth
FFT fft;
int num_bands = 512;
int sampleRate = 44100;
ArrayList<float[]> ref_freqs;
ArrayList<Integer> ref_freq_times;
long lastPlayedTime;

int playHarmony = 0;
double beatThreshScale = 0.7;
double minBeatThresh = 0.12; //0.08;
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
int nTempoBuckets = 24; //Same idea

//Upper and lower bounds on tempo.
int minBPM = 59;
int maxBPM = 61;

//We'll compute these
float minMsPerRhythm;
float maxMsPerRhythm;

//Gaussian parameters. Hopefully don't need changing anymore
double beatprobamp = 4; //How confident we are that when we hear a beat, it corresponds to an actual beat. (As opposed to beatSD, which is how unsure we are that the beat is at the correct time.) 
double beatSD = bucketsPerRhythm/320.0; //SD on Gaussians for sensor model (when we heard a beat) in # time buckets
double posSD = bucketsPerRhythm/256.0; //SD on Gaussians for motion model (time since last measurement) in # time buckets
double tempoSD = nTempoBuckets/16.0;//1; //SD on tempo changes (# tempo buckets) - higher means we think weird stuff is more likely due to a tempo change than bad execution of same tempo

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

NoteArray nArr;
//Where we think we are in the song
int rhythmnum = 0; //Again, this is actually counting instances of the rhythm pattern, which may not line up with actual measures as written
int bucket = 0;
boolean beatReady = true; //Keep track of repeated beat detections so we can filter those out
long lastReady;

ArrayList<ArrayList<Integer>> rhythmPattern;
int bucketShift = 0;
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
  myBus = new MidiBus(this, 0, 2);
  MidiBus.list();
  
  in.amp(1);
  // start the Audio Input
  in.start();
  
  // patch the AudioIn
  pd.input(in);
  amp.input(in);
  fft.input(in);
  
  notes = new ArrayList<ArrayList<Integer>>();

  nArr = new NoteArray(fileName, bucketsPerMeasure);
  
  
  notes = nArr.notes.get(playHarmony);
  println("melody size: " + nArr.notes.get(1-playHarmony).size());
  println("harmony size: " + notes.size());
  //println(notes.size());

  //rhythmPattern = sublist(nArr.notes.get(0), (int) (bucket - bucketsPerRhythm * 0.5), (int) (bucket + bucketsPerRhythm * 0.5));
  
  float measuresPerRhythm = (1.0 * (bucketsPerRhythm+1)) / bucketsPerMeasure; //(buckets/rhythm) / (buckets/measure)
  //println("measures per rhythm " + measuresPerRhythm);
  //Before resample, notes uses bucketsPerMeasure
  //Have bucketsPerMeasure, measuresPerRhythm, and bucketsPerRhythm
  //notes = resampleBy(notes, 1.0/bucketsPerMeasure/measuresPerRhythm*(bucketsPerRhythm+1));
  //notes = resampleBy(notes, 1.0/bucketsPerMeasure*(bucketsPerRhythm+1));


  //bucketsPerRhythm = rhythmPattern.size();
  probs = new Matrix(bucketsPerRhythm+1, 1, 1.0/(bucketsPerRhythm+1));
  probsonemat = new Matrix(nTempoBuckets, 1, 1);
  probs2 = new Matrix(bucketsPerRhythm+1, nTempoBuckets);
  beatProbs = new Matrix(bucketsPerRhythm+1, 1, 0.01); //P(location | heard a beat)
  
  
  maxMsPerRhythm = 60000 / minBPM * nArr.quarternotespermeasure*measuresPerRhythm;
  minMsPerRhythm = 60000 / maxBPM * nArr.quarternotespermeasure*measuresPerRhythm;
  float dMsPerRhythm = (maxMsPerRhythm - minMsPerRhythm)/(nTempoBuckets-1);

  for(int i = 0; i < nTempoBuckets; i++){
    msPerRhythm.set(i, 0, (minMsPerRhythm + dMsPerRhythm*i)/(bucketsPerRhythm+1));
    assert(msPerRhythm.get(i, 0) > 0);
  }
  
  //for (int i = 0; i < 4; i ++)
  //{
  //  playRhythm(rhythmPattern, measuresPerRhythm);
  //} 

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
 
 //ArrayList<Integer> beatpositions = new ArrayList<Integer>();
 //for(int i = 0; i < bucketsPerRhythm+1; i++){
 //  if(rhythmPattern.get(i).size() > 0 && rhythmPattern.get(i).get(0) > 0){
 //    beatpositions.add(i);
 //  }
 //}
 //for(int i:beatpositions){
 //  for(int j = 0; j < bucketsPerRhythm+1; j++){
 //    int disp = min(abs( (i-j)%bucketsPerRhythm), abs( (j-i)%bucketsPerRhythm));
 //    //disp = #buckets off from i that we are
 //    beatProbs.set(j, 0, beatProbs.get(j, 0) + beatprobamp * GaussPDF(disp, 0, beatSD));
 //  }
 //}
 //Normalize beatProbs
 //double beatProbSum = 0;
 //for(int i = 0; i < bucketsPerRhythm+1; i++){
 //  beatProbSum += beatProbs.get(i, 0);
 //}
 //for(int i = 0; i < bucketsPerRhythm+1; i++){
 //  beatProbs.set(i, 0, beatProbs.get(i, 0) / beatProbSum);
 //}
 
 //Set up tempoGaussMat
  for(int k = 0; k < nTempoBuckets; k++){
   for(int l = 0; l < nTempoBuckets; l++){
     //Overall plan is newprobs2[i][k] = adhocPosGaussMat[i][j] * probs2[j][l] * tempoGaussMat[l][k], summed over j and l, and then this is just matrix multiplication
     //But note that tempoGaussMat is symmetric so this won't end up mattering
     tempoGaussMat.set(l, k, GaussPDF(k-l, 0, tempoSD));
   }
  }
  oldtime = millis();
  
  ref_freqs = new ArrayList<float[]>();
  ref_freq_times = new ArrayList<Integer>();
  myBus.sendNoteOn(new Note(0, MIDIfromPitch(440), 25));
  delay(500);
  lastPlayedTime = millis();
  while (millis()-lastPlayedTime < 500)
  {
    
    float[] temp = new float[num_bands];
    fft.analyze(temp);
    ref_freqs.add(temp);
    ref_freq_times.add((int) (millis()-lastPlayedTime));

  }
  myBus.sendNoteOff(new Note(0, MIDIfromPitch(440), 25));
  //rectMode(CORNERS);
  
}      

void draw()
{
  rhythmPattern = sublist(nArr.notes.get(1-playHarmony), (int) (bucket - bucketsPerRhythm * 0.5), (int) (bucket + bucketsPerRhythm * 0.5));
  //println(rhythmPattern);
  beatProbs = new Matrix(bucketsPerRhythm+1, 1, 0.01); //P(location | heard a beat)
 
 
 ArrayList<Integer> beatpositions = new ArrayList<Integer>();
 for(int i = 0; i < bucketsPerRhythm+1; i++){
   if(rhythmPattern.get(i).size() > 0 && rhythmPattern.get(i).get(0) > 0){
     beatpositions.add(i);
   }
 }
 
 for(int i:beatpositions){
   for(int j = 0; j < (bucketsPerRhythm+1); j++){
     int disp = min(abs( (i-j)%(bucketsPerRhythm+1)), abs( (j-i)%(bucketsPerRhythm+1)));
     //disp = #buckets off from i that we are
     beatProbs.set(j, 0, beatProbs.get(j, 0) + beatprobamp * GaussPDF(disp, 0, beatSD));
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
 
  background(255);
  int newtime = millis();
  int t = newtime - oldtime;
  oldtime = newtime;
  
  
  float[] freqs = new float[num_bands];
  long timeDisp = millis() - lastPlayedTime;
  fft.analyze(freqs);
  
  int bucket440 = (int) (440 * (2 * num_bands) / sampleRate);
  //ArrayList<Integer> pitch = new ArrayList<Integer>();
  int clear_num = 1;
  //pitch.add(MIDIfromPitch(440));
  //for(int i = 0; i < num_bands; i++){
  //// The result of the FFT is normalized
  //// draw the line for frequency band i scaling it up by 5 to get more amplitude.
  //  rect( i*5, height, (i+1)*5-1, height - freqs[i]*height*5 );
  //  fill(0);
  //}
  float[] ref_freqs_arr = ref_freqs.get(ref_freqs.size()-1);
  for (int i = 1; i < ref_freq_times.size(); i++)
  {
    if (timeDisp <= ref_freq_times.get(i))
    {
      int prevTime = ref_freq_times.get(i-1);
      if (Math.abs(timeDisp - prevTime) < Math.abs(timeDisp - ref_freq_times.get(i)))
      {
        ref_freqs_arr = ref_freqs.get(i-1);
      }
      else
      {
        ref_freqs_arr = ref_freqs.get(i);
      }
      break;
    }
  }
  for (int ppitch : pitch)
  {
    int bucket = (int) (pitchFromMIDI(ppitch) * (2 * num_bands) / sampleRate);
    for (int i = 0; i < num_bands; i++)
    {
      float tempinew = i / (1.0*bucket/bucket440);
      int i_new = (int) tempinew;
      if (i_new > num_bands) break;
      float round_freq;
      if (Math.round(tempinew) >= num_bands)
      {
        round_freq = ref_freqs_arr[num_bands-1];
      }
      else
      {
        round_freq = ref_freqs_arr[(int) Math.round(tempinew)];
      }
      //print(i, i_new);
      //println(freqs);
      //println(ref_freqs);
      freqs[i] -= round_freq;
      //freqs[i] -= (tempinew - Math.floor(tempinew)) * ceil_freq + (Math.floor(tempinew) + 1 - tempinew) * floor_freq; //(float) Math.log(max(1, (int)(1 + Math.exp(freqs[i_new]) - Math.exp(ref_freqs[i]))));
      //freqs[(int) Math.floor(tempinew)] -= (Math.ceil(tempinew) - tempinew) * floor_freq;
    }
    //for (int j = bucket; j <= num_bands - clear_num/2 - 1; j += bucket)
    //{
    //  for (int i = j - clear_num/2; i <= j + clear_num/2; i++)
    //  {
    //    freqs[i] = 0;
    //  }
    //}
    //for (int j = bucket; j > 1; j /= 2)
    //{
    //  for (int i = j - clear_num/2; i <= j + clear_num/2; i++)
    //  {
    //    freqs[i] = 0;
    //  }
    //}
  }
  //for(int i = 0; i < num_bands; i++){
  //// The result of the FFT is normalized
  //// draw the line for frequency band i scaling it up by 5 to get more amplitude.
  //  rect( i*5, height, (i+1)*5-1, height - freqs[i]*height*5 );
  //  fill(255,0,0);
  //}
  float max_vol = 0;
  int max_idx = 0;
  float sum = 0;
  
  for (int i = 0; i < num_bands; i++)
  {
      if (freqs[i] > max_vol)
      {
        max_vol = freqs[i];
        max_idx = i;
    
      }
      sum += freqs[i];
  }
  //float frequency = max_idx * sampleRate / (2*num_bands);
  //println(max_idx + " " + max_vol + " " + sum + " " + frequency);
  boolean detectedBeat = (max_vol > 0.7 * beatThresh) || keyPressed;
  if (max_vol > beatThresh) beatThresh += 0.005;
  else beatThresh = beatThresh - 0.001;
  if (beatThresh < minBeatThresh)
  {
    beatThresh = minBeatThresh;
    background(127);
  }
  
  boolean isBeat = detectedBeat && beatReady;
  beatReady = !detectedBeat;
  
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
        tempil *= beatProbs.get(i, 0);
      }
      else{
        tempil *= (1-beatProbs.get(i, 0));
      }
      
      prenewprobs2.set(i-bucketShift, l, tempil);
      
    }
  }

  newprobs2 = prenewprobs2.times(tempoGaussMat);
  
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
  dispProbArray(probs, isBeat);
  dispProbArray(beatProbs, isBeat);
  
  bucketShift = newprobmaxind - (bucketsPerRhythm/2);
  //if(bucketShift == 0){
  //  //We haven't gotten to the next bucket yet, don't repeat the note
  //  return;
  //}
  
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
