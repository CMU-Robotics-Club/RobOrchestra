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
-1 - not sure what chord it is
*/
public static class ChordDetection{
  static int[] prevMajorMinorArr = new int[]{-1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1, -1};
  
  //Returns first number between 0 and 11 (C is 0), for the root (-1 if no idea)
  //Returns second number for chord type --> see list above
  public static int[] findChord(ShortMessage[] arr){
    int[] out = findChordWrapped(arr);
    printArray(out);
    println();
    if(out[1] != -1){
      /*for(int x = 0; x < 12; x++){
        //prevMajorMinorArr[x] = out[1];
      }*/
      prevMajorMinorArr[out[0]] = out[1];
    }
    return out;
  }
  
  public static int[] findChordWrapped(ShortMessage[] arr)
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
    
    printArray(chordTest);
    
    //If no notes are detected
    if(chordTest[0] == -1) return new int[]{-1, -1};
    
    //If only one note is detected
    else if(chordTest[1] == -1)
    {
      return new int[]{chordTest[0], -1}; 
    }
    
    //If two notes are detected
    else if(chordTest[2] == -1)
    {
      if((chordTest[0] + 4) % 12 == chordTest[1]) return new int[]{chordTest[0], 1};
      else if((chordTest[0] + 3) % 12 == chordTest[1]) return new int[]{chordTest[0], 2};
      else if((chordTest[0] + 7) % 12 == chordTest[1]) return new int[]{chordTest[0], prevMajorMinorArr[chordTest[0]]};
      //else if((chordTest[0] + 10) % 12 == chordTest[1]) return new int[]{chordTest[0], 3};
      else if((chordTest[0] + 11) % 12 == chordTest[1]) return new int[]{chordTest[0], 5};
      else if((chordTest[0] + 6) % 12 == chordTest[1]) return new int[]{chordTest[0], 4};
      
      else if((chordTest[1] + 4) % 12 == chordTest[0]) return new int[]{chordTest[1], 1};
      else if((chordTest[1] + 3) % 12 == chordTest[0]) return new int[]{chordTest[1], 2};
      else if((chordTest[1] + 7) % 12 == chordTest[0]) return new int[]{chordTest[1], prevMajorMinorArr[chordTest[1]]};
      //else if((chordTest[1] + 10) % 12 == chordTest[0]) return new int[]{chordTest[1], 3};
      else if((chordTest[1] + 11) % 12 == chordTest[0]) return new int[]{chordTest[1], 5};
      else if((chordTest[1] + 6) % 12 == chordTest[0]) return new int[]{chordTest[1], 4};
    }
    
