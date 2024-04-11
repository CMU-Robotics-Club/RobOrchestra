import processing.sound.*;
import themidibus.*;;

FFT fft;
AudioIn in;
PitchDetector pd;
int bands = 64;
float bpm = 188;
float x = 0;
float y = 0;
float yOld = 0;
MidiBus myBus;
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
  
  myBus = new MidiBus(this, 0, 1);
  MidiBus.list();
  
  in.amp(1);
  // start the Audio Input
  in.start();
  
  // patch the AudioIn
  //fft.input(in);
  pd.input(in);
  background(255);
}      

void draw()
{ 

  //fft.analyze(spectrum);
  float freq = pd.analyze();
  

  //for(int i = 0; i < bands; i++)
  //{
  //// The result of the FFT is normalized
  //// draw the line for frequency band i scaling it up by 5 to get more amplitude.
  //line( i * (512/bands), height, i * (512/bands), height - spectrum[i]*height*50 );
  //}
    yOld = y;
    y = freq;
    x++;
    line(x-1, height - yOld, x, height - y);
    //System.out.println(freq);


  Note newNote = new Note(0, MIDIfromPitch(y), 100);
  if (oldNote != null){
    myBus.sendNoteOff(oldNote);
  }
  myBus.sendNoteOn(newNote);
  oldNote = newNote;
  
  delay(50);
  
}

//This works, TODO do clever log space things eventually? (Take log of freq, then divide by 12thrt2)
int MIDIfromPitch(double freq){
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
