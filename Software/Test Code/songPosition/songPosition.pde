import themidibus.*;

import processing.sound.*;
import java.io.File;
import java.lang.*;
import java.util.Arrays;
import java.util.ArrayList;
import java.io.FileInputStream;

import javax.sound.midi.MetaMessage;
import javax.sound.midi.MidiEvent;
import javax.sound.midi.MidiMessage;
import javax.sound.midi.MidiSystem;
import javax.sound.midi.Sequence;
import javax.sound.midi.ShortMessage;
import javax.sound.midi.Track;
import javax.sound.midi.InvalidMidiDataException;

public static final int NOTE_ON = 0x90;
public static final int NOTE_OFF = 0x80;
public static final String[] NOTE_NAMES = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};

MidiBus myBus;
Track[] tracks;
double mspertick;
long newTick;
long minDiff; // minimum difference in notes, in ticks (may need to be converted)
double msperbeat;
int beatspermeasure;
ArrayList<Integer> notes;
int bucketspermeasure = 16;
void setup()
{
  
  notes = new ArrayList<Integer>();
  myBus = new MidiBus(this, 0, 1);
  File myFile = new File(dataPath("WWRY.mid"));
  try
  {
    
    Sequence sequence = MidiSystem.getSequence(myFile);
    tracks = sequence.getTracks();
    mspertick = (1.0*sequence.getMicrosecondLength()/sequence.getTickLength()/1000);
    minDiff = sequence.getTickLength();
    int metaidx = 0;
    while (tracks[0].get(metaidx).getMessage() instanceof MetaMessage)
    {
      MetaMessage mm = (MetaMessage) tracks[0].get(metaidx).getMessage();
      byte[] b = mm.getMessage();
      for (int k = 0; k < b.length; k++)
      {
        System.out.format("%x ", b[k]);
      }
      System.out.println();
      if (b[1] == 0x51)
      {
        assert(b[2] == 3);
        msperbeat = (b[3] << 16 | b[4] << 8 | b[5]) / 1000.0;
        
        double a = 60000.0 / msperbeat;
        System.out.println(a);
      }
      else if (b[1] == 0x58)
      {
        beatspermeasure = b[3];
      }
      metaidx++;
    }
          
    for (int i = 1; i <= 1; i++) // go through tracks, limited to track 0 for now
    {
      System.out.println("Track " + i);
      for (int j = 0; j < tracks[i].size()/2; j++)
      {
        MidiEvent event = tracks[i].get(j);
        MidiMessage message = event.getMessage(); // get message
        if (message instanceof ShortMessage)
        {
          ShortMessage sm = (ShortMessage) message;
          if (sm.getCommand() == NOTE_ON) // note on
          {
            if (sm.getData2() > 0)
            {
              // if ShortMessage that actually sends a note, 
              int key = sm.getData1();
              int octave = (key / 12) - 1;
              newTick = event.getTick();
              //System.out.println("note " + j + " is " + key + " at timestamp " + newTick);
              double pos = ((newTick * mspertick) / msperbeat) + 10e-8;
              System.out.format("current position %f\n", pos);
              //System.out.format("milliseconds per beat %f\n", msperbeat);
              int measure = (int) (pos / beatspermeasure);
              double beat = pos % beatspermeasure;
              int buckets = (int) Math.round((pos * bucketspermeasure) / beatspermeasure);
              System.out.println(buckets + "th bucket"); 
              
              while (notes.size() < buckets)
              {
                notes.add(0);
              }
              notes.add(key);

              System.out.format("At measure %d with beat %f\n", measure, beat);
            }
            
            else
            {
              //System.out.println("Note off at timestamp " + event.getTick());
              //oldTick = newTick;
              //newTick = event.getTick();
              //newTick2 = event.getTick();
              
              ////System.out.println("Ticks elapsed: " + (newTick - oldTick));
              //if (newTick - oldTick < minDiff) minDiff = newTick - oldTick;
            }
          }

        }
      }
    }
    System.out.println("Total num of ticks is " + sequence.getTickLength());
    System.out.println("Min distance between ticks is " + minDiff);
    System.out.println(notes);
  }
  catch (InvalidMidiDataException e)
  {
    System.out.println("Bad file input");
    exit();
  }
  catch (IOException e)
  {
    println("Bad file input");
    exit();
  }
}



void draw()
{
}
