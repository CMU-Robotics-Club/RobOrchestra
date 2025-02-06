import processing.sound.*;
//import processing.sound.BeatDetector;

FFT fft;
AudioIn in;
//BeatDetector bd;
int bands = 512;
float[] spectrum = new float[bands];

BandPass bandPass;

float oldamp = -1;
float oldoldamp = -1;

void setup() {
  size(512, 360);
  background(255);
  
  System.out.println(Sound.list());
    
  // Create an Input stream which is routed into the Amplitude analyzer
  fft = new FFT(this, bands);
  //bd = new BeatDetector(this);
  in = new AudioIn(this, 0);
  
  // start the Audio Input
  in.start();
  
  bandPass = new BandPass(this);
  bandPass.bw(256);
  bandPass.freq(512);
  bandPass.process(in);
  
  // patch the AudioIn
  fft.input(in);
  rectMode(CORNERS);
}      

void draw() { 
  background(255);
  fft.analyze(spectrum);
  float amp = 0;
  for(int i = 0; i < bands; i++){
  // The result of the FFT is normalized
  // draw the line for frequency band i scaling it up by 5 to get more amplitude.
  rect( i*5, height, (i+1)*5-1, height - spectrum[i]*height*5 );
  fill(0);
  amp += spectrum[i];
  }
  oldoldamp = oldamp;
  oldamp = amp;
  if(oldoldamp < oldamp && oldamp > amp){
    System.out.println("Beat");
  }
}
