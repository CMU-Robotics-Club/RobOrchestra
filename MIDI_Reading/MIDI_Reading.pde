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
    Sequence sequence = MidiSystem.getSequence(new File("/Users/davidneiman/RobOrchestra/MarkovTesting/Classical/Beethoven1.mid"));
    int trackNumber = 0;
    
    Track[] tracks = sequence.getTracks();
    for (int x = 0; x < tracks.length; x++) {
        Track track = tracks[x];
        
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
                    
                    if(sm.getData2() > 0){
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
    System.out.println("Finished reading input");
    
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
    double[][] transProbs = new double[notes.size()][notes.size()];
    for(int x = 0; x < notes.size(); x++){
       for(int y = 0; y < transitions.get(x).size(); y++){
           transCount[x][notes.indexOf(transitions.get(x).get(y))]++;
       }
       transProbs[x] = generateMarkov(transCount[x]);
    }
    System.out.println("Starting melody");
    
    //We now have our transition matrix transProbs
    playMelody(notes, transProbs);
  }
}

void playMelody(ArrayList<Integer> notes, double[][]T){
  Orchestra output = new Orchestra(0); //Test output port
  
  int note = notes.get((int)(Math.random()*notes.size()));
  while(true){
     note = getNextNote(note, notes, T);
     NoteMessage temp = new NoteMessage(note, 127, 0);
     output.sendMidiNote(temp);
     delay(200);
     output.sendNoteOff(temp);
  }
}

//Return the new note for Markov chaining
int getNextNote(int note, ArrayList<Integer> notes, double[][]T){
   int i = notes.indexOf(note);
   int out = -1;
   
   //Run Markov chain
   double rand = Math.random();
   for(int x = 0; x < notes.size(); x++){
      rand -= T[i][x];
      if(rand < 0){
         out = notes.get(x);
         break;
      }
   }
   
   //In the event of rounding error, just try again
   if(out == -1){
      out = getNextNote(note, notes, T); 
   }
   
   return out;
}

double[] generateMarkov(int[] tcounts){
  double total = 0;
  for(int x = 0; x < tcounts.length; x++){
     total += tcounts[x];
  }
  //Total now has the total
  double[] probs = new double[tcounts.length];
  for(int x = 0; x < tcounts.length; x++){
      probs[x] = tcounts[x]/total;
  }
  return probs;
}

//Array util

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

//Other util

//processes delay in milliseconds
void delay(int time) {
  int current = millis();
  while (millis () < current+time) Thread.yield();
}