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

String filename;
String outfilename;
File outFile;
Sequence sequence;
Sequence outsequence;

int[][] rhythmTracks = {{}, {2}, {3, 1, 14}};
boolean write = false;

//This is the channel in the original file that we want to map to track 1 in the new file
int rhythmTrack;

void setup(){
  
  try{
    filename = "SWtheme_short_auto.mid";
    File myFile = new File(dataPath(filename));
    outfilename = filename.split("\\.")[0] + "_auto.mid";
    outFile = new File(dataPath(outfilename));
    sequence = MidiSystem.getSequence(myFile);      
    mspertick = (1.0*sequence.getMicrosecondLength()/sequence.getTickLength()/1000);

    tracks = sequence.getTracks();

    outsequence = new Sequence(sequence.getDivisionType(), sequence.getResolution()); //TODO fix this so tempo's correct
    for (int i = 0; i < rhythmTracks.length; i++)
    {
      outsequence.createTrack();
    }
   
    
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
  
  rhythmTrack = midiCompress.getRhythmTrack(dataPath(filename), 32);
  //rhythmTrack = 0;
  println(rhythmTrack);
  
  if (!write) exit();
}

void draw(){
  
  long nextTick = -1;
  int nextChannel = -1;
  MidiEvent nextevent = null;
  
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
        print("Successfully wrote file " + outfilename);

    } catch (IOException e) {
        e.printStackTrace();
        System.exit(1);
    }
    System.exit(0);
  }
  
  if(nextevent != null && nextevent.getMessage() instanceof ShortMessage){
    ShortMessage sm = (ShortMessage)nextevent.getMessage();
    if(sm.getCommand() == 0xC0){
      //Get the new next event
      int i = nextChannel;
      eventIndices[i]++;
      if (tracks[i].size() > eventIndices[i]) {
        nextevents[i] = tracks[i].get(eventIndices[i]);
      }
      return;
    }
    int mychannel = -1;
    for (int i = 0; i < rhythmTracks.length; i++)
    {
      for (int j = 0; j < rhythmTracks[i].length; j++)
      {
        if (rhythmTracks[i][j] == nextChannel){
          mychannel = i;
        }
      }
    }
    try{
          sm.setMessage(sm.getCommand(), mychannel, sm.getData1(), sm.getData2());
          if (mychannel != -1)
          {
            outsequence.getTracks()[mychannel].add(nextevent);
          }
        } catch(InvalidMidiDataException e){print("oops");}
    
  }
  //Given that we haven't ended, add the next event to the new file, then update next events
  else if(nextevent != null && nextevent.getMessage() instanceof MetaMessage == false && nextChannel == rhythmTrack){
    outsequence.getTracks()[1].add(nextevent);
  }
  else{
    if (nextevent != null && nextevent.getMessage() instanceof MetaMessage){
      byte[] b = ((MetaMessage) nextevent.getMessage()).getMessage();
      if (b[1] == 0x4)
      {
        for (int i = 3; i < 2 + b[2]; i++)
        {
          b[i] = 65;
        }
      
        try
        {
          byte[] b2 = new byte[b[2]];
          for (int i = 0; i < b2.length; i++)
          {
            b2[i] = b[i + 3];
          }
          ((MetaMessage) nextevent.getMessage()).setMessage(4, b2, b[2]);
          outsequence.getTracks()[0].add(nextevent);
        }
        catch (InvalidMidiDataException e)
        {
          println(e);
        }
      }
      
    }
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
