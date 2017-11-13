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
ArrayList<ArrayList<Integer>> xylo_rhythms = new ArrayList<ArrayList<Integer>>();

MidiBus output;
String key = "D";
int xylo_channel = 1;
int noteLen = 333;    // Length of eighth note
int num_phrases = 4;

void setup() {
  
  MidiBus.list();
  System.out.println("");
  output = new MidiBus(this, 0, 1);
  
  
  
  // Generates phrases of notes for XyloBot
  xylo_phrases();
  
  
  System.out.println(rhythm());
  
  
}

void draw() {
  
  for(int i=0; i<25; i++) {
    
    int phrase = (int)(Math.random()*num_phrases);
    ArrayList<Integer> rand_pattern = xylo_patterns.get(phrase);
    
    for(int j=0; j<rand_pattern.size(); j++) {
      Note mynote = new Note(xylo_channel, rand_pattern.get(j), 100);
      
      output.sendNoteOn(mynote);
      delay(noteLen);
      output.sendNoteOff(mynote);
    }
  }
}


// Generates phrases of notes for XyloBot
void xylo_phrases(int phrase_length) {
  
  // Whole array of notes
  ArrayList<Integer> notes = new ArrayList<Integer>();
  
  int k = Arrays.asList(NOTE_NAMES).indexOf(KEY);
  
  // Adds random notes in the given key to the notes array 
  for(int i=0; i<phrase_length*num_phrases; i++) {
    notes.add((KEY_NOTES[(int)(Math.random()*8)]+k)+60);
  }
  
  // Splits up notes into (num_phrases) arrays stored in xylo_patterns
  for(int i=phrase_length; i<=notes.size(); i+=phrase_length) {  
    ArrayList<Integer> pattern = new ArrayList<Integer>();
    
    for(int j=i-phrase_length; j<i; j++) {
      pattern.add(notes.get(j));
    }
    
    xylo_patterns.add(pattern);
  }
}

ArrayList<Integer> rhythm() {
  ArrayList<Integer> rhythm_array = new ArrayList<Integer>();
  ArrayList<Integer> temp_array = new ArrayList<Integer>();
  
  temp_array.add(1);
  
  for(int i=0; i<15; i++) {
    if((int)(Math.random()*2)>0) {
      temp_array.add(0);
    }
    else { temp_array.add(1); }
  }
  
  System.out.println(temp_array);
  
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
  
  return rhythm_array;
}