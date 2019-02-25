import themidibus.*; //Import midi library
import gab.opencv.*;
import processing.video.*;
import java.awt.Rectangle;

MarkovChain<State> mc;
State mystate;
//CV conductor = new CV();
static Capture video;
static OpenCV opencv;

MidiBus myBus; //Creates a MidiBus object
MidiBus compBus; //Creates a MidiBus object
int channel = 0; //set channel. 0 for speakers
int velocity = 120; //melody note volume
int buff = 0;
int previous_time = 0;
int current_time = 0;
boolean play_trigger = true;
double[] last_three_tempos = {0,0,0};


PImage src, colorFilteredImage;
ArrayList<Contour> contours;

// <1> Set the range of Hue values for our filter
int rangeLow = 20;
int rangeHigh = 35;

int[] p1 = {0, 0};
int[] p2 = {0, 0};
int time1 = 0;
int time2 = 0;
double prevV = 0;
double currV = 0;
int beat_count = 0;
int beat_buffer = 0;
double last_beat = 0;
double curr_beat = 0;


double legato = 0.9;
double lenmult = 1; //Note length multiplier (to speed up/slow down output)
static double tempo = 0;
boolean sendNoteOffCommands = false;
boolean percussionNoteOff = false;

int percussionLen = 1000; //Overwritten in setup

int chordVolume = 100;

MIDIReader_hash hashreader;
int precision = 20;

//Length of Markov chain states. Smaller number means more random. Really big numbers (on the order of the file size) can lead to errors
int statelength = 50;

void setup(){
  video = new Capture(this, 640, 480, 30);
  
  opencv = new OpenCV(this, video.width, video.height);
  
  video.start();

  contours = new ArrayList<Contour>();
  
  size(1280, 480, P2D);
  
  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  myBus = new MidiBus(this, 0, 1);
  compBus = new MidiBus(this, 0, 2);
  
  File myFile = new File(dataPath("twinkle_twinkle.mid"));
  //File myFile = new File(dataPath("Despacito5.mid"));
  
  File chordFile = myFile;
  //chordFile = new File(dataPath("CMajChordTest.mid"));
  
  
  MIDIReader reader = new MIDIReader(myFile, new int[]{1}, statelength);
  mc = new MarkovChain(reader.states, reader.transitions);
  
  mystate = mc.objects.get((int)(Math.random()*mc.objects.size()));
  println(mc.objects.size());
  
  hashreader = new MIDIReader_hash(chordFile, new int[]{1}, precision);
  
  Object[] timestamps = hashreader.mMap.keySet().toArray();
  Long[] times = new Long[timestamps.length];
  for(int x = 0; x < timestamps.length; x++){
    times[x] = (Long)timestamps[x];
  }
  Arrays.sort(times);
  
  //Get percussion beat length by iterating the Markov chain a lot to get a common length value
  State tempstate = mc.objects.get((int)(Math.random()*mc.objects.size()));
  for(int x = 0; x < 100; x++){
    tempstate = mc.getNext(tempstate);
  }
  percussionLen = tempstate.lengths[tempstate.lengths.length-1];
  //thread("playPercussion");
  previous_time = millis();
}

