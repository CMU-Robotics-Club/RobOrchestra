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

ArrayList<ArrayList<Integer>> pattern_list = new ArrayList<ArrayList<Integer>>();

MidiBus output;
String key = "D";
int channel = 0;
int noteLen = 333;
int phrase_length = 4;
int num_phrases = 10;

void setup() {
  
  MidiBus.list();
  System.out.println("");
  output = new MidiBus(this, 0, 1);
  
  // Whole array of notes
  ArrayList<Integer> notes = new ArrayList<Integer>();
  
  int k = Arrays.asList(NOTE_NAMES).indexOf(KEY);
  
  // Adds random notes in the given key to the notes array 
  for(int i=0; i<phrase_length*num_phrases; i++) {
    notes.add((KEY_NOTES[(int)(Math.random()*8)]+k)+60);
  }
  
  // Split up notes into (num_phrases) arrays stored in pattern_list
  for(int i=phrase_length; i<=notes.size(); i+=phrase_length) {  
    ArrayList<Integer> pattern = new ArrayList<Integer>();
    
    for(int j=i-phrase_length; j<i; j++) {
      pattern.add(notes.get(j));
    }
    
    pattern_list.add(pattern);
  }
}

void draw() {
  
  for(int i=0; i<25; i++) {
    
    int phrase = (int)(Math.random()*num_phrases);
    ArrayList<Integer> rand_pattern = pattern_list.get(phrase);
    
    for(int j=0; j<phrase_length; j++) {
      Note mynote = new Note(channel, rand_pattern.get(j), 100);
      
      output.sendNoteOn(mynote);
      delay(noteLen);
      output.sendNoteOff(mynote);
    }
  }
}