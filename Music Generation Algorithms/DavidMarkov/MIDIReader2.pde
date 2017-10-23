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

public class MIDIReader2{
  
  File MIDIfile;
  ArrayList<State> notes = new ArrayList<State>();
  ArrayList<State> lengths = new ArrayList<State>();
  ArrayList<ArrayList<State>> transitions = new ArrayList<ArrayList<State>>();
  ArrayList<ArrayList<State>> transitions2 = new ArrayList<ArrayList<State>>();
  double mspertick;
  
  private ArrayList<PartialNote> activeNotes = new ArrayList<PartialNote>();
  private int[] pitchbuffer = new int[0];
  private int[] lengthbuffer = new int[0];
  private State prevState = null;
  
  public MIDIReader2(File file){
    this(file, new int[] {0}, 1);
  }
  
  //One state, storing stateLength notes/pitches. Assumes they overlap
  public MIDIReader2(File file, int[] toRead, int stateLength){
    
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
                      
                      if(sm.getData2() > 0){ //Make sure you're not just setting the velocity to 0...
                        //key is the numerical value for the pitch
                        
                        //Add a new note for the new pitch
                        activeNotes.add(new PartialNote(key, timestamp));
                        
                        //Update the delay for the previous pitch
                        PartialNote p = activeNotes.get(activeNotes.indexOf(new PartialNote(key)));
                        p.delay = (int)(timestamp - p.startTime);
                        
                        //Check if notes finished
                        checkCompletedNotes();
                        
                        //TODO: Might need to add to starting notes; not sure where to do that...
                        
                        //Update the previous pitch
                        prevNote = key;
                        
                        /*
                        //Code for processing a note
                        //Add pitch to relevant buffers
                        //Off-by-one here because length is length of previous note
                        if(prevNote != -1){
                          pitchbuffer = cappedAdd(pitchbuffer, prevNote, stateLength); //Off by 1 because lengths
                        }
                        
                        //Store first notes so we can use them at the end to make a cycle
                        if(firstPitches.size() < stateLength){
                          firstPitches.add(new Integer(key));
                        }
                        
                        //Compute lengths
                        if(prevTime != -1){
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
                        }*/
                      }
                      else{
                        //Note is actually 0 velocity
                        //Compute length of whatever note stopped
                        PartialNote p = activeNotes.get(activeNotes.indexOf(new PartialNote(key)));
                        p.len = (int)(timestamp - p.startTime);
                        checkCompletedNotes();
                      }
                      
                      //Print stuff
                      String noteName = NOTE_NAMES[note];
                      int velocity = sm.getData2();
                      qprint("Note on, " + noteName + octave + " key=" + key + " velocity: " + velocity);  
            } else if (sm.getCommand() == NOTE_OFF) {
                      int key = sm.getData1();
                      int octave = (key / 12)-1;
                      int note = key % 12;
                      
                      //Compute length of whatever note stopped
                      PartialNote p = activeNotes.get(activeNotes.indexOf(new PartialNote(key)));
                      p.len = (int)(timestamp - p.startTime);
                      checkCompletedNotes();
                      
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
          
          
          //TODO: This needs to change
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
  
  private void checkCompletedNotes(){
    //Process any notes that are done (have to go in order, so stop at first incomplete)
    while(true){
      PartialNote p = activeNotes.get(0);
      if(p.delay >= 0 && p.len >= 0){
        //Note is done; process it
        //TODO: Process note
        
        activeNotes.remove(p);
      }
      else{
        return;
      }
    }
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