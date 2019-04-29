import controlP5.*;
import themidibus.*;

ControlP5 cp5;
MidiBus myBus;

Button melodyLabel;
Button harmonyLabel;
Button onOff1;
Button onOff2;
Button scaleCycle;
Button subScaleCycle;

Slider xyloSlider;
Slider snareSlider;
Slider tomSlider;

Knob tonicKnob;
Knob tempoKnob;

Textlabel rootNote;
Textlabel tempoBPM;

Slider[] noteSliders = {};

int scale = 2;

int snarePitchMIDI = 36;
int tomPitchMIDI = 37;
int channel = 0;
int perc_channel = -1;
int velocity = 100; 

String[] scaleNames = {"Diatonic", "Jazz", "Minor", "Pentatonic", "Other"};
String[][] subScaleNames = {
  {"Ionian", "Dorian", "Phyrigian", "Lydian", "Mixolydian", "Aeolian", "Locrian"},
  {"Blues", "Bebop", "Whole Tone", "Dorian", "Mixolydian", "Half-Whole\nDim", "Whole-Half\nDim"},
  {"Natural", "Harmonic", "Melodic", "Dorian", "Phyrigian", "Locrian"},
  {"Major", "Minor"},
  {"Chromatic", "Iwato", "Pelog"}
};

int[][][] scaleOffsets = {
  {{0, 2, 4, 5, 7, 9, 11},
   {0, 2, 3, 5, 7, 9, 10},
   {0, 1, 3, 5, 7, 8, 10},
   {0, 2, 4, 6, 7, 9, 11},
   {0, 2, 4, 5, 7, 9, 10},
   {0, 2, 3, 5, 7, 8, 10},
   {0, 1, 3, 5, 6, 8, 10}},
  
  {{0, 3, 5, 6, 7, 10},
   {0, 2, 4, 5, 7, 9, 10, 11},
   {0, 2, 4, 6, 8, 10},
   {0, 2, 3, 5, 7, 9, 10},
   {0, 2, 4, 5, 7, 9, 10},
   {0, 1, 3, 4, 6, 7, 9, 10},
   {0, 2, 3, 5, 6, 8, 9, 11}},
   
  {{0, 2, 3, 5, 7, 8, 10},
   {0, 2, 3, 5, 7, 8, 11},
   {0, 2, 3, 5, 7, 9, 11},
   {0, 2, 3, 5, 7, 9, 10},
   {0, 1, 3, 5, 7, 8, 10},
   {0, 1, 3, 5, 6, 8, 10}},
   
  {{0, 2, 4, 7, 9},
   {0, 3, 5, 7, 10}},
    
  {{0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11},
   {0, 1, 5, 6, 10},
   {0, 1, 3, 6, 7, 8, 10}}
};

float[][][] scaleWeights = {
  {{1.00, 0.50, 1.00, 0.25, 1.00, 0.70, 0.40},
   {1.00, 0.50, 1.00, 0.25, 1.00, 0.50, 0.75},
   {1.00, 0.50, 1.00, 0.25, 1.00, 0.50, 0.75},
   {1.00, 0.50, 1.00, 0.25, 1.00, 0.50, 0.75},
   {1.00, 0.50, 1.00, 0.25, 1.00, 0.50, 0.75},
   {1.00, 0.50, 1.00, 0.25, 1.00, 0.50, 0.75},
   {1.00, 0.50, 1.00, 0.25, 1.00, 0.50, 0.75}},
   
  {{1.00, 1.00, 0.75, 1.00, 1.00, 0.75},
   {1.00, 0.50, 1.00, 0.25, 1.00, 0.50, 0.75, 0.25},
   {1.00, 0.50, 1.00, 0.50, 0.50, 1.00},
   {1.00, 0.50, 1.00, 0.25, 1.00, 0.50, 0.75},
   {1.00, 0.50, 1.00, 0.25, 1.00, 0.50, 0.75},
   {1.00, 0.50, 1.00, 0.50, 0.50, 0.50, 0.50, 0.50},
   {1.00, 0.50, 1.00, 0.50, 0.50, 0.50, 0.50, 0.50}},
   
  {{1.00, 0.50, 1.00, 0.25, 1.00, 0.50, 0.75},
   {1.00, 0.50, 1.00, 0.25, 1.00, 0.50, 0.75},
   {1.00, 0.50, 1.00, 0.25, 1.00, 0.50, 0.75},
   {1.00, 0.50, 1.00, 0.25, 1.00, 0.50, 0.75},
   {1.00, 0.50, 1.00, 0.25, 1.00, 0.50, 0.75},
   {1.00, 0.50, 1.00, 0.25, 1.00, 0.50, 0.75}},
   
  {{1.00, 0.75, 1.00, 1.00, 0.75},
   {1.00, 1.00, 0.75, 1.00, 0.75}},
   
  {{1.00, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50, 0.50},
   {1.00, 0.75, 0.75, 0.75, 0.75},
   {1.00, 0.75, 1.00, 0.75, 1.00, 0.75, 0.75}}
};

