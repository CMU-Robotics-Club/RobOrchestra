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

public static class ChordDetection{
  
  //Returns a number between 0 and 11 (C is 0), for the tonic
  public static int findChord(ShortMessage[] arr, boolean major)
  {

    //println("Number of notes is: " + arr.length);
    
    int[] chordTest = new int[3];
    chordTest[0] = -1;
    chordTest[1] = -1;
    chordTest[2] = -1;
    //int[] lastResort = new int[4];
    int count = 0;
    
        
    for(int i = 0; i < arr.length; i++){
      if (arr[i].getCommand() == NOTE_ON) {
        int keyVal = arr[i].getData1();
        int note = keyVal%12;
        if(count > 2) {
          break;
        }
        if(note != chordTest[0] && note != chordTest[1]){ 
          chordTest[count] = note;
          count++;
        }
      }
    }
    
    /*for(int i = 0; i < 3; i++) {
      print(chordTest[i]);
      print(" ");
    } */
    //printArray(chordTest);
    
    //Arrays.sort(chordTest);
    //Arrays.sort(lastResort);
    if(major){
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
    }
    else{
      
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
    }    
    
   
    //println("COULDN'T CHORD");
    return -1;
  }


}