    //If three notes are detected
    else if(chordTest[3] == -1)
    {
      //Checking when to return index 0 as root
      if((chordTest[0] + 4) % 12 == chordTest[1])
      {
        if((chordTest[1] + 6) % 12 == chordTest[2]) return new int[]{chordTest[0], 3};
        if((chordTest[1] + 7) % 12 == chordTest[2]) return new int[]{chordTest[0], 5};
        if((chordTest[1] + 3) % 12 == chordTest[2]) return new int[]{chordTest[0], 1};
      }
      else if((chordTest[0] + 3) % 12 == chordTest[1])
      {
        if((chordTest[1] + 7) % 12 == chordTest[2]) return new int[]{chordTest[0], 6};
        if((chordTest[1] + 3) % 12 == chordTest[2]) return new int[]{chordTest[0], 4};
        if((chordTest[1] + 4) % 12 == chordTest[2]) return new int[]{chordTest[0], 2};
      }
      else if((chordTest[0] + 10) % 12 == chordTest[1]) return new int[]{chordTest[0], 3};
      else if((chordTest[0] + 11) % 12 == chordTest[1]) return new int[]{chordTest[0], 5};
      
      if((chordTest[0] + 4) % 12 == chordTest[2])
      {
        if((chordTest[2] + 6) % 12 == chordTest[1]) return new int[]{chordTest[0], 3};
        if((chordTest[2] + 7) % 12 == chordTest[1]) return new int[]{chordTest[0], 5};
        if((chordTest[2] + 3) % 12 == chordTest[1]) return new int[]{chordTest[0], 1};
      }
      else if((chordTest[0] + 3) % 12 == chordTest[2])
      {
        if((chordTest[2] + 7) % 12 == chordTest[1]) return new int[]{chordTest[0], 6};
        if((chordTest[2] + 3) % 12 == chordTest[1]) return new int[]{chordTest[0], 4};
        if((chordTest[2] + 4) % 12 == chordTest[2]) return new int[]{chordTest[0], 2};
      }
      else if((chordTest[0] + 10) % 12 == chordTest[2]) return new int[]{chordTest[0], 3};
      else if((chordTest[0] + 11) % 12 == chordTest[2]) return new int[]{chordTest[0], 5};
      
      
      
      
      
      
      //Checking when to return index 1 as root
      if((chordTest[1] + 4) % 12 == chordTest[0])
      {
        if((chordTest[0] + 6) % 12 == chordTest[2]) return new int[]{chordTest[1], 3};
        if((chordTest[0] + 7) % 12 == chordTest[2]) return new int[]{chordTest[1], 5};
        if((chordTest[0] + 3) % 12 == chordTest[2]) return new int[]{chordTest[1], 1};
      }
      else if((chordTest[1] + 3) % 12 == chordTest[0])
      {
        if((chordTest[0] + 7) % 12 == chordTest[2]) return new int[]{chordTest[1], 6};
        if((chordTest[0] + 3) % 12 == chordTest[2]) return new int[]{chordTest[1], 4};
        if((chordTest[0] + 4) % 12 == chordTest[2]) return new int[]{chordTest[1], 2};
      }
      else if((chordTest[1] + 10) % 12 == chordTest[0]) return new int[]{chordTest[1], 3};
      else if((chordTest[1] + 11) % 12 == chordTest[0]) return new int[]{chordTest[1], 5};
      
      if((chordTest[1] + 4) % 12 == chordTest[2])
      {
        if((chordTest[2] + 6) % 12 == chordTest[0]) return new int[]{chordTest[1], 3};
        if((chordTest[2] + 7) % 12 == chordTest[0]) return new int[]{chordTest[1], 5};
        if((chordTest[2] + 3) % 12 == chordTest[0]) return new int[]{chordTest[1], 1};
      }
      else if((chordTest[1] + 3) % 12 == chordTest[2])
      {
        if((chordTest[2] + 7) % 12 == chordTest[0]) return new int[]{chordTest[1], 6};
        if((chordTest[2] + 3) % 12 == chordTest[0]) return new int[]{chordTest[1], 4};
        if((chordTest[2] + 4) % 12 == chordTest[2]) return new int[]{chordTest[1], 2};
      }
      else if((chordTest[1] + 10) % 12 == chordTest[2]) return new int[]{chordTest[1], 3};
      else if((chordTest[1] + 11) % 12 == chordTest[2]) return new int[]{chordTest[1], 5};
      
      
      
      //checking when to return index 2 as root
      if((chordTest[2] + 4) % 12 == chordTest[0])
      {
        if((chordTest[0] + 6) % 12 == chordTest[1]) return new int[]{chordTest[2], 3};
        if((chordTest[0] + 7) % 12 == chordTest[1]) return new int[]{chordTest[2], 5};
        if((chordTest[0] + 3) % 12 == chordTest[1]) return new int[]{chordTest[2], 1};
      }
      else if((chordTest[2] + 3) % 12 == chordTest[0])
      {
        if((chordTest[0] + 7) % 12 == chordTest[1]) return new int[]{chordTest[2], 6};
        if((chordTest[0] + 3) % 12 == chordTest[1]) return new int[]{chordTest[2], 4};
        if((chordTest[0] + 4) % 12 == chordTest[1]) return new int[]{chordTest[2], 2};
      }
      else if((chordTest[2] + 10) % 12 == chordTest[0]) return new int[]{chordTest[2], 3};
      else if((chordTest[2] + 11) % 12 == chordTest[0]) return new int[]{chordTest[2], 5};
      
      if((chordTest[2] + 4) % 12 == chordTest[1])
      {
        //if((chordTest[1] + 6) % 12 == chordTest[0]) return new int[]{chordTest[2], 3};
        if((chordTest[1] + 7) % 12 == chordTest[0]) return new int[]{chordTest[2], 5};
        if((chordTest[1] + 3) % 12 == chordTest[0]) return new int[]{chordTest[2], 1};
      }
      else if((chordTest[2] + 3) % 12 == chordTest[1])
      {
        if((chordTest[1] + 7) % 12 == chordTest[0]) return new int[]{chordTest[2], 6};
        if((chordTest[1] + 3) % 12 == chordTest[0]) return new int[]{chordTest[2], 4};
        if((chordTest[1] + 4) % 12 == chordTest[1]) return new int[]{chordTest[2], 2};
      }
      else if((chordTest[2] + 10) % 12 == chordTest[1]) return new int[]{chordTest[2], 3};
      else if((chordTest[2] + 11) % 12 == chordTest[1]) return new int[]{chordTest[2], 5};
      
    }
    
    
    
    
    
    
    
    
    
