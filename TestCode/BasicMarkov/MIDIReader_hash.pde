import java.io.File;
import java.util.Arrays;
import java.util.ArrayList;

import java.io.PrintWriter;

import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.Set;

import javax.sound.midi.MetaMessage;
import javax.sound.midi.MidiEvent;
import javax.sound.midi.MidiMessage;
import javax.sound.midi.MidiSystem;
import javax.sound.midi.Sequence;
import javax.sound.midi.ShortMessage;
import javax.sound.midi.Track;

public static Map<Long, ArrayList<ShortMessage>> mMap = new HashMap<Long, ArrayList<ShortMessage>>();

public class MIDIReader_hash{
  
  File MIDIfile;
  double mspertick;
  
  public MIDIReader_hash(File file){
    this(file, new int[] {0});
  }
  
  //Defaults to a 1 note state and a 1 length state
  public MIDIReader_hash(File file, int[] toRead){
    try{  
      Sequence sequence = MidiSystem.getSequence(file);
      
      mspertick = 1.0*sequence.getMicrosecondLength()/sequence.getTickLength()/1000;
      
      int trackNumber = 0;
      
      Track[] tracks = sequence.getTracks();
      for(int x = 0; x < tracks.length; x++){
          Track track = tracks[x];          
          trackNumber++;
          System.out.println("Track " + trackNumber + ": size = " + track.size());
          System.out.println();
          for (int i=0; i < track.size(); i++) {
              MidiEvent event = track.get(i);
              long timestamp = event.getTick();
              MidiMessage message = event.getMessage();
              if (message instanceof ShortMessage) {
                ShortMessage sm = (ShortMessage) message;
                /* MY CODE STARTS */
                ArrayList<ShortMessage> temp = new ArrayList<ShortMessage>();
                temp.add(sm);
                if(mMap.get(timestamp/100*100) == null) mMap.put(timestamp/100*100, temp);
                else
                {
                
                  if (sm.getCommand() == NOTE_ON) {                     
                      if(sm.getData2() > 0){                   
                        mMap.get(timestamp/100*100).add(sm);  
                      }
                  }
                }
              }
              else {
                if(message instanceof MetaMessage){
                   byte[] data = ((MetaMessage)message).getData();
                }
              }
           }  
         }
  
          System.out.println();
          
          //Map the last note to the first note
       }
    catch(Exception e){exit();}
  }
}