int curScale = 0;
int curSubScale = 0;

boolean isPlaying1 = true;
boolean isPlaying2 = false;

int beatIndex = 0;
int tonic = 0;
int tempo = 0;
int prev_tone_index_1 = 1;
int prev_tone_index_2 = 1;
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
  surface.setSize(380 * scale, 278 * scale);
  cp5 = new ControlP5(this);
  myBus = new MidiBus(this, 0, 1);
  MidiBus.list();
    
  cp5.setFont(new ControlFont(createFont("OpenSans-Bold.ttf", 9 * scale, true), 9 * scale));
  
  resetArrays();
  
  melodyLabel = cp5.addButton("melodyLabel")
    .setPosition(0 * scale, 5 * scale)
    .setSize(50 * scale, 30 * scale)
    .setCaptionLabel("Melody")
    .setColorBackground(color(255, 255, 255))
    .setColorForeground(color(255, 255, 255))
    .setColorActive(color(255, 255, 225))
    .setColorLabel(color(0, 0, 0)); 
  ;
  
  harmonyLabel = cp5.addButton("harmonyLabel")
    .setPosition(48 * scale, 5 * scale)
    .setSize(50 * scale, 30 * scale)
    .setCaptionLabel("Harmony")
    .setColorBackground(color(255, 255, 255))
    .setColorForeground(color(255, 255, 255))
    .setColorActive(color(255, 255, 225))
    .setColorLabel(color(0, 0, 0));    
  ;
  
  onOff1 = cp5.addButton("togglePlay1")
    .setPosition(10 * scale, 30 * scale)
    .setSize(35 * scale, 73 * scale)
    .setFont(new ControlFont(createFont("Power.ttf", 15 * scale, true), 15 * scale))
    .setCaptionLabel("\u23FB")
  ;
  
  onOff2 = cp5.addButton("togglePlay2")
    .setPosition(55 * scale, 30 * scale)
    .setSize(35 * scale, 73 * scale)
    .setFont(new ControlFont(createFont("Power.ttf", 15 * scale, true), 15 * scale))
    .setCaptionLabel("\u23FB")
  ;  
  
  scaleCycle = cp5.addButton("changeScale")
    .setPosition(100 * scale, 30 * scale)
    .setSize(70 * scale, 34 * scale)
    .setColorBackground(color(24, 100, 204))
    .setColorForeground(color(24, 100, 204))
    .setColorActive(color(49, 144, 225))
  ;
  subScaleCycle = cp5.addButton("changeSubScale")
    .setPosition(100 * scale, 69 * scale)
    .setSize(70 * scale, 34 * scale)
    .setColorBackground(color(9, 35, 70))
    .setColorForeground(color(9, 35, 70))
    .setColorActive(color(30, 80, 150))
  ;
  
  xyloSlider = cp5.addSlider("xyloDensity")
    .setPosition(175 * scale, 30 * scale)
    .setSize(195 * scale, 21 * scale)
    .setRange(0.0, 1.0)
    .setValue(0.55)
    .setCaptionLabel("Xylo Density")
    .setColorBackground(color(103, 0, 0))
    .setColorForeground(color(204, 0, 43))
    .setColorActive(color(204, 0, 43))
  ;
  xyloSlider.getCaptionLabel().align(ControlP5.LEFT, ControlP5.CENTER).setPaddingX(10 * scale);
  xyloSlider.getValueLabel().align(ControlP5.RIGHT, ControlP5.CENTER).setPaddingX(10 * scale);
  
  snareSlider = cp5.addSlider("snareDensity")
    .setPosition(175 * scale, 56 * scale)
    .setSize(195 * scale, 21 * scale)
    .setRange(0.0, 1.0)
    .setValue(0.70)
    .setCaptionLabel("Snare Density")
    .setColorBackground(color(103, 0, 0))
    .setColorForeground(color(204, 0, 43))
    .setColorActive(color(204, 0, 43))
  ;
  snareSlider.getCaptionLabel().align(ControlP5.LEFT, ControlP5.CENTER).setPaddingX(10 * scale);
  snareSlider.getValueLabel().align(ControlP5.RIGHT, ControlP5.CENTER).setPaddingX(10 * scale);
  
  tomSlider = cp5.addSlider("tomDensity")
    .setPosition(175 * scale, 82 * scale)
    .setSize(195 * scale, 21 * scale)
    .setRange(0.0, 1.0)
    .setValue(0.45)
    .setCaptionLabel("Tom Density")
    .setColorBackground(color(103, 0, 0))
    .setColorForeground(color(204, 0, 43))
    .setColorActive(color(204, 0, 43))
  ;
  tomSlider.getCaptionLabel().align(ControlP5.LEFT, ControlP5.CENTER).setPaddingX(10 * scale);
  tomSlider.getValueLabel().align(ControlP5.RIGHT, ControlP5.CENTER).setPaddingX(10 * scale);
  
  tonicKnob = cp5.addKnob("tonic")
    .setPosition(20 * scale, 118 * scale)
    .setRadius(30 * scale)
    .setRange(60, 71)
    .setValue(60)
    .setDragDirection(Knob.VERTICAL)
    .setCaptionLabel("Root")
    .setColorBackground(color(103, 0, 0))
    .setColorForeground(color(204, 0, 43))
    .setColorActive(color(204, 0, 43))
  ;
  tonicKnob.getCaptionLabel().align(ControlP5.CENTER, ControlP5.BOTTOM_OUTSIDE).setPaddingY(-41 * scale).setFont(new ControlFont(createFont("OpenSans-Bold.ttf", 7 * scale, true), 7 * scale));
  tonicKnob.getValueLabel().setVisible(false);
  
  rootNote = cp5.addTextlabel("rootNote")
    .setPosition(10 * scale, 145 * scale)
  ;
  rootNote.getValueLabel().align(ControlP5.CENTER, ControlP5.CENTER);

  tempoKnob = cp5.addKnob("tempo")
    .setPosition(20 * scale, 188 * scale)
    .setRadius(30 * scale)
    .setRange(30, 220)
    .setValue(120)
    .setDragDirection(Knob.VERTICAL)
    .setCaptionLabel("BPM")
    .setColorForeground(color(24, 100, 204))
    .setColorActive(color(24, 100, 204))
  ;
  tempoKnob.getCaptionLabel().align(ControlP5.CENTER, ControlP5.BOTTOM_OUTSIDE).setPaddingY(-41 * scale).setFont(new ControlFont(createFont("OpenSans-Bold.ttf", 7 * scale, true), 7 * scale));
  tempoKnob.getValueLabel().setVisible(false);
  
  tempoBPM = cp5.addTextlabel("tempoBPM")
    .setPosition(10 * scale, 215 * scale)  
  ;
  tempoBPM.getValueLabel().align(ControlP5.CENTER, ControlP5.CENTER);
}

