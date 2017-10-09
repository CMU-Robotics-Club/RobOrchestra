import themidibus.*; //Import midi library

MarkovChain<State> mc;
State mystate;

MidiBus myBus; //Creates a MidiBus object
int channel = 0; //set channel. 0 for speakers
int velocity = 120; //melody note volume

double legato = 0.9;

void setup(){
  
  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  myBus = new MidiBus(this, 0, 1);
  
  File myFile = new File(dataPath("MarkovTesting/canon4.mid"));
  MIDIReader reader = new MIDIReader(myFile, new int[] {1});
  mc = new MarkovChain(reader.notes, reader.transitions);
  mystate = mc.objects.get( (int) mc.objects.size()-1 );
}

void draw(){
  mystate = mc.getNext(mystate);
  int pitch = mystate.pitches[mystate.pitches.length-1];
  int len = mystate.lengths[mystate.lengths.length-1];
  Note note = new Note(channel, pitch, velocity);
  myBus.sendNoteOn(note);
  delay((int)(len*legato));
  myBus.sendNoteOff(note);
  delay((int)(len*(1-legato)));
}

//processes delay in milliseconds
void delay(int time) {
  int current = millis();
  while (millis () < current+time) Thread.yield();
}