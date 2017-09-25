//Found some code online to parse MIDI files: http://stackoverflow.com/questions/3850688/reading-midi-files-in-java
//Modifying it here to work with our processing code

import themidibus.*; //Import midi library
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

public MidiBus output;

public static final int NOTE_ON = 0x90;
public static final int NOTE_OFF = 0x80;
public static final String[] NOTE_NAMES = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};

ArrayList<Integer> notes = new ArrayList();
ArrayList<ArrayList<Integer>> transitions = new ArrayList();
ArrayList<Long> times = new ArrayList();
ArrayList<ArrayList<Long>> transitions2 = new ArrayList();

boolean printThings = true;
boolean fixedRhythm = false;

int channel = 0;

double legato = 1;
int notelen = 200;

double mspertick = -1;

void setup() {
  output = new MidiBus(this, 0, 1);
  
  try{  
    //Sequence sequence = MidiSystem.getSequence(new File("RobOrchestra/MarkovTesting/Classical/Beethoven2.mid"));
    //Sequence sequence = MidiSystem.getSequence(new File("RobOrchestra/Songs/EyeOfTheTiger.mid"));
    //Sequence sequence = MidiSystem.getSequence(new File("RobOrchestra/MarkovTesting/C Major Stuff.mid"));
    //Sequence sequence = MidiSystem.getSequence(new File("RobOrchestra/MarkovTesting/twinkle_twinkle.mid"));
    Sequence sequence = MidiSystem.getSequence(new File("RobOrchestra/MarkovTesting/canon4.mid"));
    
    mspertick = 1.0*sequence.getMicrosecondLength()/sequence.getTickLength()/1000;
    //mspertick /= 2; //Fudge to make it sound better
    
    int trackNumber = 0;
    
    Track[] tracks = sequence.getTracks();
    int[] toRead = {1};
    for(int x: toRead){
    //for (int x = 0; x < tracks.length; x++) {
        Track track = tracks[x];
        int prevNote = -1;
        long prevLen = -1;
        long prevTime = -1;
        int firstNote = -1;
        long firstLen = -1;
        
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
                      if(!notes.contains(new Integer(key))){
                         notes.add(new Integer(key));
                         transitions.add(new ArrayList());
                      }
                      if(prevNote != -1){
                         transitions.get(notes.indexOf(prevNote)).add(key);
                      }
                      //Update previous note for future transitions
                      prevNote = key;
                      if(firstNote == -1)firstNote = key;
                      
                      
                      if(prevTime != -1 /*&& prevTime != timestamp*/){
                        long newLen = timestamp - prevTime;
                        newLen *= mspertick;
                        
                        if(!times.contains(new Long(newLen))){
                         times.add(new Long(newLen));
                         transitions2.add(new ArrayList());
                        }
                        if(prevLen != -1){
                           transitions2.get(times.indexOf(prevLen)).add(newLen);
                        }
                        if(firstLen == -1)firstLen = newLen;
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
           transitions.get(notes.indexOf(prevNote)).add(firstNote);
           //This is technically not the "right" way to do this but guarantees a loop
           //I'm actually looping the length of the second-to-last note back to the first...
           transitions2.get(times.indexOf(prevLen)).add(firstLen);
           
        }
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
    for(int x = 0; x < times.size(); x++){
       for(int y = 1; y < times.size(); y++){
         //Bubble-sort notes; move transitions accordingly
         if(times.get(y) < times.get(y-1)){
            long temp = times.get(y);
            times.set(y, times.get(y-1));
            times.set(y-1, temp);
            ArrayList templ = transitions2.get(y);
            transitions2.set(y, transitions2.get(y-1));
            transitions2.set(y-1, templ);
         }
       }
    }
    
    //printArray(notes);
    //printArray(times);
    
    int[][] transCount = new int[notes.size()][notes.size()];
    double[][] transProbs = new double[notes.size()][notes.size()];
    for(int x = 0; x < notes.size(); x++){
       for(int y = 0; y < transitions.get(x).size(); y++){
           transCount[x][notes.indexOf(transitions.get(x).get(y))]++;
       }
       transProbs[x] = generateMarkov(transCount[x]);
    }
    
    long[][] transCount2 = new long[times.size()][times.size()];
    double[][] transProbs2 = new double[times.size()][times.size()];
    for(int x = 0; x < times.size(); x++){
       for(int y = 0; y < transitions2.get(x).size(); y++){
           transCount2[x][times.indexOf(transitions2.get(x).get(y))]++;
       }
       transProbs2[x] = generateMarkov(transCount2[x]);
    }
    
    MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
    System.out.println("Starting melody");
    
    //We now have our transition matrix transProbs
    //playMelody(notes, transProbs);
    
    if(fixedRhythm){
      playMelody(notes, transProbs/*, times, transProbs2*/); //4 args for rhythm, 2 for not
    }
    else{
      playMelody(notes, transProbs, times, transProbs2); //4 args for rhythm, 2 for not
    }
  }
}

void playMelody(ArrayList<Integer> notes, double[][]T){
  
  
  int note = notes.get((int)(Math.random()*notes.size()));
  while(true){
     note = getNextNote(note, notes, T);
     note = note%12 + 60;
     Note temp = new Note(channel, note, 127);
     output.sendNoteOn(temp);
     delay((int)(notelen*legato));
     //output.sendNoteOff(temp);
     delay((int)(notelen*(1-legato)));
  }
}

void playMelody(ArrayList<Integer> notes, double[][]T, ArrayList<Long> lengths, double[][]T2){
  
  int note = notes.get((int)(Math.random()*notes.size()));
  int outnote;
  long len = lengths.get((int)(Math.random()*lengths.size()));
  printArray(notes);
  printArray(lengths);
  while(true){
     note = getNextNote(note, notes, T);
     outnote = note%12 + 60;
     len = getNextLength(len, lengths, T2);
     Note temp = new Note(channel, outnote, 127);
     output.sendNoteOn(temp);
     delay((int)(len*legato));
     output.sendNoteOff(temp);
     delay((int)(len*(1-legato)));
  }
}

//Return the new note for Markov chaining
int getNextNote(int note, ArrayList<Integer> notes, double[][]T){
   int i = notes.indexOf(note);
   int out = -1;
   
   //Run Markov chain
   double rand = Math.random();
   double startrand = rand;
   for(int x = 0; x < notes.size(); x++){
      rand -= T[i][x];
      if(rand < 0){
         out = notes.get(x);
         break;
      }
   }
   
   //In the event of rounding error, just try again
   if(out == -1){
     if(Double.isNaN(rand)){
       out = notes.get((int)(Math.random()*notes.size()));
       println("No transitions; picking next note randomly");
       
     }
     else{
      println("Warning, some kind of Markov chain error?");
      out = getNextNote(note, notes, T); 
     }
   }
   
   return out;
}

//Return the new length for Markov chaining
//Variable names are awful because this is mostly copy-paste from getNextNote
long getNextLength(long note, ArrayList<Long> notes, double[][]T){
   int i = notes.indexOf(note);
   long out = -1;
   
   //Run Markov chain
   double rand = Math.random();
   double startrand = rand;
   for(int x = 0; x < notes.size(); x++){
      rand -= T[i][x];
      if(rand < 0){
         out = notes.get(x);
         break;
      }
   }
     
   if(out == -1){
     //In the event of rounding error, just try again
     if(Double.isNaN(rand)){
       out = notes.get((int)(Math.random()*notes.size()));
       println("No transitions; picking next note randomly");
     }
     else{
       println(rand);
       println(startrand);
       println("Warning, some kind of Markov chain error?");
       out = getNextLength(note, notes, T); 
     }
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

double[] generateMarkov(long[] tcounts){
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

void printArray(int[] A) {
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

void qprint(String toPrint){
  if(printThings){
     System.out.println(toPrint); 
  }
}