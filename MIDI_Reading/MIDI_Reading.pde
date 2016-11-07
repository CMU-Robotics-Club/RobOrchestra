//Found some code online to parse MIDI files: http://stackoverflow.com/questions/3850688/reading-midi-files-in-java
//Modifying it here to work with our processing code

import java.io.File;
import java.util.Arrays;

import javax.sound.midi.MidiEvent;
import javax.sound.midi.MidiMessage;
import javax.sound.midi.MidiSystem;
import javax.sound.midi.Sequence;
import javax.sound.midi.ShortMessage;
import javax.sound.midi.Track;


public static final int NOTE_ON = 0x90;
public static final int NOTE_OFF = 0x80;
public static final String[] NOTE_NAMES = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};

ArrayList<Integer> notes = new ArrayList();
ArrayList<ArrayList<Integer>> transitions = new ArrayList();
int prevNote = -1;

void setup() {
  try{  
    Sequence sequence = MidiSystem.getSequence(new File("/Users/davidneiman/RobOrchestra/Songs/ConcerningHobbits.mid"));
    int trackNumber = 0;
    for (Track track :  sequence.getTracks()) {
        trackNumber++;
        System.out.println("Track " + trackNumber + ": size = " + track.size());
        System.out.println();
        for (int i=0; i < track.size(); i++) { 
            MidiEvent event = track.get(i);
            System.out.print("@" + event.getTick() + " ");
            MidiMessage message = event.getMessage();
            if (message instanceof ShortMessage) {
                ShortMessage sm = (ShortMessage) message;
                System.out.print("Channel: " + sm.getChannel() + " ");
                if (sm.getCommand() == NOTE_ON) {
                    int key = sm.getData1();
                    int octave = (key / 12)-1;
                    int note = key % 12;
                    
                    //key is the numerical value for the pitch
                    if(!notes.contains(new Integer(key))){
                       notes.add(new Integer(key));
                       transitions.add(new ArrayList());
                    }
                    if(prevNote != -1){
                       transitions.get(notes.indexOf(prevNote)).add(key);
                    }
                    //Update previous note for future transitions
                    prevNote = key;
                    
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
                    //System.out.println("Command:" + sm.getCommand()); //Ignore commands (not sure what those are for)
                }
            } else {
                //System.out.println("Other message: " + message.getClass()); //Ignore random miscellaneous messages
            }
        }

        System.out.println();
    }
  }
  catch(Exception e){exit();}
  finally{
    System.out.println("Global data:");
    
    //Process the lists
    for(int x = 0; x < notes.size(); x++){
       for(int y = 1; y < notes.size(); y++){
         //Bubble-sort notes; move transitions accordingly
         if(notes.get(y) < notes.get(y-1)){
            int temp = notes.get(y);
            notes.set(y, notes.get(y-1));
            notes.set(y-1, temp);
            ArrayList templ = transitions.get(y);
            transitions.set(y, transitions.get(y-1));
            transitions.set(y-1, templ);
         }
       }
    }
    int[][] transCount = new int[notes.size()][notes.size()];
    for(int x = 0; x < notes.size(); x++){
       for(int y = 0; y < transitions.get(x).size(); y++){
           transCount[x][notes.indexOf(transitions.get(x).get(y))]++;
       }
    }
    
    println(notes);
    println(transitions.get(0));
    printArrayArray(transCount);
  }
}

void printArray(Object[] A) {
  print("{");
  for (int x = 0; x < A.length; x++) {
    print(A[x]); 
    if (x < A.length - 1) print(", ");
  }
  println("}");
}

void printArrayArray(Object[] A) {
  print("{");
  for (int x = 0; x < A.length; x++) {
    printArray(A[x]); 
    if (x < A.length - 1) print(", ");
  }
  println("}");
}