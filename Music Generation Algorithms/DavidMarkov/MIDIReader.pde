//TODO: Proper note lengths and delays (currently assumes length and delay is time from note on to next note on)
//When note starts, add it to a list of active notes (yay, bufferbuffers!) and set unknown values to -1 or something else obvious
//When next note starts, set the delay
//When note ends, set the end
//Whenever the first note is complete, add it to buffer, compute Markov chain stuff then do recursion to check next note...

import java.io.File;
import java.util.Arrays;

import java.io.PrintWriter;

import javax.sound.midi.MetaMessage;
import javax.sound.midi.MidiEvent;
import javax.sound.midi.MidiMessage;
import javax.sound.midi.MidiSystem;
import javax.sound.midi.Sequence;
import javax.sound.midi.ShortMessage;
import javax.sound.midi.Track;

private static boolean printThings = false;

public static final int NOTE_ON = 0x90;
public static final int NOTE_OFF = 0x80;
public static final String[] NOTE_NAMES = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};

public class MIDIReader{
  
  File MIDIfile;
  ArrayList<State> notes = new ArrayList<State>();
  ArrayList<State> lengths = new ArrayList<State>();
  ArrayList<ArrayList<State>> transitions = new ArrayList<ArrayList<State>>();
  ArrayList<ArrayList<State>> transitions2 = new ArrayList<ArrayList<State>>();
  double mspertick;
  
  private ArrayList<TempNote> activeNotes = new ArrayList<TempNote>();
  
  public MIDIReader(File file){
    this(file, new int[] {0});
  }
  
  //Defaults to a 1 note state and a 1 length state
  public MIDIReader(File file, int[] toRead){
    try{  
      Sequence sequence = MidiSystem.getSequence(file);
      
      mspertick = 1.0*sequence.getMicrosecondLength()/sequence.getTickLength()/1000;
      
      int trackNumber = 0;
      
      Track[] tracks = sequence.getTracks();
      for(int x = 0; x < tracks.length; x++){
      //for(int x: toRead){
          Track track = tracks[x];
          int prevNote = -1;
          int prevLen = -1;
          long prevTime = -1;
          int firstNote = -1;
          int firstLen = -1;
          
          trackNumber++;
          System.out.println("Track " + trackNumber + ": size = " + track.size());
          System.out.println();
          for (int i=0; i < track.size(); i++) {
              MidiEvent event = track.get(i);
              long timestamp = event.getTick();
              qprint("@" + event.getTick() + " ");
              MidiMessage message = event.getMessage();
              if (message instanceof ShortMessage) {
                  ShortMessage sm = (ShortMessage) message;
                  qprint("Channel: " + sm.getChannel() + " ");
                  if (sm.getCommand() == NOTE_ON) {
                      int key = sm.getData1();
                      int octave = (key / 12)-1;
                      int note = key % 12;
                      
                      if(sm.getData2() > 0){ //Make sure you're not just setting the velocity to 0...
                        //key is the numerical value for the pitch
                        if(!notes.contains(new State(new int[] {key}, new int[] {}))){
                           notes.add(new State(new int[] {key}, new int[] {}));
                           transitions.add(new ArrayList());
                        }
                        if(prevNote != -1){
                           transitions.get(notes.indexOf(new State(new int[] {prevNote}, new int[] {}))).add(new State(new int[] {key}, new int[] {}));
                        }
                        //Update previous note for future transitions
                        prevNote = key;
                        if(firstNote == -1)firstNote = key;
                        
                        if(prevTime != -1 /*&& prevTime != timestamp*/){
                          int newLen = (int) (timestamp - prevTime);
                          newLen *= mspertick;
                          
                          if(!lengths.contains(new State(new int[] {}, new int[] {newLen}))){
                            lengths.add(new State(new int[] {}, new int[] {newLen}));
                            transitions2.add(new ArrayList());
                          }
                          if(prevLen != -1){
                             transitions2.get(lengths.indexOf(new State(new int[] {}, new int[] {prevLen}))).add(new State(new int[] {}, new int[] {newLen}));
                          }
                          if(firstLen == -1){firstLen = newLen;}
                          prevLen = newLen;
                          activeNotes.add(new TempNote(key, -1, -1));
                          activeNotes.get(activeNotes.indexOf(new TempNote(prevNote, -1, -1))).delay = newLen;
                          //Check for completed notes
                        }
                        //Update previous note for future transitions
                        prevTime = timestamp;
                        String noteName = NOTE_NAMES[note];
                        int velocity = sm.getData2();
                        qprint("Note on, " + noteName + octave + " key=" + key + " velocity: " + velocity);
                      }
                      else{
                        String noteName = NOTE_NAMES[note];
                        int velocity = sm.getData2();
                        qprint("Note off, " + noteName + octave + " key=" + key + " velocity: " + velocity);
                        //Stop active note with pitch key, then check if notes are done
                      }
                      
                  } else if (sm.getCommand() == NOTE_OFF) {
                      int key = sm.getData1();
                      int octave = (key / 12)-1;
                      int note = key % 12;
                      String noteName = NOTE_NAMES[note];
                      int velocity = sm.getData2();
                      qprint("Note off, " + noteName + octave + " key=" + key + " velocity: " + velocity);
                      //Stop active note with pitch key, then check if notes are done  
                } else {
                      qprint("Command:" + sm.getCommand()); //Ignore commands (not sure what those are for)
                  }
              } else {
                if(message instanceof MetaMessage){
                   byte[] data = ((MetaMessage)message).getData();
                   qprint("Type: " + ((MetaMessage)message).getType());
                }
                qprint("Other message: " + message.getClass()); //Ignore random miscellaneous messages
              }
          }
  
          System.out.println();
          
          //Map the last note to the first note
          if(firstNote != -1){
             transitions.get(notes.indexOf(prevNote)).add(new State(new int[] {firstNote}, new int[] {}));
             //This is technically not the "right" way to do this but guarantees a loop
             //I'm actually looping the length of the second-to-last note back to the first...
             transitions2.get(lengths.indexOf(prevLen)).add(new State(new int[] {}, new int[] {firstLen}));    
          }
      }
    }
    catch(Exception e){exit();}
  }
  