int curTime1 = 0;
int curTime2 = 0;
void draw() {
  float sum = 0.0;
  for (int i = 0; i < notes.length; i++)
    sum += notes[i];
  for (int i = 0; i < notes.length; i++)
    probs[i] = notes[i] / sum;
      
  background(255, 255, 255);
  
  onOff1.setColorBackground(isPlaying1 ? color(204, 0, 43) : color(240, 240, 240));
  onOff1.setColorForeground(isPlaying1 ? color(204, 0, 43) : color(240, 240, 240));
  onOff1.setColorActive(isPlaying1 ? color(235, 0, 43) : color(230, 230, 230));
  onOff1.setColorLabel(isPlaying1 ? color(255, 255, 255) : color(204, 0, 43));
  
  onOff2.setColorBackground(isPlaying2 ? color(204, 0, 43) : color(240, 240, 240));
  onOff2.setColorForeground(isPlaying2 ? color(204, 0, 43) : color(240, 240, 240));
  onOff2.setColorActive(isPlaying2 ? color(235, 0, 43) : color(230, 230, 230));
  onOff2.setColorLabel(isPlaying2 ? color(255, 255, 255) : color(204, 0, 43));  
  
  scaleCycle.setCaptionLabel(scaleNames[curScale]);
  subScaleCycle.setCaptionLabel(subScaleNames[curScale][curSubScale]);
  
  rootNote.setText(noteNames[tonic % 12]);
  tempoBPM.setText(Integer.toString(tempo));
      
  for(int i = 0; i < notes.length; i++) {
    noteSliders[i].setCaptionLabel(noteNames[(tonic + scaleOffsets[curScale][curSubScale][i]) % 12]);
  }

  double legato = 0.1;
  boolean isPlaying = false;
  if(isPlaying1 && millis() > curTime1 + (60000 / (tempo * 2))) {
    prev_tone_index_1 = playMelody(prev_tone_index_1, false);
    if(isPlaying2) playMelody(prev_tone_index_1, false); //plays harmony
    curTime1 = millis();
    isPlaying = true;
  }
  else if(isPlaying1 && millis() > curTime1 + (legato*60000 / (tempo * 2)) && isPlaying) {
    Note mynote = new Note(channel, prev_tone_index_1, 100);
    myBus.sendNoteOff(mynote);
    curTime1 = millis();
    isPlaying = false;
  }
  
  
  /*if(!isPlaying1 && isPlaying2 && millis() > curTime2 + (60000 / (tempo * 2))) {
    prev_tone_index_2 = playMelody(prev_tone_index_2, false); 
    curTime2 = millis();
  }*/
}