void draw(){
  // Read last captured frame
  if (video.available()) {
    video.read();
   
  }

  // <2> Load the new frame of our movie in to OpenCV
  opencv.loadImage(video);
  //opencv.blur(300);
  
  // Tell OpenCV to use color information
  opencv.useColor();
  opencv.blur(50);
  //opencv.blur(10);
  src = opencv.getSnapshot();
  
  // <3> Tell OpenCV to work in HSV color space.
  opencv.useColor(HSB);
  
  // <4> Copy the Hue channel of our image into 
  //     the gray channel, which we process.
  opencv.setGray(opencv.getH().clone());
  
  // <5> Filter the image based on the range of 
  //     hue values that match the object we want to track.
  opencv.inRange(rangeLow, rangeHigh);
  
  // <6> Get the processed image for reference.
  
  colorFilteredImage = opencv.getSnapshot();
  
  // <7> Find contours in our range image.
  //     Passing 'true' sorts them by descending area.
  contours = opencv.findContours(false, true);
  
  // <8> Display background images
  image(src, 0, 0);
  image(colorFilteredImage, src.width, 0);
  
  // <9> Check to make sure we've found any contours
  if (contours.size() > 0) {
    // <9> Get the first contour, which will be the largest one
    Contour biggestContour = contours.get(0);
    
    // <10> Find the bounding box of the largest contour,
    //      and hence our object.
    Rectangle r = biggestContour.getBoundingBox();
    
    // <11> Draw the bounding box of our object
    noFill(); 
    strokeWeight(2); 
    stroke(255, 0, 0);
    rect(r.x, r.y, r.width, r.height);
    
    p2[0] = p1[0];
    p2[1] = p1[1];
    time2 = time1;
    p1[0] = r.x + r.width/2;
    p1[1] = r.y + r.height/2;
    time1 = millis();
  }
  if (currV > 0.5/*.20*/){
    play_trigger = true;
  }
  prevV = currV;
  currV = velocity();
  if (play_trigger && (prevV > currV*2 && millis() > beat_buffer + 250)){
    last_beat = curr_beat;
    curr_beat = millis();
    System.out.println(curr_beat - last_beat);
    double alpha = 0.8;
    tempo = alpha*60000/((curr_beat - last_beat)) + (1-alpha)*tempo;
    System.out.println(tempo);
    //could we maybe make a way to average the tempo so it's a little more stable?
    beat_count++;
    beat_buffer = millis();
    play_trigger = false;
  }
  lenmult = 60/tempo;
  
  current_time = millis();
  if (current_time > previous_time + buff)
  {
    mystate = mc.getNext(mystate);
    int pitch = mystate.pitches[mystate.pitches.length-1];
    pitch = pitch%12 + 60;
    int len = mystate.lengths[mystate.lengths.length-1];
    Note note = new Note(channel, pitch, velocity);
    ShortMessage[] chordArray;
    try{
      chordArray = hashreader.mMap.get((mystate.starttimes[mystate.starttimes.length - 1])/precision*precision).toArray(new ShortMessage[hashreader.mMap.get((mystate.starttimes[mystate.starttimes.length - 1])/precision*precision).size()]);
    }
    catch(Exception e){
      chordArray = new ShortMessage[0];
    }
    PlayNoteThread t = new PlayNoteThread(note, len, sendNoteOffCommands, ChordDetection.findChord(chordArray));
    t.start();
    previous_time = millis();
  }
  buff = ((int)(lenmult*mystate.delays[mystate.delays.length-1]));
}

void playPercussion(){
  int percChannel = 0;
  Note snareNote = new Note(percChannel, 36, 100);
  Note bassNote = new Note(percChannel, 35, 100);
  Note tomNote = new Note(percChannel, 37, 100);
  while(true){
    
    double randomCheck = Math.random();
    
    //TODO: Instead of a deterministic or random monkey banging on the keyboard as hard as possible...
    //Try a gradual decrescendo, with a small chance of jumping back up to max volume each time? Sounds more like phrasing?
    
    if(randomCheck < 0.5) {
      myBus.sendNoteOn(snareNote);
      //myBus.sendNoteOn(bassNote);
      //myBus.sendNoteOn(tomNote);
      delay(int(percussionLen * 2 * 0.75));
      if(percussionNoteOff){
        //myBus.sendNoteOff(snareNote);
        //myBus.sendNoteOff(bassNote);
        //myBus.sendNoteOff(tomNote);
      }
      //myBus.sendNoteOn(tomNote);
      delay(int(percussionLen * 2 * 0.25));
      if(percussionNoteOff){
        //myBus.sendNoteOff(snareNote);
      }
    }
    
    else {
      myBus.sendNoteOn(snareNote);
      //myBus.sendNoteOn(bassNote);
      //myBus.sendNoteOn(tomNote);
      delay(int(percussionLen));
      if(percussionNoteOff){
        //myBus.sendNoteOff(snareNote);
        //myBus.sendNoteOff(bassNote);
        //myBus.sendNoteOff(tomNote);
      }
      myBus.sendNoteOn(tomNote);
      //delay(int(percussionLen));
      if(percussionNoteOff){
        //myBus.sendNoteOff(snareNote);
      }
    }
  }
  
}

static void printArray(int[] A){
  print("[");
  for (int x = 0; x < A.length; x++){
    print(A[x]);
    if(x < A.length-1) print(", ");
  }
  print("]");
}

//processes delay in milliseconds
void delay(int time) {
  int current = millis();
  while (millis () < current+time) Thread.yield();
}


void mousePressed() {
  color c = get(mouseX, mouseY);
  println("r: " + red(c) + " g: " + green(c) + " b: " + blue(c));
   
  int hue = int(map(hue(c), 0, 255, 0, 180));
  println("hue to detect: " + hue);
  
  rangeLow = hue - 3;
  rangeHigh = hue + 1;
}

double velocity() {
  //System.out.println(p2[0] + " " +  p3[0] + " " + p2[1] + " " + p3[1]);
  int[] v1 = {p1[0] - p2[0], p1[1] - p2[1]};
  double v1Length = Math.sqrt(Math.pow(v1[0], 2) + Math.pow(v1[1], 2));
  int time = time1 - time2;
  double velocity = v1Length/time;
  return velocity;
}
