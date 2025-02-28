import themidibus.*;

import java.io.File;
import java.lang.*;
import java.util.*;
import java.io.FileInputStream;

import javax.sound.midi.MetaMessage;
import javax.sound.midi.MidiEvent;
import javax.sound.midi.MidiMessage;
import javax.sound.midi.MidiSystem;
import javax.sound.midi.Sequence;
import javax.sound.midi.ShortMessage;
import javax.sound.midi.Track;
import javax.sound.midi.InvalidMidiDataException;

class NoteArray
{
  public static final int NOTE_ON = 0x90;
  public static final int NOTE_OFF = 0x80;
  public final String[] NOTE_NAMES = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};

  private MidiBus myBus;
  File myFile;
  private Track[] tracks;
  private double mspertick;
  private double msperbeat = 0.0;
  private long ticksperbeat;
  private long newTick;
  private long minDiff; // minimum difference in notes, in ticks (may need to be converted)

  public float quarternotespermeasure;
  public double BPM;
  public ArrayList<ArrayList<ArrayList<Integer>>> notes;
  public ArrayList<ArrayList<Integer>> pattern;
  
  public int bucketspermeasure; // minDiff relative to length of a single beat in ticks
  
  private double matchconf = 10e-5;
  private float scale = 10;

  public NoteArray(String fileName, int bucketspermeasure)
  {
    this.bucketspermeasure = bucketspermeasure;
    myBus = new MidiBus(this, 0, 1);
    myFile = new File(dataPath(fileName));
    try
    {
      Sequence sequence = MidiSystem.getSequence(myFile);
      tracks = sequence.getTracks();
      notes = new ArrayList<ArrayList<ArrayList<Integer>>>();
      pattern = new ArrayList<ArrayList<Integer>>();
      mspertick = (1.0*sequence.getMicrosecondLength()/sequence.getTickLength()/1000);
      minDiff = sequence.getTickLength();
      int metaidx = 0;
      while (metaidx < tracks[0].size() && tracks[0].get(metaidx).getMessage() instanceof MetaMessage)
      {
        MetaMessage mm = (MetaMessage) tracks[0].get(metaidx).getMessage();
        byte[] b = mm.getMessage();
        /**
        * Interpreting MIDI messages:
        * https://www.recordingblogs.com/wiki/midi-meta-messages
        */
        
        if (b[1] == 0x51) // 0x51 == set tempo in microseconds per beat
        {
          assert(b[2] == 3); // if the meta message is set tempo, there should be 3 bytes of data
          int top = (b[3] & 0xff);
          int mid = (b[4] & 0xff);
          int bot = (b[5] & 0xff);
          msperbeat = ((top << 16) + (mid << 8) + bot) / 1000.0;
          BPM = 60000.0 / msperbeat; // convert to beats per minute
        }
        else if (b[1] == 0x58) // 0x58 == time signature 
        {
          quarternotespermeasure = b[3] * 4.0/(1 << b[4]); // 4th byte is the numerator of the time signature
          println("quarter notes per measure " + quarternotespermeasure);
        }
        metaidx++;
      }
      /*
      for (int i = 0; i < tracks.length; i++)
      {
        System.out.format("Track %d\n", i);
        int midx = 0;
        while (midx < tracks[i].size() && tracks[i].get(midx).getMessage() instanceof MetaMessage)
        {
          MetaMessage mm = (MetaMessage) tracks[i].get(midx).getMessage();
          byte[] b = mm.getMessage();
          printMetaMessage(b);
          midx++;
        }
      }*/
      
      
      int tracknum = 1;
      //for (int i = 1; i >= 0; i--)
      for (int i = 0; i < tracks.length; i++)
      {
        notes.add(new ArrayList<ArrayList<Integer>>());
        for (int j = 0; j < tracks[i].size(); j++)
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
                newTick = event.getTick();
                
                double pos = ((newTick * mspertick) / msperbeat) + 10e-8; // current beat (on scale of the entire piece)
                //System.out.format("current position %f\n", pos);
                //System.out.format("milliseconds per beat %f\n", msperbeat);
                
                /**
                * calculate measure and beat
                */
                int measure = (int) (pos / quarternotespermeasure); 
                double beat = pos % quarternotespermeasure;
                //System.out.format("measure %d, beat %f\n", measure, beat);
                
                // approximate the bucket that this note belongs in
                int buckets = (int) Math.round((pos * bucketspermeasure) / quarternotespermeasure);
                //System.out.println(buckets + "th bucket"); 
                
                // pad the empty buckets in between
                while (notes.get(i).size() < buckets)
                {
                  notes.get(i).add(new ArrayList<Integer>());
                  //notes.get(i).get(notes.get(i).size()-1).add(0);
                }
                
                if (notes.get(i).size() == buckets)
                {
                  notes.get(i).add(new ArrayList<Integer>());
                  notes.get(i).get(buckets).add(key);
                }
                else
                {
                  notes.get(i).get(buckets).add(key);
                }
              }
              else
              {
                //System.out.println("velocity 0");
              }
            }
            else if (sm.getCommand() == NOTE_OFF)
            {
              //System.out.println("note off");
            }
            
          }
        }
      }
      for (int i = 0; i < notes.size(); i++)
      {
        while (notes.get(i).size() % bucketspermeasure != 0)
        {
          notes.get(i).add(new ArrayList<Integer>());
        }
      }
      //pattern = findPattern(notes.get(1));
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

  ArrayList<ArrayList<Integer>> findPattern(ArrayList<ArrayList<Integer>> notes)
  {
    System.out.println("Finding best pattern in note sequence..."); 
    double max = 0;
    int besti = 0;

    for(int i = 1; i < notes.size(); i++)
    {
      ArrayList<ArrayList<Integer>> sub = normIntALAL(sublist(notes, 0, notes.size() - i)); // use the first i buckets as a template to check the pattern
      ArrayList<ArrayList<Integer>> sub2 = normIntALAL(sublist(notes, i, notes.size()));
      double score = dotIntALAL(sub, sub2);
      
      if (score > max)
      {
         max = score;
         besti = i;
      }
    }
    
    double max2 = -1e6;
    int besti2 = 0;
    for (int i = 0; i < notes.size() - besti; i += besti)
    {
      ArrayList<ArrayList<Integer>> rhythm = sublist(notes, i, i + besti);
      double total = 0;
      for (int j = 0; j < notes.size() - besti; j += besti)
      {
        ArrayList<ArrayList<Integer>> measure = sublist(notes, j, j + besti);
        total += dotIntALAL(rhythm, measure);
      }
      if (total > max2)
      {
        max2 = total;
        besti2 = i;
      }
    }
    return sublist(notes, besti2, besti2 + besti);
    //pattern = sublist(notes, besti2, besti2 + besti);
    //System.out.print("Best fitting sublist is ");
    //System.out.println(pattern);
    //System.out.print(" with score " + max2 + ".");
    
  }
  
  ArrayList<ArrayList<Integer>> sublist(ArrayList<ArrayList<Integer>> list, int start, int end)
  {
    ArrayList<ArrayList<Integer>> res = new ArrayList<ArrayList<Integer>>();
    for (int i = 0; i < end - start; i++)
    {
      res.add(new ArrayList<Integer>());
      for (int j = 0; j < list.get(i + start).size(); j++)
      {
        res.get(i).add(list.get(i + start).get(j));
      }
    }
    return res;
  }
  
  ArrayList<ArrayList<Integer>> normIntALAL(ArrayList<ArrayList<Integer>> seq)
  {
    ArrayList<ArrayList<Integer>> res = new ArrayList<ArrayList<Integer>>();
    int mean = (int) meanIntALAL(seq);
    
    for (int i = 0; i < seq.size(); i++)
    {
      res.add(new ArrayList<Integer>());
      if (seq.get(i).size() > 0)
      {
        for (int j = 0; j < seq.get(i).size(); j++)
        {
          res.get(i).add(seq.get(i).get(j) - mean);
        }
      }
      else
      {
        res.get(i).add(-mean);
      }
    }
    return res;
  }
  
  double dotIntALAL(ArrayList<ArrayList<Integer>> v1, ArrayList<ArrayList<Integer>> v2)
  {
    assert(v1.size() == v2.size());
    double product = 0;
    for (int i = 0; i < v1.size(); i++)
    {
      product += meanIntAL(v1.get(i)) * meanIntAL(v2.get(i));
    }
    return product;
  }
  
  double meanIntAL(ArrayList<Integer> a)
  {
    if (a.size() == 0) return 0.0;
    double m = 0;
    int len = a.size();
    for (int i = 0; i < len; i++)
    {
      m += a.get(i);
    }
    m = m / (1.0 * len);
    return m;
  }
  
  double meanIntALAL(ArrayList<ArrayList<Integer>> a)
  {
    double m = 0;
    int len = a.size();
    for (int i = 0; i < len; i++)
    {
      m += meanIntAL(a.get(i));
    }
    m = m / (1.0 * len);
    return m;
  }
  
  void printMetaMessage(byte[] b)
  {
    switch(b[1])
    {
      case 0x3:
        System.out.print("Track name: ");
        for (int i = 3; i < 3 + b[2]; i++)
        {
          System.out.format("%c", b[i]);
        }
        System.out.println();
        break;
      case 0x4:
        System.out.print("Instrument: ");
        for (int i = 3; i < 3 + b[2]; i++)
        {
          System.out.format("%c", b[i]);
        }
        System.out.println();
        break;
      case 0x51:
        int top = (b[3] & 0xff);
        int mid = (b[4] & 0xff);
        int bot = (b[5] & 0xff);
        double msperbeat = ((top << 16) + (mid << 8) + bot) / 1000.0;
        
        double a = 60000.0 / msperbeat; // convert to beats per minute
        
        System.out.println("BPM: " + a);
        break;
      case 0x58:
        int numerator = (b[3] & 0xff);
        
        System.out.println(b[4]);
        int denominator = 1 << (b[4]& 0xff);
        int tick = b[5];
        System.out.format("Time signature: %d/%d\n", numerator, denominator);
        break;
      default:
        break;
    }
  }
}
