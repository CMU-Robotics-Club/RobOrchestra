import controlP5.*;
import themidibus.*;

ControlP5 cp5;
MidiBus myBus;

Button onOff;
Button scaleCycle;
Button subScaleCycle;

Slider xyloSlider;
Slider snareSlider;
Slider tomSlider;

Knob tonicKnob;
Knob lengthKnob;

int snarePitchMIDI = 36;
int tomPitchMIDI = 37;
int channel = 0;
int velocity = 120;
int[][] diatonic = {{0,2,4,5,7,9,11,12},{0,2,3,5,7,9,10,12},{0,1,3,5,7,8,10,12},{0,2,4,6,7,9,11,12},{0,2,4,5,7,9,10,12},{0,2,3,5,7,8,10,12},{0,1,3,5,6,8,10,12}};
int[][] jazz ={{0,3,5,6,7,10,12},{0,2,4,5,7,9,10,11,12},{0,2,4,6,8,10,12},{0,2,3,5,7,9,10,12},{0,2,4,5,7,9,10,12},{0,1,3,4,6,7,9,10,12},{0,2,3,5,6,8,9,11,12}};
int[][] minor = {{0,2,3,5,7,8,10,12},{0,2,3,5,7,8,11,12},{0,2,3,5,7,9,11,12},{0,2,3,5,7,9,10,12},{0,1,3,5,7,8,10,12},{0,1,3,5,6,8,10,12}};
int[][] pentatonic = {{0,2,4,7,9,12},{0,3,5,7,10,12}};
int[][] other = {{0,1,2,3,4,5,6,7,8,9,10,11,12},{0,1,5,6,10,12},{0,1,3,6,7,8,10,12}};
float[][] diatonicWeight = {{1,.5,1,.25,1,.5,.75,1},{1,.5,1,.25,1,.5,.75,1},{1,.5,1,.25,1,.5,.75,1},{1,.5,1,.25,1,.5,.75,1},{1,.5,1,.25,1,.5,.75,1},{1,.5,1,.25,1,.5,.75,1},{1,.5,1,.25,1,.5,.75,1}};
float[][] jazzWeight ={{1,1,.75,1,1,.75,1},{1,.5,1,.25,1,.5,.75,.1,1},{1,.5,1,.5,.5,1,.5},{1,.5,1,.25,1,.5,.75,1},{1,.5,1,.25,1,.5,.75,1},{1,.5,1,.5,.5,.5,.5,.5,1},{1,.5,1,.5,.5,.5,.5,.5,1}};
float[][] minorWeight = {{1,.5,1,.25,1,.5,.75,1},{1,.5,1,.25,1,.5,.75,1},{1,.5,1,.25,1,.5,.75,1},{1,.5,1,.25,1,.5,.75,1},{1,.5,1,.25,1,.5,.75,1},{1,.5,1,.25,1,.5,.75,1}};
float[][] pentatonicWeight = {{1,.75,1,1,.75,1},{1,1,.75,1,.75,1}};
float[][] otherWeight = {{1,.5,.5,.5,.5,.5,.5,.5,.5,.5,.5,.5,1},{1,.75,.75,.75,.75,1},{1,.75,1,.75,1,.75,.75,1}};
String[] scaleNames = {"Diatonic", "Jazz", "Minor", "Pentatonic", "Other"};
String[][] subScaleNames = {{"Ionian", "Dorian", "Phyrigian", "Lydian", "Mixolydian", "Aeolian", "Locrian"}, 
                           {"Blues", "Bebop", "Whole Tone", "Dorian", "Mixolydian", "Half-Whole", "Whole-Half"}, 
                           {"Natural", "Harmonic", "Melodic", "Dorian", "Phyrigian", "Locrian"},
                           {"Major", "Minor"},
                           {"Chromatic", "Iwato", "Pelog"}};
int[][][] scaleOffsets = {diatonic, jazz, minor, pentatonic, other};
float[][][] scaleWeights = {diatonicWeight, jazzWeight, minorWeight, pentatonicWeight, otherWeight};
int curScale = 0;
int curSubScale = 0;

boolean isPlaying = true;

int beatIndex = 0;
int tonic = 0;
int len = 0;

String[] noteNames = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};
float[] notes = {};
float[] probs = {};

float xyloDensity = 0.0;
float snareDensity = 0.0;
float tomDensity = 0.0;

int measureLength = 16;
float[] xylo = {1.0, 0.00, 0.00, 0.00, 1.0, 0.00, 0.0, 0.0, 1.0, 0.00, 0.0, 0.00, 1.0, 0.0, 0.0, 0.0};
float[] tom = {1.0, -1.0, 0.0, -1.0, 0.5, -1.0, 0.0, -1.0, 1.0, -1.0, 0.0, -1.0, 0.5, 0.0, -1.0, 0.0};
float[] snare = {0.5, -1.0, 0.0, -1.0, 1.0, -1.0, 0.0, -1.0, 0.5, -1.0, 0.0, -1.0, 1.0, -1.0, 0.0, -1.0};

