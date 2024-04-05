import processing.sound.*;

FFT fft;
AudioIn in;
PitchDetector pd;
int bands = 64;
float bpm = 188;
float x = 0;
float y = 0;
float yOld = 0;
//float[] spectrum = new float[bands];

void setup()
{
  size(1000, 800);
  background(255);
  System.out.println(Sound.list());
  // Create an Input stream which is routed into the Amplitude analyzer
  //fft = new FFT(this, bands);
  pd = new PitchDetector(this, 0.55);
  in = new AudioIn(this, 0);
  
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

  delay(50);
}
