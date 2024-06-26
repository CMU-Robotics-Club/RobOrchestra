//TODO: Proper note lengths and delays (currently assumes length and delay is time from note on to next note on)
//When note starts, add it to a list of active notes (yay, bufferbuffers!) and set unknown values to -1 or something else obvious
//When next note starts, set the delay
//When note ends, set the end
//Whenever the first note is complete, add it to buffer, compute Markov chain stuff then do recursion to check next note...

//TODO: use to get transitions and transitions to states

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
import javax.sound.midi.InvalidMidiDataException;



public class MIDIReaderPlusChords{
  private boolean printThings = false;

  public static final int NOTE_ON = 0x90;
  public static final int NOTE_OFF = 0x80;
  public final String[] NOTE_NAMES = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};
  
  File MIDIfile;
  ArrayList<State> states = new ArrayList<State>();
  ArrayList<ComparableIntArr> chords = new ArrayList<ComparableIntArr>();
  ArrayList<ArrayList<State>> transitions = new ArrayList<ArrayList<State>>();
  ArrayList<ArrayList<ComparableIntArr>> transitionsToChords = new ArrayList<ArrayList<ComparableIntArr>>();
  double mspertick;
  int noteCount;
  
  private ArrayList<PartialNote> activeNotes = new ArrayList<PartialNote>();
  private int[] pitchBuffer = new int[0];
  private int[] lengthBuffer = new int[0];
  private int[] delayBuffer = new int[0];
  private long[] timeBuffer = new long[0];
  private State prevState = null;
  private ArrayList<PartialNote> initialNotes = new ArrayList<PartialNote>();
  private MIDIReader_hash midireader_hash;
  private ComparableIntArr oldChord = null;
  private ComparableIntArr firstChord = null;
  //public MIDIReaderPlusChords(File file){
  //  this(file, new int[] {0}, 1, );
  //}
  
  //One state, storing stateLength notes/pitches. Assumes they overlap
  public MIDIReaderPlusChords(File file, int[] toRead, int stateLength, MIDIReader_hash mrh, ArrayList<ComparableIntArr> chordsIn){
    //chords = chordsIn;
    //for (int i = 0; i < chordsIn.size(); i++)
    //{
    //  transitions.add(new ArrayList<State>());
    //}
    noteCount = 0;
    try{
      Sequence sequence = MidiSystem.getSequence(file);
      
      mspertick = 1.0*sequence.getMicrosecondLength()/sequence.getTickLength()/1000;
      
      int trackNumber = 0;
      midireader_hash = mrh;
      Track[] tracks = sequence.getTracks();
      for(int x: toRead){
          Track track = tracks[x];
          int prevNote = -1;
          
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
                        if(prevNote != -1){
                          PartialNote p = activeNotes.get(activeNotes.indexOf(new PartialNote(prevNote)));
                          p.delay = (int)(timestamp - p.startTime);
                          p.delay*=mspertick;
                        }
                        //Check if notes finished
                        checkCompletedNotes(stateLength);
                        //Update the previous pitch
                        prevNote = key;
                        noteCount++;
                      }
                      else{
                        //Note is actually 0 velocity
                        //Compute length of whatever note stopped
                        PartialNote p = activeNotes.get(activeNotes.indexOf(new PartialNote(key)));
                        p.len = (int)(timestamp - p.startTime);
                        p.len *= mspertick;
                        checkCompletedNotes(stateLength);
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
                      p.len *= mspertick;
                      checkCompletedNotes(stateLength);
                      
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
          
          //At this point we've read the entire track. Last note should be tied up in activeNotes, everything else done
          if(activeNotes.size() > 0){
            activeNotes.get(0).delay = activeNotes.get(0).len;
            checkCompletedNotes(stateLength);
          }
          //Rerun initial notes so the piece loops
          activeNotes = new ArrayList<PartialNote>(initialNotes); //Shallow copy is fine here
          checkCompletedNotes(stateLength); //Re-process starting notes to close the loop
      }
    }
    catch(InvalidMidiDataException e){
      println("Bad file input");
      exit();
    }
    catch(IOException e){
      println("Bad file input");
      exit();
    }
  }
  
  private void checkCompletedNotes(int stateLength){
    //Process any notes that are done (have to go in order, so stop at first incomplete)
    while(activeNotes.size() != 0){
      PartialNote p = activeNotes.get(0);
      if(p.delay >= 0 && p.len >= 0){
        //Note is done; put it in buffers, and possibly state/transition arrays
        pitchBuffer = cappedAdd(pitchBuffer, p.pitch, stateLength);
        lengthBuffer = cappedAdd(lengthBuffer, p.len, stateLength);
        delayBuffer = cappedAdd(delayBuffer, p.delay, stateLength);
        timeBuffer = cappedAdd(timeBuffer, p.startTime, stateLength);
        
        //Fudge to timeout long pauses and stop simultaneous notes
        /*for(int x = 0; x < timeBuffer.length; x++){
          //if(timeBuffer[x] < 10){timeBuffer[x] = 10;}
          if(timeBuffer[x] > 1){timeBuffer[x] = 1;}
        }*/
        if(pitchBuffer.length == stateLength){
          State s = new State(pitchBuffer, lengthBuffer, delayBuffer, timeBuffer);
          long time = timeBuffer[stateLength - 1] / midireader_hash.precision * midireader_hash.precision;
          ArrayList<ShortMessage> prechord = midireader_hash.mMap.get(time);
          ComparableIntArr chord = new ComparableIntArr(ChordDetection.findChordWrapped(prechord.toArray(new ShortMessage[prechord.size()])));
          
          if(!chords.contains(chord)){
            
            chords.add(chord);
            transitions.add(new ArrayList<State>());
            transitionsToChords.add(new ArrayList<ComparableIntArr>());
          }
          if (!states.contains(s))
          {
            states.add(s);
          }
          //System.out.println(s);
          transitions.get(chords.indexOf(chord)).add(s);
          
          if (oldChord == null)
          {
              // probably not needed
             firstChord = chord;
          }
          else
          {
            //System.out.println(chords);
            //System.out.println(transitionsToChords);
            //System.out.println(oldChord);
            //System.out.println(chord);
            transitionsToChords.get(chords.indexOf(oldChord)).add(chord);
          }
          oldChord = chord;
        }
        
        //If it's one of the first notes, store it
        if(initialNotes.size() < stateLength){
          initialNotes.add(p);
        }
        
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
}
