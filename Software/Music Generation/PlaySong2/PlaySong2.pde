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

long mintimestamp = 0;
int nChannels = 0;
double mspertick;
MidiEvent[] nextevents;
long startTime;
Track[] tracks;
int[] eventIndices;

void setup(){
  //Time-based or event-based? Try time-based first, shouldn't be hard to switch
  //Get next message from all channels
  //While true, check all next messages
  //If any happen now or earlier, apply them, get next next message, check it immediately
  //If out of messages, set next message to null
  //Have a stopLoop variable, default true, set to false if we're not out of messages
  
  
  
  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  myBus = new MidiBus(this, 1, 2);  
  
  //File myFile = new File(dataPath("twinkle_twinkle.mid")); //INPUT
  //File myFile = new File(dataPath("twinkle_twinkle_melody.mid")); //INPUT
  //File myFile = new File(dataPath("Megalovania.mid")); //INPUT
  //File myFile = new File(dataPath("StarWarsMainTheme?.mid")); //INPUT
  //File myFile = new File(dataPath("auldlangsyne.mid")); //INPUT
  //File myFile = new File(dataPath("jingle_bells-2.mid")); //INPUT
  File myFile = new File(dataPath("pokemon_theme.mid")); //INPUT
  //File myFile = new File(dataPath("We-Will-Rock-You maybe??.mid")); //INPUT
  //File myFile = new File(dataPath("WWRY3.mid")); //INPUT
  
  
  try{
    Sequence sequence = MidiSystem.getSequence(myFile);      
    mspertick = (1.0*sequence.getMicrosecondLength()/sequence.getTickLength()/1000);

    tracks = sequence.getTracks();

    
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
  boolean endSong = true;
  
  long millisSinceStart = (long) ((System.currentTimeMillis() - startTime)/lenmult);
  int i = 0;
  while  (i < nChannels)
  {
    MidiEvent event = nextevents[i];

    long timestamp = (long) (event.getTick() * mspertick);
    if (timestamp <= millisSinceStart && eventIndices[i] <= tracks[i].size())
    {
      qprint("@" + event.getTick() + " ");
      MidiMessage message = event.getMessage();
          if (message instanceof ShortMessage) {
              ShortMessage sm = (ShortMessage) message;
              qprint("Channel: " + sm.getChannel() + " ");
              if (sm.getCommand() == NOTE_ON) {
                  int key = sm.getData1();
                  int octave = (key / 12)-1;
                  int note = key % 12;
                  
                  Note n = new Note(sm.getChannel(), sm.getData1(), sm.getData2());
                  if(sm.getData2() > 0){ //Make sure you're not just setting the velocity to 0...
                    //key is the numerical value for the pitch
                    
                    //Add a new note for the new pitch
                    
                    myBus.sendNoteOn(n);
                  }
                  else{
                    //Note is actually 0 velocity
                    myBus.sendNoteOff(n);
                  }
                  
                  //Print stuff
                  String noteName = NOTE_NAMES[note];
                  int velocity = sm.getData2();
                  //qprint("Note on, " + noteName + octave + " key=" + key + " velocity: " + velocity);  
        } else if (sm.getCommand() == NOTE_OFF) {
                  Note n = new Note(sm.getChannel(), sm.getData1(), sm.getData2());
                  myBus.sendNoteOff(n);
                  //int key = sm.getData1();
                  //int octave = (key / 12)-1;
                  //int note = key % 12;
                  
                  ////Compute length of whatever note stopped
                  //PartialNote p = activeNotes.get(activeNotes.indexOf(new PartialNote(key)));
                  //p.len = (int)(timestamp - p.startTime);
                  //p.len *= mspertick;
                  //checkCompletedNotes(trackNumber, myBus);
                  
                  //String noteName = NOTE_NAMES[note];
                  //int velocity = sm.getData2();
                  //qprint("Note off, " + noteName + octave + " key=" + key + " velocity: " + velocity);
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
          eventIndices[i]++;
      if (tracks[i].size() > eventIndices[i]) {
            nextevents[i] = tracks[i].get(eventIndices[i]);
            endSong = false;
          }
    }
    else
    {
      i++;
    }
  }
    
 
  
  
  
  
 
          
}
  private void qprint(String toPrint){
    if(printThings){
       System.out.println(toPrint); 
    }
  }
    //test David doing stuff
  
