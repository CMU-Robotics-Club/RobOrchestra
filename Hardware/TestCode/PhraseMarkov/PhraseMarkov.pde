import java.io.File;
import java.util.Arrays;

import javax.sound.midi.MetaMessage;
import javax.sound.midi.MidiEvent;
import javax.sound.midi.MidiMessage;
import javax.sound.midi.MidiSystem;
import javax.sound.midi.Sequence;
import javax.sound.midi.ShortMessage;
import javax.sound.midi.Track;

import themidibus.*;

static final String KEY = "D";
static final String[] NOTE_NAMES = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};
static final int[] KEY_NOTES = {0,2,4,5,7,9,11,12};

ArrayList<ArrayList<Integer>> xylo_patterns = new ArrayList<ArrayList<Integer>>();
ArrayList<ArrayList<Integer>> rhythm_array = new ArrayList<ArrayList<Integer>>();

MidiBus output;
String key = "D";
int xylo_channel = 1;
int noteLen = 200;    // Length of eighth note
int num_phrases = 2;

//Length of states
int stateLength = 1;

State mystate;
MarkovChain<State> mc;

int channel = 1;
int velocity = 100;
boolean sendNoteOffCommands = true;
double lenmult = 1;
double legato = 0.9;

MidiBus myBus;

void setup() {
  
  MidiBus.list();
  System.out.println("");
  output = new MidiBus(this, 0, 1);
  myBus = new MidiBus(this, 0, 1);
  
  for(int i=0; i<num_phrases; i++) {
    ArrayList<Integer> temp_rhythms = new ArrayList<Integer>(); 
    
    temp_rhythms = rhythm();
    
    rhythm_array.add(temp_rhythms);
    
    // Generates phrases of notes for XyloBot
    xylo_patterns.add(xylo_phrases(temp_rhythms.size()));
  }
  
  State prevState = null;
  ArrayList<State> states = new ArrayList<State>();
  ArrayList<ArrayList<State>> transitions = new ArrayList<ArrayList<State>>();
  
  ArrayList<Integer> initialpitches = new ArrayList<Integer>();
  ArrayList<Integer> initiallengths = new ArrayList<Integer>();
  
  int[] pitchBuffer = new int[0];
  int[] lengthBuffer = new int[0];
  
  for(int i = 0; i < xylo_patterns.size(); i++){
    for(int j = 0; j < xylo_patterns.get(i).size(); j++){
      
      pitchBuffer = cappedAdd(pitchBuffer, xylo_patterns.get(i).get(j), stateLength);
      lengthBuffer = cappedAdd(lengthBuffer, noteLen*rhythm_array.get(i).get(j), stateLength);
      if(pitchBuffer.length == stateLength){
        State s = new State(pitchBuffer, lengthBuffer, lengthBuffer);
        if(prevState != null){
          transitions.get(states.indexOf(prevState)).add(s);
        }
        if(!states.contains(s)){
          states.add(s);
          transitions.add(new ArrayList<State>());
        }
        prevState = s;
      }
      
      //If it's one of the first notes, store it
      if(initialpitches.size() < stateLength){
        initialpitches.add(xylo_patterns.get(i).get(j));
        initiallengths.add(rhythm_array.get(i).get(j));
      }
      
    }
  }
  
  //Rerun first notes
  
  for(int i = 0; i < initialpitches.size(); i++){
    pitchBuffer = cappedAdd(pitchBuffer, initialpitches.get(i), stateLength);
    lengthBuffer = cappedAdd(lengthBuffer, noteLen*initiallengths.get(i), stateLength);
    if(pitchBuffer.length == stateLength){
      State s = new State(pitchBuffer, lengthBuffer, lengthBuffer);
      if(prevState != null){
        transitions.get(states.indexOf(prevState)).add(s);
      }
      if(!states.contains(s)){
        states.add(s);
        transitions.add(new ArrayList<State>());
      }
      prevState = s;
    }
    
  }
  
  mc = new MarkovChain(states, transitions);
  mystate = states.get(0);
}

