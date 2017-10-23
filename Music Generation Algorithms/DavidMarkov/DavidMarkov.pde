import themidibus.*; //Import midi library

MarkovChain<State> mc;
State mystate;

MidiBus myBus; //Creates a MidiBus object
int channel = 0; //set channel. 0 for speakers
int velocity = 120; //melody note volume

double legato = 0.9;
double lenmult = 1; //Note length multiplier (to speed up/slow down output)

int percussionLen = 1000; //Overwritten in setup

void setup(){
  
  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  myBus = new MidiBus(this, 0, 1);
  
  File myFile = new File(dataPath("MarkovTesting/canon4.mid"));
  MIDIReader reader = new MIDIReader(myFile, new int[]{1}, 10);
  mc = new MarkovChain(reader.notes, reader.transitions);
  mystate = mc.objects.get((int)(Math.random()*mc.objects.size()));
  println(mc.objects.size());
  
  //Get percussion beat length by iterating the Markov chain a lot to get a common length value
  State tempstate = mc.objects.get((int)(Math.random()*mc.objects.size()));
  for(int x = 0; x < 100; x++){
    tempstate = mc.getNext(tempstate);
  }
  percussionLen = tempstate.lengths[tempstate.lengths.length-1];
  thread("playPercussion");
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

void draw(){
  mystate = mc.getNext(mystate);
  int pitch = mystate.pitches[mystate.pitches.length-1];
  pitch = pitch%12 + 60;
  int len = mystate.lengths[mystate.lengths.length-1];
  Note note = new Note(channel, pitch, velocity);
  myBus.sendNoteOn(note);
  delay((int)(lenmult*len*legato));
  //myBus.sendNoteOff(note);
  delay((int)(lenmult*len*(1-legato)));
}

//processes delay in milliseconds
void delay(int time) {
  int current = millis();
  while (millis () < current+time) Thread.yield();
}