    //If four notes are detected
    else {
      //testing if index 0 is tonic
      if((chordTest[0] + 4) % 12 == chordTest[1])
      {
        if((chordTest[1] + 6) % 12 == chordTest[2] || (chordTest[1] + 6) % 12 == chordTest[3]) return new int[]{chordTest[0], 3};
        if((chordTest[1] + 7) % 12 == chordTest[2] || (chordTest[1] + 7) % 12 == chordTest[3]) return new int[]{chordTest[0], 5};
        if((chordTest[1] + 3) % 12 == chordTest[2] || (chordTest[1] + 3) % 12 == chordTest[3]) return new int[]{chordTest[0], 1};
      }
      else if((chordTest[0] + 3) % 12 == chordTest[1])
      {
        if((chordTest[1] + 7) % 12 == chordTest[2] || (chordTest[1] + 7) % 12 == chordTest[3]) return new int[]{chordTest[0], 6};
        if((chordTest[1] + 3) % 12 == chordTest[2] || (chordTest[1] + 3) % 12 == chordTest[3]) return new int[]{chordTest[0], 4};
        if((chordTest[1] + 4) % 12 == chordTest[2] || (chordTest[1] + 4) % 12 == chordTest[3]) return new int[]{chordTest[0], 2};
      }
      else if((chordTest[0] + 10) % 12 == chordTest[1]) return new int[]{chordTest[0], 3};
      else if((chordTest[0] + 11) % 12 == chordTest[1]) return new int[]{chordTest[0], 5};
      
      if((chordTest[0] + 4) % 12 == chordTest[2])
      {
        if((chordTest[2] + 6) % 12 == chordTest[1] || (chordTest[2] + 6) % 12 == chordTest[3]) return new int[]{chordTest[0], 3};
        if((chordTest[2] + 7) % 12 == chordTest[1] || (chordTest[2] + 7) % 12 == chordTest[3]) return new int[]{chordTest[0], 5};
        if((chordTest[2] + 3) % 12 == chordTest[1] || (chordTest[2] + 3) % 12 == chordTest[3]) return new int[]{chordTest[0], 1};
      }
      else if((chordTest[0] + 3) % 12 == chordTest[2])
      {
        if((chordTest[2] + 7) % 12 == chordTest[1] || (chordTest[2] + 7) % 12 == chordTest[3]) return new int[]{chordTest[0], 6};
        if((chordTest[2] + 3) % 12 == chordTest[1] || (chordTest[2] + 3) % 12 == chordTest[3]) return new int[]{chordTest[0], 4};
        if((chordTest[2] + 4) % 12 == chordTest[1] || (chordTest[2] + 4) % 12 == chordTest[3]) return new int[]{chordTest[0], 2};
      }
      else if((chordTest[0] + 10) % 12 == chordTest[2]) return new int[]{chordTest[0], 3};
      else if((chordTest[0] + 11) % 12 == chordTest[2]) return new int[]{chordTest[0], 5};
      
      if((chordTest[0] + 4) % 12 == chordTest[3])
      {
        if((chordTest[3] + 6) % 12 == chordTest[1] || (chordTest[3] + 6) % 12 == chordTest[1]) return new int[]{chordTest[0], 3};
        if((chordTest[3] + 7) % 12 == chordTest[1] || (chordTest[3] + 7) % 12 == chordTest[1]) return new int[]{chordTest[0], 5};
        if((chordTest[3] + 3) % 12 == chordTest[1] || (chordTest[3] + 3) % 12 == chordTest[1]) return new int[]{chordTest[0], 1};
      }
      else if((chordTest[0] + 3) % 12 == chordTest[3])
      {
        if((chordTest[3] + 7) % 12 == chordTest[1] || (chordTest[3] + 7) % 12 == chordTest[2]) return new int[]{chordTest[0], 6};
        if((chordTest[3] + 3) % 12 == chordTest[1] || (chordTest[3] + 3) % 12 == chordTest[2]) return new int[]{chordTest[0], 4};
        if((chordTest[3] + 4) % 12 == chordTest[1] || (chordTest[3] + 4) % 12 == chordTest[2]) return new int[]{chordTest[0], 2};
      }
      else if((chordTest[0] + 10) % 12 == chordTest[3]) return new int[]{chordTest[0], 3};
      else if((chordTest[0] + 11) % 12 == chordTest[3]) return new int[]{chordTest[0], 5};
      
      
      
      
      //Checking when to return index 1 as root
      if((chordTest[1] + 4) % 12 == chordTest[0])
      {
        if((chordTest[0] + 6) % 12 == chordTest[2] || (chordTest[0] + 6) % 12 == chordTest[3]) return new int[]{chordTest[1], 3};
        if((chordTest[0] + 7) % 12 == chordTest[2] || (chordTest[0] + 7) % 12 == chordTest[3]) return new int[]{chordTest[1], 5};
        if((chordTest[0] + 3) % 12 == chordTest[2] || (chordTest[0] + 3) % 12 == chordTest[3]) return new int[]{chordTest[1], 1};
      }
      else if((chordTest[1] + 3) % 12 == chordTest[0])
      {
        if((chordTest[0] + 7) % 12 == chordTest[2] || (chordTest[0] + 7) % 12 == chordTest[3]) return new int[]{chordTest[1], 6};
        if((chordTest[0] + 3) % 12 == chordTest[2] || (chordTest[0] + 3) % 12 == chordTest[3]) return new int[]{chordTest[1], 4};
        if((chordTest[0] + 4) % 12 == chordTest[2] || (chordTest[0] + 4) % 12 == chordTest[3]) return new int[]{chordTest[1], 2};
      }
      else if((chordTest[1] + 10) % 12 == chordTest[0]) return new int[]{chordTest[1], 3};
      else if((chordTest[1] + 11) % 12 == chordTest[0]) return new int[]{chordTest[1], 5};
      
      if((chordTest[1] + 4) % 12 == chordTest[2])
      {
        if((chordTest[2] + 6) % 12 == chordTest[0] || (chordTest[2] + 6) % 12 == chordTest[3]) return new int[]{chordTest[1], 3};
        if((chordTest[2] + 7) % 12 == chordTest[0] || (chordTest[2] + 7) % 12 == chordTest[3]) return new int[]{chordTest[1], 5};
        if((chordTest[2] + 3) % 12 == chordTest[0] || (chordTest[2] + 3) % 12 == chordTest[3]) return new int[]{chordTest[1], 1};
      }
      else if((chordTest[1] + 3) % 12 == chordTest[2])
      {
        if((chordTest[2] + 7) % 12 == chordTest[0] || (chordTest[2] + 7) % 12 == chordTest[3]) return new int[]{chordTest[1], 6};
        if((chordTest[2] + 3) % 12 == chordTest[0] || (chordTest[2] + 3) % 12 == chordTest[3]) return new int[]{chordTest[1], 4};
        if((chordTest[2] + 4) % 12 == chordTest[0] || (chordTest[2] + 4) % 12 == chordTest[3]) return new int[]{chordTest[1], 2};
      }
      else if((chordTest[1] + 10) % 12 == chordTest[2]) return new int[]{chordTest[1], 3};
      else if((chordTest[1] + 11) % 12 == chordTest[2]) return new int[]{chordTest[1], 5};
      
      if((chordTest[1] + 4) % 12 == chordTest[3])
      {
        if((chordTest[3] + 6) % 12 == chordTest[0] || (chordTest[3] + 6) % 12 == chordTest[0]) return new int[]{chordTest[1], 3};
        if((chordTest[3] + 7) % 12 == chordTest[0] || (chordTest[3] + 7) % 12 == chordTest[0]) return new int[]{chordTest[1], 5};
        if((chordTest[3] + 3) % 12 == chordTest[0] || (chordTest[3] + 3) % 12 == chordTest[0]) return new int[]{chordTest[1], 1};
      }
      else if((chordTest[1] + 3) % 12 == chordTest[3])
      {
        if((chordTest[3] + 7) % 12 == chordTest[0] || (chordTest[3] + 7) % 12 == chordTest[2]) return new int[]{chordTest[1], 6};
        if((chordTest[3] + 3) % 12 == chordTest[0] || (chordTest[3] + 3) % 12 == chordTest[2]) return new int[]{chordTest[1], 4};
        if((chordTest[3] + 4) % 12 == chordTest[0] || (chordTest[3] + 4) % 12 == chordTest[2]) return new int[]{chordTest[1], 2};
      }
      else if((chordTest[1] + 10) % 12 == chordTest[3]) return new int[]{chordTest[1], 3};
      else if((chordTest[1] + 11) % 12 == chordTest[3]) return new int[]{chordTest[1], 5};
      
      
      
      //checking when to return index 2 as root
      if((chordTest[2] + 4) % 12 == chordTest[0])
      {
        if((chordTest[0] + 6) % 12 == chordTest[1] || (chordTest[0] + 6) % 12 == chordTest[3]) return new int[]{chordTest[2], 3};
        if((chordTest[0] + 7) % 12 == chordTest[1] || (chordTest[0] + 7) % 12 == chordTest[3]) return new int[]{chordTest[2], 5};
        if((chordTest[0] + 3) % 12 == chordTest[1] || (chordTest[0] + 3) % 12 == chordTest[3]) return new int[]{chordTest[2], 1};
      }
      else if((chordTest[2] + 3) % 12 == chordTest[0])
      {
        if((chordTest[0] + 7) % 12 == chordTest[1] || (chordTest[0] + 7) % 12 == chordTest[3]) return new int[]{chordTest[2], 6};
        if((chordTest[0] + 3) % 12 == chordTest[1] || (chordTest[0] + 3) % 12 == chordTest[3]) return new int[]{chordTest[2], 4};
        if((chordTest[0] + 4) % 12 == chordTest[1] || (chordTest[0] + 4) % 12 == chordTest[3]) return new int[]{chordTest[2], 2};
      }
      else if((chordTest[2] + 10) % 12 == chordTest[0]) return new int[]{chordTest[2], 3};
      else if((chordTest[2] + 11) % 12 == chordTest[0]) return new int[]{chordTest[2], 5};
      
      if((chordTest[2] + 4) % 12 == chordTest[1])
      {
        if((chordTest[1] + 6) % 12 == chordTest[0] || (chordTest[1] + 6) % 12 == chordTest[3]) return new int[]{chordTest[2], 3};
        if((chordTest[1] + 7) % 12 == chordTest[0] || (chordTest[1] + 7) % 12 == chordTest[3]) return new int[]{chordTest[2], 5};
        if((chordTest[1] + 3) % 12 == chordTest[0] || (chordTest[1] + 3) % 12 == chordTest[3]) return new int[]{chordTest[2], 1};
      }
      else if((chordTest[2] + 3) % 12 == chordTest[1])
      {
        if((chordTest[1] + 7) % 12 == chordTest[0] || (chordTest[1] + 7) % 12 == chordTest[3]) return new int[]{chordTest[2], 6};
        if((chordTest[1] + 3) % 12 == chordTest[0] || (chordTest[1] + 3) % 12 == chordTest[3]) return new int[]{chordTest[2], 4};
        if((chordTest[1] + 4) % 12 == chordTest[0] || (chordTest[1] + 4) % 12 == chordTest[3]) return new int[]{chordTest[2], 2};
      }
      else if((chordTest[2] + 10) % 12 == chordTest[1]) return new int[]{chordTest[2], 3};
      else if((chordTest[2] + 11) % 12 == chordTest[1]) return new int[]{chordTest[2], 5};
      
      if((chordTest[2] + 4) % 12 == chordTest[3])
      {
        if((chordTest[3] + 6) % 12 == chordTest[0] || (chordTest[3] + 6) % 12 == chordTest[0]) return new int[]{chordTest[2], 3};
        if((chordTest[3] + 7) % 12 == chordTest[0] || (chordTest[3] + 7) % 12 == chordTest[0]) return new int[]{chordTest[2], 5};
        if((chordTest[3] + 3) % 12 == chordTest[0] || (chordTest[3] + 3) % 12 == chordTest[0]) return new int[]{chordTest[2], 1};
      }
      else if((chordTest[2] + 3) % 12 == chordTest[3])
      {
        if((chordTest[3] + 7) % 12 == chordTest[0] || (chordTest[3] + 7) % 12 == chordTest[1]) return new int[]{chordTest[2], 6};
        if((chordTest[3] + 3) % 12 == chordTest[0] || (chordTest[3] + 3) % 12 == chordTest[1]) return new int[]{chordTest[2], 4};
        if((chordTest[3] + 4) % 12 == chordTest[0] || (chordTest[3] + 4) % 12 == chordTest[1]) return new int[]{chordTest[2], 2};
      }
      else if((chordTest[2] + 10) % 12 == chordTest[3]) return new int[]{chordTest[2], 3};
      else if((chordTest[2] + 11) % 12 == chordTest[3]) return new int[]{chordTest[2], 5};
      
      
      
      
      //checking when to return index 3 as root
      if((chordTest[3] + 4) % 12 == chordTest[0])
      {
        if((chordTest[0] + 6) % 12 == chordTest[1] || (chordTest[0] + 6) % 12 == chordTest[2]) return new int[]{chordTest[3], 3};
        if((chordTest[0] + 7) % 12 == chordTest[1] || (chordTest[0] + 7) % 12 == chordTest[2]) return new int[]{chordTest[3], 5};
        if((chordTest[0] + 3) % 12 == chordTest[1] || (chordTest[0] + 3) % 12 == chordTest[2]) return new int[]{chordTest[3], 1};
      }
      else if((chordTest[3] + 3) % 12 == chordTest[0])
      {
        if((chordTest[0] + 7) % 12 == chordTest[1] || (chordTest[0] + 7) % 12 == chordTest[2]) return new int[]{chordTest[3], 6};
        if((chordTest[0] + 3) % 12 == chordTest[1] || (chordTest[0] + 3) % 12 == chordTest[2]) return new int[]{chordTest[3], 4};
        if((chordTest[0] + 4) % 12 == chordTest[1] || (chordTest[0] + 4) % 12 == chordTest[2]) return new int[]{chordTest[3], 2};
      }
      else if((chordTest[3] + 10) % 12 == chordTest[0]) return new int[]{chordTest[3], 3};
      else if((chordTest[3] + 11) % 12 == chordTest[0]) return new int[]{chordTest[3], 5};
      
      if((chordTest[3] + 4) % 12 == chordTest[1])
      {
        if((chordTest[1] + 6) % 12 == chordTest[0] || (chordTest[1] + 6) % 12 == chordTest[2]) return new int[]{chordTest[3], 3};
        if((chordTest[1] + 7) % 12 == chordTest[0] || (chordTest[1] + 7) % 12 == chordTest[2]) return new int[]{chordTest[3], 5};
        if((chordTest[1] + 3) % 12 == chordTest[0] || (chordTest[1] + 3) % 12 == chordTest[2]) return new int[]{chordTest[3], 1};
      }
      else if((chordTest[3] + 3) % 12 == chordTest[1])
      {
        if((chordTest[1] + 7) % 12 == chordTest[0] || (chordTest[1] + 7) % 12 == chordTest[2]) return new int[]{chordTest[3], 6};
        if((chordTest[1] + 3) % 12 == chordTest[0] || (chordTest[1] + 3) % 12 == chordTest[2]) return new int[]{chordTest[3], 4};
        if((chordTest[1] + 4) % 12 == chordTest[0] || (chordTest[1] + 4) % 12 == chordTest[2]) return new int[]{chordTest[3], 2};
      }
      else if((chordTest[3] + 10) % 12 == chordTest[1]) return new int[]{chordTest[3], 3};
      else if((chordTest[3] + 11) % 12 == chordTest[1]) return new int[]{chordTest[3], 5};
      
      if((chordTest[3] + 4) % 12 == chordTest[2])
      {
        if((chordTest[2] + 6) % 12 == chordTest[0] || (chordTest[2] + 6) % 12 == chordTest[0]) return new int[]{chordTest[3], 3};
        if((chordTest[2] + 7) % 12 == chordTest[0] || (chordTest[2] + 7) % 12 == chordTest[0]) return new int[]{chordTest[3], 5};
        if((chordTest[2] + 3) % 12 == chordTest[0] || (chordTest[2] + 3) % 12 == chordTest[0]) return new int[]{chordTest[3], 1};
      }
      else if((chordTest[3] + 3) % 12 == chordTest[2])
      {
        if((chordTest[2] + 7) % 12 == chordTest[0] || (chordTest[2] + 7) % 12 == chordTest[1]) return new int[]{chordTest[3], 6};
        if((chordTest[2] + 3) % 12 == chordTest[0] || (chordTest[2] + 3) % 12 == chordTest[1]) return new int[]{chordTest[3], 4};
        if((chordTest[2] + 4) % 12 == chordTest[0] || (chordTest[2] + 4) % 12 == chordTest[1]) return new int[]{chordTest[3], 2};
      }
      else if((chordTest[3] + 10) % 12 == chordTest[2]) return new int[]{chordTest[3], 3};
      else if((chordTest[3] + 11) % 12 == chordTest[2]) return new int[]{chordTest[3], 5};
      
    }
   
    
    //println("COULDN'T CHORD");
    return new int[]{-1, -1};
  }


}
