import themidibus.*;

import processing.sound.*;
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

public static final int NOTE_ON = 0x90;
public static final int NOTE_OFF = 0x80;
public static final String[] NOTE_NAMES = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};

MidiBus myBus;
Track[] tracks;
double mspertick;
double msperbeat = 0.0;
long ticksperbeat;
long newTick;
long minDiff; // minimum difference in notes, in ticks (may need to be converted)

int beatspermeasure;
ArrayList<Integer> notes;
ArrayList<ArrayList<Integer>> notes2;
int bucketspermeasure = 16; // minDiff relative to length of a single beat in ticks

double matchconf = 10e-5;
float scale = 10;
void setup()
{
  size(1000,500);
  background(255);
  notes = new ArrayList<Integer>();
  notes2 = new ArrayList<ArrayList<Integer>>();
  myBus = new MidiBus(this, 0, 1);
  File myFile = new File(dataPath("test5.mid"));
  try
  {
    Sequence sequence = MidiSystem.getSequence(myFile);
    tracks = sequence.getTracks();
    mspertick = (1.0*sequence.getMicrosecondLength()/sequence.getTickLength()/1000);
    minDiff = sequence.getTickLength();
    minDiff = minTickDiff(sequence);
    int metaidx = 0;
    while (metaidx < tracks[0].size() && tracks[0].get(metaidx).getMessage() instanceof MetaMessage)
    {
      MetaMessage mm = (MetaMessage) tracks[0].get(metaidx).getMessage();
      byte[] b = mm.getMessage();
      for (int k = 0; k < b.length; k++)
      {
        System.out.format("%x ", b[k]);
      }
      System.out.println();
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
        System.out.println("msperbeat : " + msperbeat);
        double a = 60000.0 / msperbeat; // convert to beats per minute
        
        System.out.println("BPM: " + a);
      }
      else if (b[1] == 0x58) // 0x58 == time signature 
      {
        beatspermeasure = b[3]; // 4th byte is the numerator of the time signature
      }
      metaidx++;
    }
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
    }
    
    
    ticksperbeat = (long) (msperbeat / mspertick);
    Sypstem.out.println("TICKS PER BEAT " + ticksperbeat);
    System.out.println("min tick diff: " + minDiff);
    System.out.println("subdivisions: " + (ticksperbeat / minDiff));
    //bucketspermeasure = (beatspermeasure * (int) (ticksperbeat / minDiff));
    System.out.println("buckets per measure : " + bucketspermeasure);
    
    int tracknum = 1;
    for (int i = tracknum; i < tracknum+1; i++) // go through tracks, limited to track 1 for now
    {
      System.out.println("Track " + i);
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
              int octave = (key / 12) - 1;
              newTick = event.getTick();
              int note = key % 12;
              
              //System.out.println("note " + j + " is " + key + " at timestamp " + newTick);
              double pos = ((newTick * mspertick) / msperbeat) + 10e-8; // current beat (on scale of the entire piece)
              //System.out.format("current position %f\n", pos);
              //System.out.format("milliseconds per beat %f\n", msperbeat);
              /**
              * calculate measure and beat
              */
              int measure = (int) (pos / beatspermeasure); 
              double beat = pos % beatspermeasure;
              //System.out.format("measure %d, beat %f\n", measure, beat);
              // approximate the bucket that this note belongs in
              int buckets = (int) Math.round((pos * bucketspermeasure) / beatspermeasure);
              //System.out.println(buckets + "th bucket"); 
              
              // pad the empty buckets in between
              while (notes.size() < buckets)
              {
                notes.add(0);
                
              }
              while (notes2.size() < buckets)
              {
                notes2.add(new ArrayList<Integer>());
                notes2.get(notes2.size()-1).add(0);
              }

              notes.add(key);
              if (notes2.size() == buckets)
              {
                
                notes2.add(new ArrayList<Integer>());
                notes2.get(buckets).add(key);
              }
              else
              {
                //notes.set(buckets, key);
                notes2.get(buckets).add(key);
              }
              
              
              

              //System.out.format("At measure %d with beat %f\n", measure, beat);
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
    //System.out.println("Total num of ticks is " + sequence.getTickLength());
    //System.out.println("Min distance between ticks is " + minDiff);
    //System.out.println(notes);
    //System.out.println(notes2);
    int[] notesArr = new int[notes.size()];
    for (int i = 0; i < notes.size(); i++)
      notesArr[i] = notes.get(i);
    
    int[] notes2Arr = new int[notes2.size()];
    for (int i = 0; i < notes2.size(); i++)
    {
      if (notes2.get(i).size() < 2)
        notes2Arr[i] = notes2.get(i).get(0);
      else
        notes2Arr[i] = (int) Math.round(mean(notes2.get(i)));
    }
    print(notes2);
    findPattern(notesArr);
    
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

void findPatternOld(int[] notes)
{
  System.out.println("Finding best pattern in note sequence..."); 
  double bestdiff = 0;
  int besti = 0;
  
  for(int i = 2; i < (notes.length / 2); i++)
  {
    int[] sub = sublist(notes, 0, i); // use the first i buckets as a template to check the pattern
    System.out.print("using sublist : ");
    print(sub);
    System.out.println();

    double[] pattern = norm2(sub);
    double patterndot = dot2(pattern, pattern); // this score denotes a perfect match between the pattern sequence and a test sequence
    System.out.println("dot score = " + patterndot);
    
    double avg = 0.0;
    /*
    * For each i-length sequence we can get out of the bucket list,
    * match the sequence with the candidate pattern and add the score to a sum
    */
    
    for(int j = i; j < (notes.length / i) * i; j += i)
    {
      double[] test = norm2(sublist(notes, j, j + i)); 
      
      double prod = dot2(pattern, test);
      avg += prod;
    }
    
    /**
    * average the scores and check whether it is 
    * the best matching sequence. If the difference
    * between the perfect score and the average score
    * is sufficiently close to 0 
    * (i.e. all test sequences match "perfectly"),
    * we should just break from the loop. Otherwise
    * store the score and length of the best sequence.
    */
    avg = avg / ((notes.length - i) / i);
    
    double diff = (double) abs((float) (avg - patterndot));
    System.out.println("average = " + avg + " (diff = " + diff + ")");
    if (besti == 0)
    {
      bestdiff = diff;
      besti = i;
    }
    else if (diff < bestdiff)
    {
      bestdiff = (double) abs((float) (avg - patterndot));
      besti = i;
      if (bestdiff < matchconf) break;
    
    }
  }
  
  int[] maxsub = sublist(notes, 0, besti);
  System.out.print("Best fitting sublist is ");
  print(maxsub);
  System.out.print(" with score difference " + bestdiff + ".");
}

void findPattern(int[] notes)
{
  System.out.println("Finding best pattern in note sequence..."); 
  double max = 0;
  int besti = 0;
  
  for(int i = 1; i < notes.length; i++)
  {
    double[] sub = norm2(sublist(notes, 0, notes.length - i)); // use the first i buckets as a template to check the pattern
    double[] sub2 = norm2(sublist(notes, i, notes.length));
    double score = dot2(sub, sub2);
    float div = 500;
    rect((float) i * scale, (float)(250.0-score/div), 1.0 * scale, (float) (score/div));
    
    if (score > max)
    {
       max = score;
       besti = i;
    }
  }
  
  int[] maxsub = sublist(notes, 0, besti);
  System.out.print("Best fitting sublist is ");
  print(maxsub);
  System.out.print(" with score " + max + ".");
}

void print(int[] list)
{
  if (list.length < 1) return;
  System.out.print("[");
  System.out.print(list[0]);
  for(int i = 1; i < list.length; i++)
  {
    System.out.print(", " + list[i]);
  }
  System.out.print("]");
}


void print(double[] list)
{
  if (list.length < 1) return;
  System.out.print("[");
  System.out.print(list[0]);
  for(int i = 1; i < list.length; i++)
  {
    System.out.print(", " + list[i]);
  }
  System.out.print("]");
}

// creates a subsequence of list starting at start with length (end - start)
int[] sublist(int[] list, int start, int end)
{
  int[] res = new int[end - start];
  for(int i = 0; i < end - start; i++)
  {
    res[i] = list[i + start];
  }
  return res;
  
}

// normalizes sequence values around a mean
double[] norm2(int[] sequence)
{
  double[] res = new double[sequence.length];
  
  double mean = mean(sequence);
  for (int i = 0; i < sequence.length; i++)
  {
    res[i] = sequence[i] - mean;
  }
  return res;
}

// calculates the dot product of two "vectors" (double lists)
double dot2(double[] v1, double[] v2)
{
  assert(v1.length == v2.length);
  double product = 0;
  for (int i = 0; i < v1.length; i++)
  {
    product += (v1[i] * v2[i]);
  }
  return product;
}

double mean(int[] a)
{
  double m = 0;
  int len = a.length;
  for (int i = 0; i < len; i++)
  {
    m += a[i];
  }
  m = m / (1.0 * len);
  return m;
}
double mean(ArrayList<Integer> a)
{
  double m = 0;
  int len = a.size();
  for (int i = 0; i < len; i++)
  {
    m += a.get(i);
  }
  m = m / (1.0 * len);
  return m;
}

long minTickDiff(Sequence s)
{
  Track[] tracks = s.getTracks();
  
  long minDiff = s.getTickLength();
  long altDiff = s.getTickLength();
  System.out.println("sequence length: " + minDiff);
  for (int i = 0; i < tracks.length; i++)
  {
    System.out.println("Track " + i);
    long oldTick = 0;
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
            
          }
        }
      }
    }
  }
  return minDiff;
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
