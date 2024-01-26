import themidibus.*; //Import midi library

MarkovChain<ChordState> mc;
ComparableIntArr mystate;

MidiBus myBus; //Creates a MidiBus object
MidiBus compBus; //Creates a MidiBus object
int channel = 0; //set channel. 0 for speakers
int velocity = 120; //melody note volume

double legato = 0.9;
double lenmult = 1; //Note length multiplier (to speed up/slow down output)
boolean sendNoteOffCommands = false;
boolean percussionNoteOff = false;

int percussionLen = 1000; //Overwritten in setup

int chordVolume = 100;
int precision = 20;

//Length of Markov chain states. Smaller number means more random. Really big numbers (on the order of the file size) can lead to errors
int statelength = 1; //INPUT

private static boolean printThings = false;

public static final int NOTE_ON = 0x90;
public static final int NOTE_OFF = 0x80;
public static final String[] NOTE_NAMES = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};

HMM<ComparableIntArr> hmm;
void setup(){
  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  myBus = new MidiBus(this, 0, 1); //Melody
  compBus = new MidiBus(this, 0, 2); //Harmony
  
  File myFile = new File(dataPath("auldlangsyne.mid")); //INPUT
  //File myFile = new File(dataPath("Despacito5.mid"));
  
  File chordFile = myFile;
  //chordFile = new File(dataPath("CMajChordTest.mid"));
  System.out.println("chordFile");
  
  MIDIReader_hash midireader_hash = new MIDIReader_hash(chordFile, new int[]{2}, precision);

  MIDIReaderPlusChords mrpc = new MIDIReaderPlusChords(myFile, new int[]{1}, 1, midireader_hash, midireader_hash.chords);
  
  hmm = new HMM<ComparableIntArr>(mrpc.chords, mrpc.transitionsToChords, mrpc.states, mrpc.transitions);

  mystate = hmm.objects.get((int)(Math.random()*hmm.objects.size()));

  ////TODO: Currently dead code, consider resurrecting
  ////Get percussion beat length by iterating the Markov chain a lot to get a common length value
  //ChordState tempstate = mc.objects.get((int)(Math.random()*mc.objects.size()));
  //for(int x = 0; x < 100; x++){
  //  tempstate = mc.getNext(tempstate);
  //}
  //percussionLen = tempstate.lengths[tempstate.lengths.length-1];
  //thread("playPercussion");
  
  
}

void draw(){
  mystate = hmm.getNext(mystate);
  State myNote = hmm.getNote(mystate);
  int chordRoot = mystate.value[0];
  int type = mystate.value[1];
  chordRoot = chordRoot%12 + 60; //Wrap to fit Xylobot
  int melodyPitch = myNote.pitches[myNote.pitches.length-1];
  if (melodyPitch == 64)
    melodyPitch = 76;
  int len = myNote.lengths[myNote.lengths.length-1];
  Note note = new Note(channel, melodyPitch, velocity);
  
  int[] myChord = {chordRoot, type};
  PlayNoteThread t = new PlayNoteThread(note, len, sendNoteOffCommands, myChord);
  t.start();
  
  delay((int)(lenmult*myNote.delays[myNote.delays.length-1]));
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
