import java.io.File;
import java.util.Arrays;

import javax.sound.midi.MetaMessage;
import javax.sound.midi.MidiEvent;
import javax.sound.midi.MidiMessage;
import javax.sound.midi.MidiSystem;
import javax.sound.midi.Sequence;
import javax.sound.midi.ShortMessage;
import javax.sound.midi.Track;

static final String KEY = "D";
static final String[] NOTE_NAMES = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};
static final int[] KEY_NOTES = {0,2,4,5,7,9,11,12};
static final int[] LENGTHS = {1,2,4,8};

void setup() {
  
  ArrayList<Integer> notes = new ArrayList<Integer>();
  ArrayList<ArrayList<Integer>> pattern_list = new ArrayList<ArrayList<Integer>>();
  ArrayList<ArrayList<Integer>> pattern_lengths = new ArrayList<ArrayList<Integer>>();
  
  int k = Arrays.asList(NOTE_NAMES).indexOf(KEY);
  
  for(int i=0; i<100; i++) {
    notes.add((KEY_NOTES[(int)(Math.random()*8)]+k)+60);
  }
  
  for(int i=10; i<notes.size(); i+=10) {  
  ArrayList<Integer> pattern = new ArrayList<Integer>();
  ArrayList<Integer> lengths = new ArrayList<Integer>();
  
    for(int j=i-10; j<i; j++) {
      pattern.add(notes.get(j));
      lengths.add(LENGTHS[(int)(Math.random())*4]);
    }
  pattern_list.add(pattern);
  pattern_lengths.add(lengths);
  }
  
  try{
    
  }
  catch(Exception e){exit();}
}