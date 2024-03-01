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
double lenmult = .4; //Note length multiplier (to speed up/slow down output)
boolean sendNoteOffCommands = true;

//Length of Markov chain states. Smaller number means more random. Really big numbers (on the order of the file size) can lead to errors
int stateLength = 1000  ; //INPUT

long mintimestamp = 0;
int nChannels = 0;
double mspertick;
MidiEvent[] nextevents;

void setup(){
  //Time-based or event-based? Try time-based first, shouldn't be hard to switch
  //Get next message from all channels
  //While true, check all next messages
  //If any happen now or earlier, apply them, get next next message, check it immediately
  //If out of messages, set next message to null
  //Have a stopLoop variable, default true, set to false if we're not out of messages
  
  
  
  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  myBus = new MidiBus(this, 0, 1);  
  
  //File myFile = new File(dataPath("twinkle_twinkle.mid")); //INPUT
  File myFile = new File(dataPath("pokemon_theme.mid")); //INPUT
  //File myFile = new File(dataPath("StarWarsMainTheme?.mid")); //INPUT
  //File myFile = new File(dataPath("auldlangsyne.mid")); //INPUT
  //File myFile = new File(dataPath("Undertale_-_Megalovania2.mid")); //INPUT
  
  try{
    Sequence sequence = MidiSystem.getSequence(myFile);      
    mspertick = 1.0*sequence.getMicrosecondLength()/sequence.getTickLength()/1000;
    
          
    Track[] tracks = sequence.getTracks();
    PlayChannelThread[] threads = new PlayChannelThread[tracks.length];
    
    nChannels = threads.length;
    //test David doing stuff
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
  boolean endSong = true;
  
  
}
