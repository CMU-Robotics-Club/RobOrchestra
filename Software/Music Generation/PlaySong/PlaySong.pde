import themidibus.*; //Import midi library

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

private static boolean printThings = false;

public static final int NOTE_ON = 0x90;
public static final int NOTE_OFF = 0x80;
public static final String[] NOTE_NAMES = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};
//End import file processing stuff (from MIDIReader)

MidiBus myBus; //Creates a MidiBus object
MidiBus compBus; //Creates a MidiBus object
int channel = 0; //set channel. 0 for speakers
int globalVolume = 50; //melody note volume

double legato = 0.5;
double lenmult = 1; //Note length multiplier (to speed up/slow down output)
boolean sendNoteOffCommands = true;

//Length of Markov chain states. Smaller number means more random. Really big numbers (on the order of the file size) can lead to errors
int stateLength = 1  ; //INPUT

long mintimestamp = 0;

void setup(){
  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  myBus = new MidiBus(this, 0, 1);
  compBus = new MidiBus(this, 0, 1);
  
  //File myFile = new File(dataPath("twinkle_twinkle.mid")); //INPUT
  File myFile = new File(dataPath("pokemon_theme.mid")); //INPUT
  
  try{
    Sequence sequence = MidiSystem.getSequence(myFile);
          
    Track[] tracks = sequence.getTracks();
    PlayChannelThread[] threads = new PlayChannelThread[tracks.length];
    
    /*for(int trackNumber = 0; trackNumber < tracks.length; trackNumber++){
        Track track = tracks[trackNumber];
      
      //TODO start thread here
      System.out.println("Track " + trackNumber + ": size = " + track.size());
      System.out.println();
      for (int i=0; i < track.size(); i++) { 
          MidiEvent event = track.get(i);
          long timestamp = event.getTick();
          MidiMessage message = event.getMessage();
          if (message instanceof ShortMessage) {
              ShortMessage sm = (ShortMessage) message;
              if (sm.getCommand() == NOTE_ON) {
                  
                  if(sm.getData2() > 0){ //Make sure you're not just setting the velocity to 0...
                    if(mintimestamp == -1 || timestamp < mintimestamp){
                      println(timestamp);
                      mintimestamp = timestamp;
                      //break;
                    }
                  }
              }
          }
      }
    }*/
    
    for(int trackNumber = 0; trackNumber < tracks.length; trackNumber++){
      threads[trackNumber] = new PlayChannelThread(myFile, trackNumber);
    }
    for(int trackNumber = 0; trackNumber < tracks.length; trackNumber++){
      threads[trackNumber].start();
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

void draw(){
  //Do nothing, we've played everything in setup
}
