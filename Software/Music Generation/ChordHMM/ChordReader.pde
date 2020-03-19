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
import javax.sound.midi.InvalidMidiDataException;

/*private static boolean printThings = false;

public static final int NOTE_ON = 0x90;
public static final int NOTE_OFF = 0x80;
public static final String[] NOTE_NAMES = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};/**/

public class ChordReader{
  
  File MIDIfile;
  ArrayList<ChordState> states = new ArrayList<ChordState>();
  ArrayList<ArrayList<ChordState>> transitions = new ArrayList<ArrayList<ChordState>>();
  double mspertick;
  int noteCount;
  
  //private ArrayList<PartialChord> activeNotes = new ArrayList<PartialChord>();
  private int[] rootBuffer = new int[0];
  private int[] typeBuffer = new int[0];
  private int[] lengthBuffer = new int[0];
  private int[] delayBuffer = new int[0];
  private long[] timeBuffer = new long[0];
  private ChordState prevState = null;
  private ArrayList<PartialChord> initialNotes = new ArrayList<PartialChord>();
  
  public ArrayList<ShortMessage> notesPlaying = new ArrayList<ShortMessage>();
  
  public ChordReader(File file){
    this(file, new int[] {0}, 1);
  }
  
  //One state, storing stateLength notes/pitches. Assumes they overlap
  public ChordReader(File file, int[] toRead, int stateLength){
    noteCount = 0;
    try{
      Sequence sequence = MidiSystem.getSequence(file);
      
      mspertick = 1.0*sequence.getMicrosecondLength()/sequence.getTickLength()/1000;
      
      int trackNumber = 0;
      
      Track[] tracks = sequence.getTracks();
      for(int x: toRead){
          Track track = tracks[x];
          PartialChord prevChord = new PartialChord();
          long timeThresh = 100; //These are in ticks?
          long prevTimestamp = 0;
          long currentStartTime = 0;
          
          //Any time the activeNotes change (after timeThresh after the previous change), you end the previous chord (assumed to use the current activeNotes), save the start time for the current chord
          //Then apply the change (regardless of timethresh)
          //NOTE: If staccato, we'd get an empty chord, which may not be a bad thing (does mean you'd have to double stateLength, but whatever). 
          
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
                
                  if (sm.getCommand() == NOTE_ON) {
                      if ((timestamp - prevTimestamp) > timeThresh){
                        println(timestamp - prevTimestamp);
                        updateChords(prevChord, timestamp, stateLength); //Stop previous chord
                        currentStartTime = timestamp; //Next chord starts now (but we'll figure out what it is after we update all the note changes)
                      }
                      if(sm.getData2() > 0){         
                        notesPlaying.add(sm);
                      }
                      else{
                        //It's a note off
                        notesPlaying = removeStuff(notesPlaying, sm);
                      }
                      int[] temp = ChordDetection.findChord(makeArray(notesPlaying)); //TODO: Look up syntax
                      prevChord = new PartialChord(temp[0], temp[1], currentStartTime);
                  }
                  else if(sm.getCommand() == NOTE_OFF){
                    //It's a note off
                    if ((timestamp - prevTimestamp) > timeThresh){
                      println(timestamp - prevTimestamp);
                      updateChords(prevChord, timestamp, stateLength); //Stop previous chord
                      currentStartTime = timestamp; //Next chord starts now (but we'll figure out what it is after we update all the note changes)
                    }
                    notesPlaying = removeStuff(notesPlaying, sm);
                    int[] temp = ChordDetection.findChord(makeArray(notesPlaying)); //TODO: Look up syntax
                    prevChord = new PartialChord(temp[0], temp[1], currentStartTime);
                  }
              }
              else {
                if(message instanceof MetaMessage){
                   byte[] data = ((MetaMessage)message).getData();
                   //Consider printing, then reconsider and don't
                }
              }
              prevTimestamp = timestamp;
          }
          System.out.println();
          
          //At this point we've read the entire track. Last prevChord should be some useless empty chord at the end of the piece.
          //Annoying if stacatto, but I'll ignore that case for now. For now, just ignore prevChord
          //TODO: Close the loop by rerunning the first few partialChords, stored in initialNotes
          
          //So, loop through initialNotes, add currentStartTime to their start times, then start processing stuff
          int i = 0;
          while(i < stateLength){ //NOTE: I'm using a while loop to leave open the possibility to just keep refilling initialNotes in case stateLength is bigger than the total number of chords. Note that this'll force verbatim playback, as you can find a complete instance of the piece, figure out where you are, and go from there. (Some subtleties with symmetry, but nothing major.)
            prevChord = initialNotes.get(i);
            prevChord.startTime += currentStartTime; //currentStartTime is just whenever the las chord in the piece ended (again, staccato may cause issues here...)
            updateChords(prevChord, prevChord.startTime + prevChord.len, stateLength);
            i++;
          }
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
  
  private ArrayList<ShortMessage> removeStuff(ArrayList<ShortMessage> notesPlaying, ShortMessage sm){
    int key = sm.getData1();
    for(int x = 0; x < notesPlaying.size(); x++){
      int tempkey = notesPlaying.get(x).getData1();
      if(tempkey == key){
        notesPlaying.remove(x);
        break;
      }
    }
    return notesPlaying;
  }
  
  private void updateChords(PartialChord prevchord, long currentTimestamp, int stateLength){
    //Old chord stops, gets processed if it's not nonsense
    PartialChord p = prevchord;
    
    p.len = (int)(currentTimestamp - p.startTime);
    p.delay = p.len;
      
    if(p.delay >= 0 && p.len >= 0 && p.startTime >= 0){ //Throw out silly stuff, such as the dummy prevchord we use for initialization
      //Note is done; put it in buffers, and possibly state/transition arrays
      rootBuffer = cappedAdd(rootBuffer, p.root, stateLength);
      typeBuffer = cappedAdd(typeBuffer, p.type, stateLength);
      lengthBuffer = cappedAdd(lengthBuffer, p.len, stateLength);
      delayBuffer = cappedAdd(delayBuffer, p.delay, stateLength);
      timeBuffer = cappedAdd(timeBuffer, p.startTime, stateLength);
      
      if(rootBuffer.length == stateLength){
        ChordState s = new ChordState(rootBuffer, typeBuffer, lengthBuffer, delayBuffer, timeBuffer);
        if(prevState != null){
          transitions.get(states.indexOf(prevState)).add(s);
        }
        if(!states.contains(s)){
          states.add(s);
          transitions.add(new ArrayList<ChordState>());
        }
        prevState = s;
      }
      
      //If it's one of the first notes, store it
      if(initialNotes.size() < stateLength){
        initialNotes.add(p);
      }
    }
    
  }
  
  //TODO: This is silly, but I don't have Internet right now; there has to be a premade function for this, and this should be replaced with that
  public ShortMessage[] makeArray(ArrayList<ShortMessage> mylist){
    ShortMessage[] myarray = new ShortMessage[mylist.size()];
    for(int i = 0; i < mylist.size(); i++){
      myarray[i] = mylist.get(i);
    }
    return myarray;
  }
}
