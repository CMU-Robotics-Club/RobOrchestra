import processing.sound.*;
import themidibus.*;;
import java.util.ArrayList;

FFT fft;
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
float ampThreshold = 0.03 * ampScale;
//float[] spectrum = new float[bands];

Note oldNote = null;

void setup()
{
  size(1000, 800);
  background(255);
  System.out.println(Sound.list());
  // Create an Input stream which is routed into the Amplitude analyzer
  //fft = new FFT(this, bands);
  pd = new PitchDetector(this, 0.55);
  in = new AudioIn(this, 0);
  amp = new Amplitude(this);
  
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
 
}      

void draw()
{ 
  //fft.analyze(spectrum);
  float freq = pd.analyze();
  float amplitude = ampScale * amp.analyze();
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
    line(x-1, height - ampOld, x, height - amplitude);
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
  }
  
  //System.out.println(notes);
}

//This works, TODO do clever log space things eventually? (Take log of freq, then divide by 12thrt2)
int MIDIfromPitch(double freq){
  if(freq <= 10){
    return 0;
  }
  double twelfthrt2 = Math.pow(2, 1.0/12); //=1.something_small
  int midiA = 69;
  float freqA = 440;
  int midi = midiA;
  while(freq > freqA*Math.sqrt(twelfthrt2)){
    freq /= twelfthrt2;
    midi++;
  }
  while(freq < freqA/Math.sqrt(twelfthrt2)){
    freq *= twelfthrt2;
    midi--;
  }
  return midi;
}