int playMelody(int prev_tone_index, boolean isHarmony) {
  double r = Math.random();
  double xyloPlay = Math.random();
  double snarePlay = Math.random();
  double tomPlay = Math.random();
  
  double xyloThresh = Math.min(xylo[beatIndex] + xyloDensity, 1.0);
  double snareThresh = Math.min(snare[beatIndex] + snareDensity, 1.0);
  double tomThresh = Math.min(tom[beatIndex] + tomDensity, 1.0);
  
  int toneToPlay = 0;
  int toneIndex = 0;
  
  if(snarePlay <= snareThresh) {
    //myBus.sendNoteOn(new Note(perc_channel, snarePitchMIDI, 100));  
  }
   
  delay(2);
  if(tomPlay <= tomThresh) {
    //myBus.sendNoteOn(new Note(perc_channel, tomPitchMIDI, 100));   
  }
    
  delay(2);
  if(xyloPlay <= xyloThresh) {
    
    if(isHarmony){
      toneIndex = (prev_tone_index+2) % scaleOffsets[curScale][curSubScale].length;    
    }
    else if(r < .50){
      for(int i = 0; i < scaleOffsets[curScale][curSubScale].length; i++) {
        r -= probs[i];
        if(r < 0) {
          toneIndex = i; 
          break;      
        }
      }
    }
    else if(r < .80){
      toneIndex = (prev_tone_index+1) % scaleOffsets[curScale][curSubScale].length; 
    }    
    else{
      toneIndex = (prev_tone_index-1+scaleOffsets[curScale][curSubScale].length) % scaleOffsets[curScale][curSubScale].length; 
    }
    print(toneIndex);
    toneToPlay = tonic + scaleOffsets[curScale][curSubScale][toneIndex];
    myBus.sendNoteOn(new Note(channel, 60 + (toneToPlay % 12), velocity));       
    }      
  beatIndex = (beatIndex + 1) % measureLength;
  return toneIndex;
}

void togglePlay1() {
  isPlaying1 = !isPlaying1;
}

void togglePlay2(){
  isPlaying2 = !isPlaying2;
}

void resetArrays() {
  for(int i = 0; i < notes.length; i++) {
    cp5.remove("note"+Integer.toString(i));
  }
  int newLength = scaleOffsets[curScale][curSubScale].length;
  notes = new float[newLength];
  probs = new float[newLength];
  
  noteSliders = new Slider[notes.length];
  for(int i = 0; i < notes.length; i++) {
    noteSliders[i] = cp5.addSlider("note"+Integer.toString(i))
    .setPosition((350 - (260 / notes.length) * (notes.length - i - 1) - (260 / notes.length - 5)) * scale, 118 * scale)
    .setSize((260 / notes.length - 5) * scale, 130 * scale)
    .setRange(0.0, 1.0)
    .setValue(scaleWeights[curScale][curSubScale][i])
    .setId(i)
    .setColorForeground(color(24, 100, 204))
    .setColorActive(color(24, 100, 204))
   ;
   noteSliders[i].getCaptionLabel().align(ControlP5.CENTER, ControlP5.BOTTOM_OUTSIDE).setPaddingY(-17 * scale);
   noteSliders[i].getValueLabel().setVisible(false);
   
   notes[i] = noteSliders[i].getValue();
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

void controlEvent(ControlEvent theEvent) {
  if (theEvent.isController()) {
    if (theEvent.getName().startsWith("note")) {
      int id = theEvent.getId();
      if (id >= 0 && id < notes.length) {
        notes[id] = theEvent.getValue();
      }
    }
  }
}
