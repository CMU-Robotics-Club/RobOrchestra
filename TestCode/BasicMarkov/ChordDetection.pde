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


/*
Code for types of chords
1 - major
2 - minor
3 - dominant seventh
4 - diminished
5 - major seventh
6 - minor seventh
7 - diminished seventh
*/

public static class ChordDetection{
  
  //Returns first number between 0 and 11 (C is 0), for the tonic
  //Returns second number for chord type --> see list above
  public static int[] findChord(ShortMessage[] arr)
  {
    
    int[] chordTest = new int[4];
    chordTest[0] = -1;
    chordTest[1] = -1;
    chordTest[2] = -1;
    chordTest[3] = -1;
    int count = 0;
    
        
    for(int i = 0; i < arr.length; i++){
      if (arr[i].getCommand() == NOTE_ON) {
        int keyVal = arr[i].getData1();
        int note = keyVal%12;
        if(count > 3) {
          break;
        }
        if(note != chordTest[0] && note != chordTest[1] && note != chordTest[2]){ 
          chordTest[count] = note;
          count++;
        }
      }
    }
    
    //If no notes are detected
    if(chordTest[0] == -1) return new int[]{-1, -1};
    
    //If only one note is detected
    if(chordTest[1] == -1)
    {
      return new int[]{chordTest[0], -1}; 
    }
    
    //If two notes are detected
    if(chordTest[2] == -1)
    {
      if((chordTest[0] + 4) % 12 == chordTest[1]) return new int[]{chordTest[0], 1};
      else if((chordTest[0] + 3) % 12 == chordTest[1]) return new int[]{chordTest[0], 2};
      else if((chordTest[0] + 7) % 12 == chordTest[1]) return new int[]{chordTest[0], -1};
      else if((chordTest[0] + 10) % 12 == chordTest[1]) return new int[]{chordTest[0], 3};
      else if((chordTest[0] + 11) % 12 == chordTest[1]) return new int[]{chordTest[0], 5};
      
      else if((chordTest[1] + 4) % 12 == chordTest[0]) return new int[]{chordTest[1], 1};
      else if((chordTest[1] + 3) % 12 == chordTest[0]) return new int[]{chordTest[1], 2};
      else if((chordTest[1] + 7) % 12 == chordTest[0]) return new int[]{chordTest[1], -1};
      else if((chordTest[1] + 10) % 12 == chordTest[0]) return new int[]{chordTest[1], 3};
      else if((chordTest[1] + 11) % 12 == chordTest[0]) return new int[]{chordTest[1], 5};
    }
    
    //If three notes are detected
    if(chordTest[3] == -1)
    {
      if((chordTest[0] + 4) % 12 == chordTest[1]) return new int[]{chordTest[0], 1};
      else if((chordTest[0] + 3) % 12 == chordTest[1]) return new int[]{chordTest[0], 2};
      else if((chordTest[0] + 7) % 12 == chordTest[1]) return new int[]{chordTest[0], -1};
      else if((chordTest[0] + 10) % 12 == chordTest[1]) return new int[]{chordTest[0], 3};
      else if((chordTest[0] + 11) % 12 == chordTest[1]) return new int[]{chordTest[0], 5};
      
      if((chordTest[0] + 4) % 12 == chordTest[2]) return new int[]{chordTest[0], 1};
      else if((chordTest[0] + 3) % 12 == chordTest[2]) return new int[]{chordTest[0], 2};
      else if((chordTest[0] + 7) % 12 == chordTest[2]) return new int[]{chordTest[0], -1};
      else if((chordTest[0] + 10) % 12 == chordTest[2]) return new int[]{chordTest[0], 3};
      else if((chordTest[0] + 11) % 12 == chordTest[2]) return new int[]{chordTest[0], 5};
      
      
      if((chordTest[1] + 4) % 12 == chordTest[0]) return new int[]{chordTest[1], 1};
      else if((chordTest[1] + 3) % 12 == chordTest[0]) return new int[]{chordTest[1], 2};
      else if((chordTest[1] + 7) % 12 == chordTest[0]) return new int[]{chordTest[1], -1};
      else if((chordTest[1] + 10) % 12 == chordTest[0]) return new int[]{chordTest[1], 3};
      else if((chordTest[1] + 11) % 12 == chordTest[0]) return new int[]{chordTest[1], 5};
      
      if((chordTest[1] + 4) % 12 == chordTest[2]) return new int[]{chordTest[1], 1};
      else if((chordTest[1] + 3) % 12 == chordTest[2]) return new int[]{chordTest[1], 2};
      else if((chordTest[1] + 7) % 12 == chordTest[2]) return new int[]{chordTest[1], -1};
      else if((chordTest[1] + 10) % 12 == chordTest[2]) return new int[]{chordTest[1], 3};
      else if((chordTest[1] + 11) % 12 == chordTest[2]) return new int[]{chordTest[1], 5};
      
      
      if((chordTest[2] + 4) % 12 == chordTest[1]) return new int[]{chordTest[2], 1};
      else if((chordTest[2] + 3) % 12 == chordTest[1]) return new int[]{chordTest[2], 2};
      else if((chordTest[2] + 7) % 12 == chordTest[1]) return new int[]{chordTest[2], -1};
      else if((chordTest[2] + 10) % 12 == chordTest[1]) return new int[]{chordTest[2], 3};
      else if((chordTest[2] + 11) % 12 == chordTest[1]) return new int[]{chordTest[2], 5};
      
      if((chordTest[2] + 4) % 12 == chordTest[0]) return new int[]{chordTest[2], 1};
      else if((chordTest[2] + 3) % 12 == chordTest[0]) return new int[]{chordTest[2], 2};
      else if((chordTest[2] + 7) % 12 == chordTest[0]) return new int[]{chordTest[2], -1};
      else if((chordTest[2] + 10) % 12 == chordTest[0]) return new int[]{chordTest[2], 3};
      else if((chordTest[2] + 11) % 12 == chordTest[0]) return new int[]{chordTest[2], 5};
      
    }
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    //if(major){
      if(chordTest[2] == -1) {
        if((chordTest[0] + 4) % 12 == chordTest[1]) return chordTest[0];
        else if((chordTest[1] + 4) % 12 == chordTest[0]) return chordTest[1];
        else if((chordTest[0] + 7) % 12 == chordTest[1]) return chordTest[0];
        else if((chordTest[1] + 7) % 12 == chordTest[0]) return chordTest[1];
      }
      if(chordTest[0] == (chordTest[1] - 3) % 12 && chordTest[2] == (chordTest[0] - 4) % 12) return chordTest[2];
      else if(chordTest[0] == (chordTest[1] - 4) % 12 && chordTest[1] == (chordTest[2] - 3) % 12) return chordTest[0];
      else if(chordTest[1] == (chordTest[0] - 4) % 12 && chordTest[0] == (chordTest[2] - 3) % 12) return chordTest[1];
      else if(chordTest[2] == (chordTest[1] - 4) % 12 && chordTest[1] == (chordTest[0] - 3) % 12) return chordTest[2];
      else if(chordTest[2] == (chordTest[1] - 3) % 12 && chordTest[0] == (chordTest[2] - 4) % 12) return chordTest[0];
      else if(chordTest[2] == (chordTest[0] - 3) % 12 && chordTest[1] == (chordTest[2] - 4) % 12) return chordTest[1];
      
       /*
      else if((chordTest[0] + 7) % 12 == chordTest[1]) return chordTest[0];
      else if((chordTest[0] + 7) % 12 == chordTest[2]) return chordTest[0];
      else if((chordTest[1] + 7) % 12 == chordTest[0]) return chordTest[1];
      else if((chordTest[1] + 7) % 12 == chordTest[2]) return chordTest[1];
      else if((chordTest[2] + 7) % 12 == chordTest[0]) return chordTest[2];
      else if((chordTest[2] + 7) % 12 == chordTest[1]) return chordTest[2];
      
      else if((chordTest[0] + 4) % 12 == chordTest[1]) return chordTest[0];
      else if((chordTest[0] + 4) % 12 == chordTest[2]) return chordTest[0];
      else if((chordTest[1] + 4) % 12 == chordTest[0]) return chordTest[1];
      else if((chordTest[1] + 4) % 12 == chordTest[2]) return chordTest[1];
      else if((chordTest[2] + 4) % 12 == chordTest[0]) return chordTest[2];
      else if((chordTest[2] + 4) % 12 == chordTest[1]) return chordTest[2];*/
    //}
    //else{
      
      if(chordTest[2] == -1) {
        if((chordTest[0] + 3) % 12 == chordTest[1]) return chordTest[0];
        else if((chordTest[1] + 3) % 12 == chordTest[0]) return chordTest[1];
        else if((chordTest[0] + 7) % 12 == chordTest[1]) return chordTest[0];
        else if((chordTest[1] + 7) % 12 == chordTest[0]) return chordTest[1];
      }
      
      
      if(chordTest[0] == (chordTest[1] - 4) % 12 && chordTest[2] == (chordTest[0] - 3) % 12) return chordTest[2];
      else if(chordTest[0] == (chordTest[1] - 3) % 12 && chordTest[1] == (chordTest[2] - 4) % 12) return chordTest[0];
      else if(chordTest[1] == (chordTest[0] - 3) % 12 && chordTest[0] == (chordTest[2] - 4) % 12) return chordTest[1];
      else if(chordTest[2] == (chordTest[1] - 3) % 12 && chordTest[1] == (chordTest[0] - 4) % 12) return chordTest[2];
      else if(chordTest[2] == (chordTest[1] - 4) % 12 && chordTest[0] == (chordTest[2] - 3) % 12) return chordTest[0];
      else if(chordTest[2] == (chordTest[0] - 4) % 12 && chordTest[1] == (chordTest[2] - 33) % 12) return chordTest[1];
      
      /*
      else if((chordTest[0] + 7) % 12 == chordTest[1]) return chordTest[0];
      else if((chordTest[0] + 7) % 12 == chordTest[2]) return chordTest[0];
      else if((chordTest[1] + 7) % 12 == chordTest[0]) return chordTest[1];
      else if((chordTest[1] + 7) % 12 == chordTest[2]) return chordTest[1];
      else if((chordTest[2] + 7) % 12 == chordTest[0]) return chordTest[2];
      else if((chordTest[2] + 7) % 12 == chordTest[1]) return chordTest[2];
      
      else if((chordTest[0] + 3) % 12 == chordTest[1]) return chordTest[0];
      else if((chordTest[0] + 3) % 12 == chordTest[2]) return chordTest[0];
      else if((chordTest[1] + 3) % 12 == chordTest[0]) return chordTest[1];
      else if((chordTest[1] + 3) % 12 == chordTest[2]) return chordTest[1];
      else if((chordTest[2] + 3) % 12 == chordTest[0]) return chordTest[2];
      else if((chordTest[2] + 3) % 12 == chordTest[1]) return chordTest[2]; */
    //}    
    
   for(
   
   
    //println("COULDN'T CHORD");
    return new int[]{-1, -1};
  }


}