void setup() {
  int scl = displayHeight/720;
  int sizeW = scl*380;
  int sizeH = scl*278;
  //fullScreen();
  size(380, 278);
  surface.setResizable(true);
  surface.setSize(sizeW, sizeH);
 
  cp5 = new ControlP5(this);
  myBus = new MidiBus(this, 0, 1);
    
  cp5.setFont(new ControlFont(createFont("OpenSans-Bold.ttf", scl*9, true), scl*9));
  
  resetArrays();
  
  onOff = cp5.addButton("togglePlay")
    .setPosition(scl*30, scl*30)
    .setSize(scl*35, scl*73)
    .setFont(new ControlFont(createFont("Power.ttf", scl*15, true), scl*15))
    .setCaptionLabel("\u23FB")
  ;
  
  scaleCycle = cp5.addButton("changeScale")
    .setPosition(scl*70, scl*30)
    .setSize(scl*70, scl*34)
  ;
  subScaleCycle = cp5.addButton("changeSubScale")
    .setPosition(scl*70, scl*69)
    .setSize(scl*70, scl*34)
  ;
  
  xyloSlider = cp5.addSlider("xyloDensity")
    .setPosition(scl*155, scl*30)
    .setSize(scl*195, scl*21)
    .setRange(0.0, 1.0)
    .setValue(0.55)
  ;
  xyloSlider.getCaptionLabel().align(ControlP5.LEFT, ControlP5.CENTER).setPaddingX(scl*10);
  xyloSlider.getValueLabel().align(ControlP5.RIGHT, ControlP5.CENTER).setPaddingX(scl*10);
  
  snareSlider = cp5.addSlider("snareDensity")
    .setPosition(scl*155, scl*56)
    .setSize(scl*195, scl*21)
    .setRange(0.0, 1.0)
    .setValue(0.70);
  ;
  snareSlider.getCaptionLabel().align(ControlP5.LEFT, ControlP5.CENTER).setPaddingX(scl*10);
  snareSlider.getValueLabel().align(ControlP5.RIGHT, ControlP5.CENTER).setPaddingX(scl*10);
  
  tomSlider = cp5.addSlider("tomDensity")
    .setPosition(scl*155, scl*82)
    .setSize(scl*195, scl*21)
    .setRange(0.0, 1.0)
    .setValue(0.45);
  ;
  tomSlider.getCaptionLabel().align(ControlP5.LEFT, ControlP5.CENTER).setPaddingX(scl*10);
  tomSlider.getValueLabel().align(ControlP5.RIGHT, ControlP5.CENTER).setPaddingX(scl*10);
  
  tonicKnob = cp5.addKnob("tonic")
    .setRange(60, 72)
    .setValue(67)
    .setPosition(scl*30, scl*118)
    .setRadius(scl*30)
    .setDragDirection(Knob.VERTICAL)
  ;
  tonicKnob.getCaptionLabel().align(ControlP5.CENTER, ControlP5.BOTTOM_OUTSIDE).setPaddingY(scl*-42).setFont(new ControlFont(createFont("OpenSans-Bold.ttf", scl*7, true), scl*7));
  tonicKnob.getValueLabel().setFont(new ControlFont(createFont("OpenSans-Bold.ttf", scl*8, true), scl*8));

  lengthKnob = cp5.addKnob("len")
    .setRange(100, 500)
    .setValue(250)
    .setPosition(scl*30, scl*188)
    .setRadius(scl*30)
    .setDragDirection(Knob.VERTICAL)
  ;
  lengthKnob.getCaptionLabel().align(ControlP5.CENTER, ControlP5.BOTTOM_OUTSIDE).setPaddingY(scl*-42).setFont(new ControlFont(createFont("OpenSans-Bold.ttf", scl*7, true), scl*7));
  lengthKnob.getValueLabel().setFont(new ControlFont(createFont("OpenSans-Bold.ttf", scl*8, true), scl*8));
}

