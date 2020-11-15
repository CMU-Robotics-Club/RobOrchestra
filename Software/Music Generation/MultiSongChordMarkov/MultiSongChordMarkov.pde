import themidibus.*; //Import midi library

MarkovChain<State>[] mc;
State mystate;
int songIndex;

MidiBus myBus; //Creates a MidiBus object
MidiBus compBus; //Creates a MidiBus object
int channel = 0; //set channel. 0 for speakers
int velocity = 120; //melody note volume

double legato = 0.5;
double lenmult = 1; //Note length multiplier (to speed up/slow down output)
boolean sendNoteOffCommands = true;
boolean percussionNoteOff = false;

int percussionLen = 1000; //Overwritten in setup

int chordVolume = 100;

MIDIReader_hash[] hashreader;
int precision = 20;

//Length of Markov chain states. Smaller number means more random. Really big numbers (on the order of the file size) can lead to errors
int statelength = 1; //INPUT

void setup(){
  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  myBus = new MidiBus(this, 0, 1);
  compBus = new MidiBus(this, 0, 2);
  
  //File[] myFile = {new File(dataPath("twinkle_twinkle.mid")), new File(dataPath("Despacito5.mid"))}; //INPUT
  File[] myFile = {new File(dataPath("Don't Stop Believing Melody.mid")), new File(dataPath("With Or Without You Melody (verse).mid"))}; //INPUT

  //File myFile = new File(dataPath("Despacito5.mid"));
  
  File[] chordFile = myFile;
  //chordFile = new File(dataPath("CMajChordTest.mid"));
  
  
  //MIDIReader reader = new MIDIReader(myFile, new int[]{4}, statelength);
  MIDIReader[] reader = {new MIDIReader(myFile[0], new int[]{0}, statelength), new MIDIReader(myFile[1], new int[]{0}, statelength)}; //The "1" is an INPUT (melody reader track(s) )
  
  mc = new MarkovChain[]{new MarkovChain(reader[0].states, reader[0].transitions), new MarkovChain(reader[1].states, reader[1].transitions)};
  
  songIndex = 1;
  mystate = mc[songIndex].objects.get((int)(Math.random()*mc[songIndex].objects.size()));
  
  //println(mc.objects.size());
  println(mc[0].objects);
  println(mc[1].objects);

  //TODO: Add chords back in
  hashreader = new MIDIReader_hash[] {new MIDIReader_hash(myFile[0], new int[]{0}, precision), new MIDIReader_hash(myFile[1], new int[]{0}, precision)}; //The "1" is an INPUT (melody reader track(s) )

  Object[][] timestamps = {hashreader[0].mMap.keySet().toArray(), hashreader[1].mMap.keySet().toArray()};
  Long[][] times = new Long[timestamps.length][2];
  for(int x = 0; x < timestamps.length; x++){
    times[x] = new Long[] {(Long)timestamps[x][0], (Long)timestamps[x][1]};
  }
  //Do we need this?? If so, things get ugly
  //Arrays.sort(times);
  
  
  //Get percussion beat length by iterating the Markov chain a lot to get a common length value
  /*State tempstate = mc.objects.get((int)(Math.random()*mc.objects.size()));
  for(int x = 0; x < 100; x++){
    tempstate = mc.getNext(tempstate);
  }
  percussionLen = tempstate.lengths[tempstate.lengths.length-1];
  //thread("playPercussion");/**/
}

void draw(){
  double r = Math.random();
  double switchprob = 0.1;
  if(r < switchprob){
    songIndex = 1-songIndex; //Switch songs (or try to, at least)
    println("Trying to switch songs");
  }
  
  try{
    mystate = mc[songIndex].getNext(mystate);
    if(r < switchprob){
      print("Successfully switched songs");
    }
  }
  catch(Exception e){
    //Switched songs into a non-existent state, unswitch songs and keep going
    songIndex = 1-songIndex; //Switch it back
    mystate = mc[songIndex].getNext(mystate);
    println(e);
    println("Failed to switch songs");
  }
  
  
  int pitch = mystate.pitches[mystate.pitches.length-1];
  pitch = pitch%12 + 60;
  int len = mystate.lengths[mystate.lengths.length-1];
  Note note = new Note(channel, pitch, velocity);
  ShortMessage[] chordArray;
  try{
    chordArray = hashreader[songIndex].mMap.get((mystate.starttimes[mystate.starttimes.length - 1])/precision*precision).toArray(new ShortMessage[hashreader[songIndex].mMap.get((mystate.starttimes[mystate.starttimes.length - 1])/precision*precision).size()]);
  }
  catch(Exception e){
    println(e);
    print("bad chord");
    chordArray = new ShortMessage[0];
  }
  
  PlayNoteThread t = new PlayNoteThread(note, len, sendNoteOffCommands, ChordDetection.findChord(chordArray));
  t.start();
  
  delay((int)(lenmult*mystate.delays[mystate.delays.length-1]));
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
