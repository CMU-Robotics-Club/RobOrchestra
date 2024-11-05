//Partly adapted from: https://stackoverflow.com/questions/31354944/how-change-midi-file

import themidibus.*; //Import midi library

import java.lang.*;
//Import file processing stuff (from MIDIReader)
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

private static boolean printThings = true;

public static final int NOTE_ON = 0x90;
public static final int NOTE_OFF = 0x80;
public static final String[] NOTE_NAMES = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};
//End import file processing stuff (from MIDIReader)

MidiBus myBus; //Creates a MidiBus object
MidiBus compBus; //Creates a MidiBus object
int channel = 1; //set channel. 0 for speakers
int globalVolume = 50; //melody note volume

double legato = 0.5;
double lenmult = 1; //Note length multiplier (to speed up/slow down output)
boolean sendNoteOffCommands = true;

//Length of Markov chain states. Smaller number means more random. Really big numbers (on the order of the file size) can lead to errors
int stateLength = 1000  ; //INPUT

int nChannels = 0;
double mspertick;
MidiEvent[] nextevents;
long startTime;
Track[] tracks;
int[] eventIndices;

String outfilename;
File outFile;
Sequence sequence;
Sequence outsequence;

void setup(){
  //Time-based or event-based? Try time-based first, shouldn't be hard to switch
  //Get next message from all channels
  //While true, check all next messages
  //If any happen now or earlier, apply them, get next next message, check it immediately
  //If out of messages, set next message to null
  //Have a stopLoop variable, default true, set to false if we're not out of messages
  
  
  
  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  //myBus = new MidiBus(this, 1, 2);  
  
  
  try{
    String filename = "WWRY.mid";
    File myFile = new File(dataPath(filename));
    outfilename = filename.split("\\.")[0] + "_auto.mid";
    outFile = new File(dataPath(outfilename));
    sequence = MidiSystem.getSequence(myFile);      
    mspertick = (1.0*sequence.getMicrosecondLength()/sequence.getTickLength()/1000);

    tracks = sequence.getTracks();

    outsequence = new Sequence(sequence.getDivisionType(), sequence.getResolution()); //TODO fix this so tempo's correct
    outsequence.createTrack();
    outsequence.createTrack();
    
    nChannels = tracks.length;
    
    nextevents = new MidiEvent[nChannels];
    eventIndices = new int[nChannels];
    
    for (int i=0; i < tracks.length; i++) { 
          System.out.println(tracks[i].size());
          if (tracks[i].size() != 0) {
            nextevents[i] = tracks[i].get(0);
            eventIndices[i] = 0;
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
  startTime = System.currentTimeMillis();
}

void draw(){
  
  long nextTick = -1;
  int nextChannel = -1;
  MidiEvent nextevent = null;
  
  //This is the channel in the original file that we want to map to track 1 in the new file
  int rhythmTrack = 1; //TODO update this using clever Ryan code
  
  for(int i = 0; i < nChannels; i++)
  {
    if(eventIndices[i] > tracks[i].size()){
      continue; //Out of stuff on this track; skip
    }
    MidiEvent event = nextevents[i];
    
    if(nextTick == -1 || event.getTick() < nextTick){
      nextTick = event.getTick();
      nextChannel = i;
      nextevent = event;
    }
  }
  
  if(nextChannel == -1){
    //We're done; write the file and end
    try {
        MidiSystem.write(outsequence, MidiSystem.getMidiFileTypes(outsequence)[0], outFile);
    } catch (IOException e) {
        e.printStackTrace();
        System.exit(1);
    }
    print("Successfully wrote file " + outfilename);
    System.exit(0);
  }
  
  //Given that we haven't ended, add the next event to the new file, then update next events
  if(nextChannel == rhythmTrack){
    outsequence.getTracks()[1].add(nextevent);
  }
  else{
    outsequence.getTracks()[0].add(nextevent);
  }
  
  //Get the new next event
  int i = nextChannel;
  eventIndices[i]++;
  if (tracks[i].size() > eventIndices[i]) {
    nextevents[i] = tracks[i].get(eventIndices[i]);
  }
  
  println(nextTick + "/" + sequence.getTickLength());
}

private void qprint(String toPrint){
  if(printThings){
     System.out.println(toPrint); 
  }
}