int curTime = 0;
void draw() {
  float sum = 0.0;
  for (int i = 0; i < notes.length; i++)
    sum += notes[i];
  for (int i = 0; i < notes.length; i++)
    probs[i] = notes[i] / sum;
  
  background(255, 255, 255);
  
  onOff.setColorBackground(isPlaying ? color(204, 0, 43) : color(240, 240, 240));
  onOff.setColorForeground(isPlaying ? color(204, 0, 43) : color(240, 240, 240));
  onOff.setColorActive(isPlaying ? color(235, 0, 43) : color(230, 230, 230));
  onOff.setColorLabel(isPlaying ? color(255, 255, 255) : color(204, 0, 43));
  
  scaleCycle.setCaptionLabel(scaleNames[curScale]);
  scaleCycle.setColorBackground(color(24, 100, 204));
  scaleCycle.setColorForeground(color(24, 100, 204));
  scaleCycle.setColorActive(color(49, 144, 225));
  
  subScaleCycle.setCaptionLabel(subScaleNames[curScale][curSubScale]);
  subScaleCycle.setColorBackground(color(9, 35, 70));
  subScaleCycle.setColorForeground(color(9, 35, 70));
  subScaleCycle.setColorActive(color(30, 80, 150));
  
  xyloSlider.setCaptionLabel("Xylo Density");
  xyloSlider.setColorBackground(color(103, 0, 0));
  xyloSlider.setColorForeground(color(204, 0, 43));
  xyloSlider.setColorActive(color(204, 0, 43));
  
  snareSlider.setCaptionLabel("Snare Density");
  snareSlider.setColorBackground(color(103, 0, 0));
  snareSlider.setColorForeground(color(204, 0, 43));
  snareSlider.setColorActive(color(204, 0, 43));
  
  tomSlider.setCaptionLabel("Tom Density");
  tomSlider.setColorBackground(color(103, 0, 0));
  tomSlider.setColorForeground(color(204, 0, 43));
  tomSlider.setColorActive(color(204, 0, 43));
  
  tonicKnob.setCaptionLabel("Root");
  tonicKnob.setColorBackground(color(103, 0, 0));
  tonicKnob.setColorForeground(color(204, 0, 43));
  tonicKnob.setColorActive(color(204, 0, 43));
  tonicKnob.setValueLabel(noteNames[((scaleOffsets[curScale][curSubScale][0] - scaleOffsets[curScale][curSubScale][0]) + tonic) % 12]);
  resetArrays();
  
  lengthKnob.setCaptionLabel("Tempo"); //delay --> tempo
  lengthKnob.setColorForeground(color(24, 100, 204));
  lengthKnob.setColorActive(color(24, 100, 204));

  if(isPlaying && millis() > curTime + len) {
    playMelody();
    curTime = millis();
  }
}

void playMelody() {
  double r = Math.random();
  double xyloPlay = Math.random();
  double snarePlay = Math.random();
  double tomPlay = Math.random();
  
  double xyloThresh = Math.min(xylo[beatIndex] + xyloDensity, 1.0);
  double snareThresh = Math.min(snare[beatIndex] + snareDensity, 1.0);
  double tomThresh = Math.min(tom[beatIndex] + tomDensity, 1.0);
  
  if(snarePlay <= snareThresh) {
    myBus.sendNoteOn(new Note(0, snarePitchMIDI, 100));  
  }
   
  delay(2);
  if(tomPlay <= tomThresh) {
    myBus.sendNoteOn(new Note(0, tomPitchMIDI, 100));   
  }
    
  delay(2);
  if(xyloPlay <= xyloThresh) {
    for(int i = 0; i < scaleOffsets[curScale][curSubScale].length; i++) {
      r -= probs[i];
      if(r < 0) {
        myBus.sendNoteOn(new Note(channel, (scaleOffsets[curScale][curSubScale][i] + tonic) % 12 + 60, velocity)); //range is 60 to 72  
        break;
      }
    }      
  }
  beatIndex = (beatIndex + 1) % measureLength;
}

void togglePlay() {
  isPlaying = !isPlaying;
}

void resetArrays() {
  for(int i = 0; i < notes.length; i++) {
    cp5.remove(Integer.toString(i));
  }
  int newLength = scaleOffsets[curScale][curSubScale].length;
  notes = new float[newLength];
  probs = new float[newLength];
  
  for(int i = 0; i < newLength; i++) {
    notes[i] = 1.0;
    probs[i] = 1/7;
  }
  Slider[] noteSliders = new Slider[notes.length];
  int scl = displayHeight/720;
  for(int i = 0; i < notes.length; i++) {
    noteSliders[i] = cp5.addSlider(Integer.toString(i))
    .setPosition(scl*350 - (scl*260 / notes.length) * (notes.length - i - 1) - (scl*260 / notes.length - 5), scl*118)
    .setSize(scl*260 / notes.length - 5, scl*130)
    .setRange(0, 1)
    .setValue(scaleWeights[curScale][curSubScale][i])
    .setColorForeground(color(24, 100, 204))
    .setColorActive(color(24, 100, 204))
    .setCaptionLabel(noteNames[((scaleOffsets[curScale][curSubScale][i] - scaleOffsets[curScale][curSubScale][0]) + tonic) % 12]);
   ;
   noteSliders[i].getCaptionLabel().align(ControlP5.CENTER, ControlP5.BOTTOM_OUTSIDE).setPaddingY(scl*-17);
   noteSliders[i].setValueLabel("");
  }
}

void changeScale() {
  curSubScale = 0;
  curScale = (curScale + 1) % scaleNames.length;
  resetArrays();
}

void changeSubScale() {
  curSubScale = (curSubScale + 1) % subScaleNames[curScale].length;
  resetArrays();
}