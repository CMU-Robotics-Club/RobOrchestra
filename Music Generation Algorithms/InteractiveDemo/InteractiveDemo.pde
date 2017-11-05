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

String[] scaleNames = {"Major", "Minor", "Chromatic"};
String[][] subScaleNames = {{"Blah1", "Blah2"}, {"Meh1", "Meh2", "Meh3"}, {"Ugh1", "Ugh2"}};
int[][][] scaleOffsets = {
  {{0, 2, 4, 5, 7, 9, 11, 12},
   {0, 2, 4, 5, 7, 9, 11, 12}},
  
  {{0, 2, 3, 5, 7, 8, 10, 12},
   {0, 2, 3, 5, 7, 8, 10, 12},
   {0, 2, 3, 5, 7, 8, 10, 12}},
   
  {{0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12},
   {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12}}
};
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
  size(380, 278);
  cp5 = new ControlP5(this);
  myBus = new MidiBus(this, 0, 1);
    
  cp5.setFont(new ControlFont(createFont("OpenSans-Bold.ttf", 9, true), 9));
  
  resetArrays();
  
  onOff = cp5.addButton("togglePlay")
    .setPosition(30, 30)
    .setSize(35, 73)
    .setFont(new ControlFont(createFont("Power.ttf", 15, true), 15))
    .setCaptionLabel("\u23FB")
  ;
  
  scaleCycle = cp5.addButton("changeScale")
    .setPosition(70, 30)
    .setSize(70, 34)
  ;
  subScaleCycle = cp5.addButton("changeSubScale")
    .setPosition(70, 69)
    .setSize(70, 34)
  ;
  
  xyloSlider = cp5.addSlider("xyloDensity")
    .setPosition(155, 30)
    .setSize(195, 21)
    .setRange(0.0, 1.0)
    .setValue(0.55)
  ;
  xyloSlider.getCaptionLabel().align(ControlP5.LEFT, ControlP5.CENTER).setPaddingX(10);
  xyloSlider.getValueLabel().align(ControlP5.RIGHT, ControlP5.CENTER).setPaddingX(10);
  
  snareSlider = cp5.addSlider("snareDensity")
    .setPosition(155, 56)
    .setSize(195, 21)
    .setRange(0.0, 1.0)
    .setValue(0.70);
  ;
  snareSlider.getCaptionLabel().align(ControlP5.LEFT, ControlP5.CENTER).setPaddingX(10);
  snareSlider.getValueLabel().align(ControlP5.RIGHT, ControlP5.CENTER).setPaddingX(10);
  
  tomSlider = cp5.addSlider("tomDensity")
    .setPosition(155, 82)
    .setSize(195, 21)
    .setRange(0.0, 1.0)
    .setValue(0.45);
  ;
  tomSlider.getCaptionLabel().align(ControlP5.LEFT, ControlP5.CENTER).setPaddingX(10);
  tomSlider.getValueLabel().align(ControlP5.RIGHT, ControlP5.CENTER).setPaddingX(10);
  
  tonicKnob = cp5.addKnob("tonic")
    .setRange(0, 100)
    .setValue(60)
    .setPosition(30, 118)
    .setRadius(30)
    .setDragDirection(Knob.VERTICAL)
  ;
  tonicKnob.getCaptionLabel().align(ControlP5.CENTER, ControlP5.BOTTOM_OUTSIDE).setPaddingY(-42).setFont(new ControlFont(createFont("OpenSans-Bold.ttf", 7, true), 7));
  tonicKnob.getValueLabel().setFont(new ControlFont(createFont("OpenSans-Bold.ttf", 8, true), 8));

  lengthKnob = cp5.addKnob("len")
    .setRange(100, 500)
    .setValue(250)
    .setPosition(30, 188)
    .setRadius(30)
    .setDragDirection(Knob.VERTICAL)
  ;
  lengthKnob.getCaptionLabel().align(ControlP5.CENTER, ControlP5.BOTTOM_OUTSIDE).setPaddingY(-42).setFont(new ControlFont(createFont("OpenSans-Bold.ttf", 7, true), 7));
  lengthKnob.getValueLabel().setFont(new ControlFont(createFont("OpenSans-Bold.ttf", 8, true), 8));
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
  
  tonicKnob.setCaptionLabel("Tone");
  tonicKnob.setColorBackground(color(103, 0, 0));
  tonicKnob.setColorForeground(color(204, 0, 43));
  tonicKnob.setColorActive(color(204, 0, 43));
  
  lengthKnob.setCaptionLabel("Delay");
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
        myBus.sendNoteOn(new Note(channel, tonic + scaleOffsets[curScale][curSubScale][i], velocity));  
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
  for(int i = 0; i < notes.length; i++) {
    noteSliders[i] = cp5.addSlider(Integer.toString(i))
    .setPosition(350 - (260 / notes.length) * (notes.length - i - 1) - (260 / notes.length - 5), 118)
    .setSize(260 / notes.length - 5, 130)
    .setRange(0, 1)
    .setValue(1)
    .setColorForeground(color(24, 100, 204))
    .setColorActive(color(24, 100, 204))
    .setCaptionLabel(noteNames[(scaleOffsets[curScale][curSubScale][i] - scaleOffsets[curScale][curSubScale][0]) % 12]);
   ;
   noteSliders[i].getCaptionLabel().align(ControlP5.CENTER, ControlP5.BOTTOM_OUTSIDE).setPaddingY(-17);
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