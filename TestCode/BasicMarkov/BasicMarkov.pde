import themidibus.*; //Import midi library

MarkovChain<State> mc;
State mystate;

MidiBus myBus; //Creates a MidiBus object
int channel = 0; //set channel. 0 for speakers
int velocity = 120; //melody note volume

double legato = 0.9;
double lenmult = 1; //Note length multiplier (to speed up/slow down output)
boolean sendNoteOffCommands = false;

int percussionLen = 1000; //Overwritten in setup

void setup(){
  
  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  myBus = new MidiBus(this, 0, 1);
  
  File myFile = new File(dataPath("pachelbel_canon.mid"));
  
  //MIDIReader reader = new MIDIReader(myFile, new int[]{0}, 1);
  //mc = new MarkovChain(reader.states, reader.transitions);
  
  //mystate = mc.objects.get((int)(Math.random()*mc.objects.size()));
  //println(mc.objects.size());
  
  MIDIReader_hash hashreader = new MIDIReader_hash(myFile, new int[]{0});
  
  Object[] timestamps = hashreader.mMap.keySet().toArray();
  Long[] times = new Long[timestamps.length];
  for(int x = 0; x < timestamps.length; x++){
    times[x] = (Long)timestamps[x];
  }
  Arrays.sort(times);
  for(int x = 0; x < times.length; x++){
    ShortMessage[] chordArray = hashreader.mMap.get(times[x]).toArray(new ShortMessage[hashreader.mMap.get(times[x]).size()]);
    println("Chord is: " + ChordDetection.findChord(chordArray, true));
  }
  
  println(times);
  
  //Get percussion beat length by iterating the Markov chain a lot to get a common length value
  /*State tempstate = mc.objects.get((int)(Math.random()*mc.objects.size()));
  for(int x = 0; x < 100; x++){
    tempstate = mc.getNext(tempstate);
  }
  percussionLen = tempstate.lengths[tempstate.lengths.length-1];
  thread("playPercussion");*/
  
  //println(mc.objects);
}

void draw(){
  /*mystate = mc.getNext(mystate);
  int pitch = mystate.pitches[mystate.pitches.length-1];
  pitch = pitch%12 + 60;
  int len = mystate.lengths[mystate.lengths.length-1];
  Note note = new Note(channel, pitch, velocity);
  PlayNoteThread t = new PlayNoteThread(note, len, sendNoteOffCommands);
  t.start();
  delay((int)(lenmult*mystate.delays[mystate.delays.length-1]));*/
}

void playPercussion(){
  int percChannel = 2;
  Note snareNote = new Note(percChannel, 36, 100);
  Note bassNote = new Note(percChannel, 35, 100);
  Note tomNote = new Note(percChannel, 37, 100);
  while(true){
    myBus.sendNoteOn(snareNote);
    myBus.sendNoteOn(bassNote);
    myBus.sendNoteOn(tomNote);
    delay(percussionLen);
    myBus.sendNoteOn(snareNote);
    delay(percussionLen);
  }
}

//processes delay in milliseconds
void delay(int time) {
  int current = millis();
  while (millis () < current+time) Thread.yield();
}