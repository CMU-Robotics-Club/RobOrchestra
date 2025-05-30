import processing.sound.*;
import controlP5.*;
import themidibus.*;

ControlP5 cp5;
MidiBus myBus;

AudioIn in; //Raw sound input
Amplitude amp; //Get amplitudes from input

Button playNone;
Button playOne;
Button playAll;

boolean playingNone = true;
boolean playingOne = false;
boolean playingAll = false;

int scale = 2; //GUI size scale

int playNext = 60;
int playMin = 60;
int playMax = 76;

long playedLastTime = millis();
int mspernote = 500;
Slider mspernoteslider;

Textlabel amplitudeLabel;
Textlabel amplitudeMaxLabel;


ArrayList<Float> recentAmps = new ArrayList<Float>();
ArrayList<Integer> recentTimes = new ArrayList <Integer>();

void setup(){
  size(10000, 10000); //Doesn't take variables, changes window size and controlP5 responsive area
  surface.setSize(380 * scale, 278 * scale); //Takes variables, changes window size but apparently not controlP5 responsive area
  cp5 = new ControlP5(this);
  myBus = new MidiBus(this, 0, 2);
  MidiBus.list();
  
  in = new AudioIn(this, 0);
  amp = new Amplitude(this);
  in.amp(1);
  in.start();
  amp.input(in);
    
  cp5.setFont(new ControlFont(createFont("OpenSans-Bold.ttf", 9 * scale, true), 9 * scale));
  
  playNone = cp5.addButton("togglePlayNone")
    .setPosition(0 * scale, 5 * scale)
    .setSize(50 * scale, 30 * scale)
    .setCaptionLabel("PlayNone")
    .setColorBackground(color(255, 255, 255))
    .setColorForeground(color(255, 255, 255))
    .setColorActive(color(255, 255, 225))
    .setColorLabel(color(0, 0, 0)); 
  ;
  
  playOne = cp5.addButton("togglePlayOne")
    .setPosition(60 * scale, 5 * scale)
    .setSize(50 * scale, 30 * scale)
    .setCaptionLabel("PlayOne")
    .setColorBackground(color(255, 255, 255))
    .setColorForeground(color(255, 255, 255))
    .setColorActive(color(255, 255, 225))
    .setColorLabel(color(0, 0, 0)); 
  ;
  
  playAll = cp5.addButton("togglePlayAll")
    .setPosition(120 * scale, 5 * scale)
    .setSize(50 * scale, 30 * scale)
    .setCaptionLabel("PlayAll")
    .setColorBackground(color(255, 255, 255))
    .setColorForeground(color(255, 255, 255))
    .setColorActive(color(255, 255, 225))
    .setColorLabel(color(0, 0, 0)); 
  ;
  
  mspernoteslider = cp5.addSlider("mspernote")
    .setPosition(0 * scale, 75 * scale)
    .setSize(195 * scale, 21 * scale)
    .setRange(0.0, 5000.0)
    .setValue(1000)
    .setCaptionLabel("Ms Per Note")
    .setColorBackground(color(103, 0, 0))
    .setColorForeground(color(204, 0, 43))
    .setColorActive(color(204, 0, 43))
  ;
  
  amplitudeLabel = cp5.addTextlabel("amplitude")
    .setPosition(10 * scale, 100 * scale)  
  ;
  amplitudeMaxLabel = cp5.addTextlabel("RecentMaxAmplitude")
    .setPosition(10 * scale, 125 * scale)  
  ;
  
  updateButtons();
}

void draw(){
  background(127);
  updateButtons();
  
  amplitudeLabel.setText("Amplitude: " + amp.analyze());
  recentAmps.add(amp.analyze());
  recentTimes.add(millis());
  while(recentTimes.get(0) < millis() - mspernote){
    recentTimes.remove(0);
    recentAmps.remove(0);
  }
  
  int namps = recentAmps.size();
  float ampmax = -1;
  for(int i = 0; i < namps; i++){
    if(ampmax < recentAmps.get(i)) ampmax = recentAmps.get(i);
  }
  amplitudeMaxLabel.setText("Recent Max Amplitude: " + ampmax);

  
  if(millis() > playedLastTime + mspernote){
    playedLastTime = millis();
    //Stop old notes
    for(int i = playMin; i <= playMax; i++){
      myBus.sendNoteOff(new Note(0, i, 0));
    }
    
    //Start new notes  
    if(playingOne){
      playNext++;
      if(playNext > playMax) playNext = playMin;
      myBus.sendNoteOn(new Note(0, playNext, 100));
    }
    if(playingAll){
      for(int i = playMin; i <= playMax; i++){
        myBus.sendNoteOn(new Note(0, i, 100));
      }
    }
  }
}

void updateButtons(){
  playNone.setColorBackground(playingNone ? color(204, 0, 43) : color(240, 240, 240));
  playNone.setColorForeground(playingNone ? color(204, 0, 43) : color(240, 240, 240));
  playNone.setColorActive(playingNone ? color(235, 0, 43) : color(230, 230, 230));
  playNone.setColorLabel(playingNone ? color(255, 255, 255) : color(204, 0, 43));
  
  playOne.setColorBackground(playingOne ? color(204, 0, 43) : color(240, 240, 240));
  playOne.setColorForeground(playingOne ? color(204, 0, 43) : color(240, 240, 240));
  playOne.setColorActive(playingOne ? color(235, 0, 43) : color(230, 230, 230));
  playOne.setColorLabel(playingOne ? color(255, 255, 255) : color(204, 0, 43));
  
  playAll.setColorBackground(playingAll ? color(204, 0, 43) : color(240, 240, 240));
  playAll.setColorForeground(playingAll ? color(204, 0, 43) : color(240, 240, 240));
  playAll.setColorActive(playingAll ? color(235, 0, 43) : color(230, 230, 230));
  playAll.setColorLabel(playingAll ? color(255, 255, 255) : color(204, 0, 43));
}

void togglePlayNone(){
  if(!playingNone){
    playingNone = true;
    playingOne = false;
    playingAll = false;
    updateButtons();
  }
}

void togglePlayOne(){
  if(!playingOne){
    playingNone = false;
    playingOne = true;
    playingAll = false;
    updateButtons();
  }
}

void togglePlayAll(){
  if(!playingAll){
    playingNone = false;
    playingOne = false;
    playingAll = true;
    updateButtons();
  }
}
