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
int noteLen = 333;    // Length of eighth note
int num_phrases = 4;

void setup() {
  
  MidiBus.list();
  System.out.println("");
  output = new MidiBus(this, 0, 1);
  
  for(int i=0; i<num_phrases; i++) {
    ArrayList<Integer> temp_rhythms = new ArrayList<Integer>(); 
    
    temp_rhythms = rhythm();
    
    rhythm_array.add(temp_rhythms);
    
    // Generates phrases of notes for XyloBot
    xylo_patterns.add(xylo_phrases(temp_rhythms.size()));
  }
  
}

void draw() {
  
  for(int i=0; i<25; i++) {
    
    int phrase = (int)(Math.random()*num_phrases);
    ArrayList<Integer> rand_pattern = xylo_patterns.get(phrase);
    
    for(int j=0; j<rand_pattern.size(); j++) {
      Note mynote = new Note(xylo_channel, rand_pattern.get(j), 100);
      
      output.sendNoteOn(mynote);
      delay(noteLen * rhythm_array.get(phrase).get(j));
      output.sendNoteOff(mynote);
    }
    //delay(noteLen * 4);
  }
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