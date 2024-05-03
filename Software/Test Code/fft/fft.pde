import processing.sound.*;
import themidibus.*;
import java.io.File;
import java.lang.*;
import java.util.Arrays;
import java.util.ArrayList;
import java.io.FileInputStream;

import javax.sound.midi.MetaMessage;
import javax.sound.midi.MidiEvent;
import javax.sound.midi.MidiMessage;
import javax.sound.midi.MidiSystem;
import javax.sound.midi.Sequence;
import javax.sound.midi.ShortMessage;
import javax.sound.midi.Track;
import javax.sound.midi.InvalidMidiDataException;

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
double mspertick;
int currentTick;
float ampThreshold = 0.03;
//float[] spectrum = new float[bands];

Note oldNote = null;

SinOsc osc;
Sound s;
Track[] tracks;
int numBuckets;
double[] buckets;
void setup()
{

  size(1000, 800);
  background(255);
  System.out.println(Sound.list());
  
  Sound s = new Sound(this);
  //s.outputDevice(4); //Warning about static method seems fine probably
  
  // Create an Input stream which is routed into the Amplitude analyzer
  //fft = new FFT(this, bands);
  pd = new PitchDetector(this, 0.55); //Last arg is confidence - increase to filter out more garbage
  in = new AudioIn(this, 0);
  amp = new Amplitude(this);

  osc = new SinOsc(this);
  osc.freq(440);
  osc.play();
  
  myBus = new MidiBus(this, 0, 2);
  File myFile = new File(dataPath("auldlangsyne.mid"));
  try
  {
    
    Sequence sequence = MidiSystem.getSequence(myFile);
    tracks = sequence.getTracks();
    numBuckets = (int) sequence.getTickLength()/30;
    System.out.println(sequence.getTickLength() + " ticks -> "  + numBuckets + " buckets");
    mspertick = (1.0*sequence.getMicrosecondLength()/sequence.getTickLength()/1000);
    buckets = new double[numBuckets];
    for (int i = 0; i < numBuckets; i++)
    {
      buckets[i] = 1.0/numBuckets;
    }
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
 
}      

void draw()
{ 
  //fft.analyze(spectrum);
  float freq = pd.analyze();
  float amplitude = amp.analyze();
  System.out.println(amplitude);
  
  //for(int i = 0; i < bands; i++)
  //{
  //// The result of the FFT is normalized
  //// draw the line for frequency band i scaling it up by 5 to get more amplitude.
  //line( i * (512/bands), height, i * (512/bands), height - spectrum[i]*height*50 );
  //}
    yOld = y;
    y = freq;
    x++;
    stroke(255, 0, 0);
    line(x-1, height - yOld, x, height - y);
    stroke(0, 0, 255);
    line(x-1, height - ampOld * ampScale, x, height - amplitude * ampScale);
    ampOld = amplitude;
    //System.out.println(freq);
  
  midi = MIDIfromPitch(y);
  
  if (midi > 0 && amplitude > ampThreshold)
  {
    //if (notes.size() > 0) notes.remove(0);
    notes.add(midi);
    
    //Note newNote = new Note(0, midi, 50);
    
    //if (oldNote != null)
    //{
    //  myBus.sendNoteOff(oldNote);
    //}
    //myBus.sendNoteOn(newNote);
    //oldNote = newNote;
    
      Note newNote = new Note(0, midi, 0); //Low volume for now so we don't pick up ourself
      if (oldNote != null){
        myBus.sendNoteOff(oldNote);
      }
      myBus.sendNoteOn(newNote);
      oldNote = newNote;
      
      osc.freq((float)pitchFromMIDI(midi));
      osc.play();
      println(MIDIfromPitch(y));
  }
  else{
    osc.stop();
  }


  delay(10);
  
  //System.out.println(notes);
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