void draw() {
  mystate = (State) mc.getNext(mystate);
  int pitch = mystate.pitches[mystate.pitches.length-1];
  pitch = pitch%12 + 60;
  int len = mystate.lengths[mystate.lengths.length-1];
  Note note = new Note(channel, pitch, velocity);
  PlayNoteThread t = new PlayNoteThread(note, len, sendNoteOffCommands);
  t.start();
  delay((int)(lenmult*mystate.delays[mystate.delays.length-1]));
  /*for(int i=0; i<25; i++) {
    
    int phrase = (int)(Math.random()*num_phrases);
    ArrayList<Integer> rand_pattern = xylo_patterns.get(phrase);
    
    for(int j=0; j<rand_pattern.size(); j++) {
      Note mynote = new Note(xylo_channel, rand_pattern.get(j), 100);
      
      output.sendNoteOn(mynote);
      delay(noteLen * rhythm_array.get(phrase).get(j));
      output.sendNoteOff(mynote);
    }
    //delay(noteLen * 4);
  }*/
}


// Generates phrases of notes
ArrayList<Integer> xylo_phrases(int phrase_length) {
  
  // Array of note pitches to be stored in xylo_patterns
  ArrayList<Integer> notes = new ArrayList<Integer>();
  
  int k = Arrays.asList(NOTE_NAMES).indexOf(KEY);
  
  // Adds random notes in the given key to the notes array 
  for(int i=0; i<phrase_length; i++) {
    notes.add((KEY_NOTES[(int)(Math.random()*8)]+k)+60);
  }
  
  // Sets last note as the tonic
  notes.set(phrase_length-1, KEY_NOTES[0]+k+60);
  
  return notes;
}

ArrayList<Integer> rhythm() {
  //Generates 4 measures of rhythms, with quarter notes and half notes, ending on a whole note?
  ArrayList<Integer> rhythm_array = new ArrayList<Integer>();
  // ArrayList<Integer> temp_array = new ArrayList<Integer>();
  
  for(int j=0; j<3; j++) {
    int rand = (int)(Math.random()*2);
    if(rand == 0) {
      rhythm_array.add(2);
      rhythm_array.add(2);
    }
    if(rand == 1) {
      rhythm_array.add(1);
      rhythm_array.add(1);
      rhythm_array.add(1);
      rhythm_array.add(1);
    }
  }
  
  rhythm_array.add(4);
  
  /*
  temp_array.add(1);
  
  for(int i=0; i<15; i++) {
    if((int)(Math.random()*4)>2) {
      temp_array.add(0);
    }
    else { temp_array.add(1); }
  }
  
  temp_array.set(15,0);
  
  int inc = 1;
  
  for(int i=1; i<16; i++) {
    if(temp_array.get(i) == 0) {
      inc++;
    } else {
      rhythm_array.add(inc);
      inc = 1;
    }
  }
  
  rhythm_array.add(inc);
  */
  
  return rhythm_array;
}


//Utility function from MIDIReader
private int[] cappedAdd(int[] array, int newval, int maxlen){
  if(array.length < maxlen){
    int[] temp = new int[array.length + 1];
    for(int x = 0; x < array.length; x++){
      temp[x] = array[x];
    }
    temp[temp.length-1] = newval;
    return temp;
  }
  else{
    return shiftArrayBack(array, newval);
  }
}

private long[] cappedAdd(long[] array, long newval, int maxlen){
  if(array.length < maxlen){
    long[] temp = new long[array.length + 1];
    for(int x = 0; x < array.length; x++){
      temp[x] = array[x];
    }
    temp[temp.length-1] = newval;
    return temp;
  }
  else{
    return shiftArrayBack(array, newval);
  }
}

private int[] shiftArrayBack(int[] array, int newval){
  for(int x = 0; x < array.length-1; x++){
    array[x] = array[x+1];
  }
  array[array.length-1] = newval;
  return array;
}

private long[] shiftArrayBack(long[] array, long newval){
  for(int x = 0; x < array.length-1; x++){
    array[x] = array[x+1];
  }
  array[array.length-1] = newval;
  return array;
}

private int[] copy(int[] A){
  int[] temp = new int[A.length];
  for(int x = 0; x < A.length; x++){
    temp[x] = A[x];
  }
  return temp;
}

private long[] copy(long[] A){
  long[] temp = new long[A.length];
  for(int x = 0; x < A.length; x++){
    temp[x] = A[x];
  }
  return temp;
}