  //One state, storing stateLength notes/pitches. Assumes they overlap
  public MIDIReader(File file, int[] toRead, int stateLength){
    int[] pitchbuffer = new int[0];
    int[] lengthbuffer = new int[0];
    
    //Going to ignore the last note (no length measurement) and reuse the first stateLength of them
    ArrayList<Integer> firstPitches = new ArrayList<Integer>();
    ArrayList<Integer> firstLengths = new ArrayList<Integer>();
    
    try{  
      Sequence sequence = MidiSystem.getSequence(file);
      
      mspertick = 1.0*sequence.getMicrosecondLength()/sequence.getTickLength()/1000;
      
      int trackNumber = 0;
      
      Track[] tracks = sequence.getTracks();
      for(int x: toRead){
          Track track = tracks[x];
          int prevNote = -1;
          int prevLen = -1;
          long prevTime = -1;
          int messageCount = 0;
          State prevState = new State();
          
          trackNumber++;
          System.out.println("Track " + trackNumber + ": size = " + track.size());
          System.out.println();
          for (int i=0; i < track.size(); i++) { 
              MidiEvent event = track.get(i);
              long timestamp = event.getTick();
              qprint("@" + event.getTick() + " ");
              MidiMessage message = event.getMessage();
              if (message instanceof ShortMessage) {
                  ShortMessage sm = (ShortMessage) message;
                  qprint("Channel: " + sm.getChannel() + " ");
                  if (sm.getCommand() == NOTE_ON) {
                      int key = sm.getData1();
                      int octave = (key / 12)-1;
                      int note = key % 12;
                      if(prevNote != -1){
                        pitchbuffer = cappedAdd(pitchbuffer, prevNote, stateLength); //Off by 1 because lengths
                      }
                      
                      if(firstPitches.size() < stateLength){
                        firstPitches.add(new Integer(key));
                      }
                      if(sm.getData2() > 0){ //Make sure you're not just setting the velocity to 0...
                        //key is the numerical value for the pitch
                        if(prevTime != -1 /*&& prevTime != timestamp*/){
                          int newLen = (int) (timestamp - prevTime);
                          newLen *= mspertick;
                          lengthbuffer = cappedAdd(lengthbuffer, newLen, stateLength);
                          if(firstLengths.size() < stateLength){
                            firstLengths.add(new Integer(newLen));
                          }
                          prevLen = newLen;
                        }
                        //Update previous note for future transitions
                        prevTime = timestamp;
                        prevNote = key;
                        
                        //Store states in arrays
                        if(pitchbuffer.length == stateLength){
                          State newState = new State(copy(pitchbuffer), copy(lengthbuffer));
                          if(!notes.contains(newState) && pitchbuffer.length == stateLength){
                            notes.add(newState);
                            transitions.add(new ArrayList<State>());
                          }
                          if(!prevState.equals(new State())){ //If we have a prevState...
                            transitions.get(notes.indexOf(prevState)).add(newState);
                          }
                          prevState = newState;
                        }
                      }
                      else{
                        //Note is actually 0 velocity; do something clever
                      }
                      
                      //Print stuff
                      String noteName = NOTE_NAMES[note];
                      int velocity = sm.getData2();
                      qprint("Note on, " + noteName + octave + " key=" + key + " velocity: " + velocity);  
            } else if (sm.getCommand() == NOTE_OFF) {
                      int key = sm.getData1();
                      int octave = (key / 12)-1;
                      int note = key % 12;
                      String noteName = NOTE_NAMES[note];
                      int velocity = sm.getData2();
                      qprint("Note off, " + noteName + octave + " key=" + key + " velocity: " + velocity);
                  } else {
                      qprint("Command:" + sm.getCommand()); //Ignore commands (not sure what those are for)
                  }
              } else {
                if(message instanceof MetaMessage){
                   byte[] data = ((MetaMessage)message).getData();
                   qprint("Type: " + ((MetaMessage)message).getType());
                }
                qprint("Other message: " + message.getClass()); //Ignore random miscellaneous messages
              }
          }
          System.out.println();
          
          //TODO: Rerun the first notes
          for(int y = 0; y < stateLength; y++){
            int key = firstPitches.get(y);
            pitchbuffer = cappedAdd(pitchbuffer, key, stateLength);
            int newLen = firstLengths.get(y);
            lengthbuffer = cappedAdd(lengthbuffer, newLen, stateLength);
            State newState = new State(copy(pitchbuffer), copy(lengthbuffer));
            if(!notes.contains(newState) && pitchbuffer.length == stateLength){
              notes.add(newState);
              transitions.add(new ArrayList<State>());
            }
            if(!prevState.equals(new State())){ //If we have a prevState...
              transitions.get(notes.indexOf(prevState)).add(newState);
            }
            prevState = newState;
          }
          
          //Copy arrays in case we disagree on which to use...
          lengths = notes;
          transitions2 = transitions;
      }
    }
    catch(Exception e){exit();}
  }
  
  private void qprint(String toPrint){
    if(printThings){
       System.out.println(toPrint); 
    }
  }
  
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
  
  private int[] copy(int[] A){
    int[] temp = new int[A.length];
    for(int x = 0; x < A.length; x++){
      temp[x] = A[x];
    }
    return temp;
  }
  
  //Pretty sure this'll modify the actual array, not just a copy.
  private int[] shiftArrayBack(int[] array, int newval){
    for(int x = 0; x < array.length-1; x++){
      array[x] = array[x+1];
    }
    array[array.length-1] = newval;
    return array;
  }
}