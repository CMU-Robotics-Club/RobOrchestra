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
  ArrayList<State> notes;
  ArrayList<State> lengths;
  ArrayList<ArrayList<State>> transitions;
  ArrayList<ArrayList<State>> transitions2;
  double mspertick;
  
  public MIDIReader(File file){
    this(file, new int[] {1});
  }
  
  //Defaults to a 1 note state and a 1 length state
  public MIDIReader(File file, int[] toRead){
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
                           transitions.get(notes.indexOf(prevNote)).add(new State(new int[] {key}, new int[] {}));
                        }
                        //Update previous note for future transitions
                        prevNote = key;
                        if(firstNote == -1)firstNote = key;
                        
                        
                        if(prevTime != -1 /*&& prevTime != timestamp*/){
                          int newLen = (int) (timestamp - prevTime);
                          newLen *= mspertick;
                          
                          if(!lengths.contains(new State(new int[] {}, new int[] {newLen})){
                           lengths.add(new State(new int[] {}, new int[] {newLen}));
                           transitions2.add(new ArrayList());
                          }
                          if(prevLen != -1){
                             transitions2.get(lengths.indexOf(prevLen)).add(new State(new int[] {}, new int[] {newLen}));
                          }
                          if(firstLen == -1){firstLen = newLen;}
                          prevLen = newLen;
                        }
                        //Update previous note for future transitions
                        prevTime = timestamp;
                      }
                      
                      String noteName = NOTE_NAMES[note];
                      int velocity = sm.getData2();
                      System.out.println("Note on, " + noteName + octave + " key=" + key + " velocity: " + velocity);
                  } else if (sm.getCommand() == NOTE_OFF) {
                      int key = sm.getData1();
                      int octave = (key / 12)-1;
                      int note = key % 12;
                      String noteName = NOTE_NAMES[note];
                      int velocity = sm.getData2();
                      System.out.println("Note off, " + noteName + octave + " key=" + key + " velocity: " + velocity);
                  } else {
                      qprint("Command:" + sm.getCommand()); //Ignore commands (not sure what those are for)
                  }
              } else {
                if(message instanceof MetaMessage){
                   byte[] data = ((MetaMessage)message).getData();
                   println("Type: " + ((MetaMessage)message).getType());
                   printArray(data);
                }
                System.out.println("Other message: " + message.getClass()); //Ignore random miscellaneous messages
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
  
  private void qprint(String toPrint){
    if(printThings){
       System.out.println(toPrint); 
    }
  }
}