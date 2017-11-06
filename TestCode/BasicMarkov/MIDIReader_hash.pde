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


public class MIDIReader_hash{
  
  File MIDIfile;
  double mspertick;
  
  int precision;
  
  public Map<Long, ArrayList<ShortMessage>> mMap = new HashMap<Long, ArrayList<ShortMessage>>();
  
  public ArrayList<ShortMessage> notesPlaying = new ArrayList<ShortMessage>();
  
  public MIDIReader_hash(File file){
    this(file, new int[] {0});
  }
  
  public MIDIReader_hash(File file, int[] toRead){
    this(file, toRead, 100);
  }
  
  //Defaults to a 1 note state and a 1 length state
  public MIDIReader_hash(File file, int[] toRead, int p){
    precision = p;
    try{  
      Sequence sequence = MidiSystem.getSequence(file);
      
      mspertick = 1.0*sequence.getMicrosecondLength()/sequence.getTickLength()/1000;
      
      int trackNumber = 0;
      
      Track[] tracks = sequence.getTracks();
      for(int x: toRead){
      //for(int x = 0; x < tracks.length; x++){
          Track track = tracks[x];          
          trackNumber++;
          System.out.println("Track " + trackNumber + ": size = " + track.size());
          System.out.println();
          long oldtimestamp = 0;
          for (int i=0; i < track.size(); i++) {
              MidiEvent event = track.get(i);
              long timestamp = event.getTick();
              
              //Update hash map
              for(long y = oldtimestamp/precision*precision; y < timestamp/precision*precision; y += precision){
                ArrayList<ShortMessage> temp = (ArrayList<ShortMessage>)notesPlaying.clone();
                mMap.put(y, temp);
              }
              oldtimestamp = timestamp;
              
              //Read new message
              MidiMessage message = event.getMessage();
              if (message instanceof ShortMessage) {
                ShortMessage sm = (ShortMessage) message;
                /* MY CODE STARTS */
                
                //Trying to keep old code mostly intact...
                /*ArrayList<ShortMessage> temp = new ArrayList<ShortMessage>();
                temp.add(sm);
                if(mMap.get(timestamp/precision*precision) == null) mMap.put(timestamp/precision*precision, temp);
                else
                {*/
                
                  if (sm.getCommand() == NOTE_ON) {                     
                      if(sm.getData2() > 0){         
                        notesPlaying.add(sm);
                        //mMap.get(timestamp/precision*precision).add(sm);  
                      }
                      else{
                        //It's a note off
                        notesPlaying = removeStuff(notesPlaying, sm);
                      }
                  }
                  else if(sm.getCommand() == NOTE_OFF){
                    //It's a note off
                    notesPlaying = removeStuff(notesPlaying, sm);
                  }
                //}
              }
              else {
                if(message instanceof MetaMessage){
                   byte[] data = ((MetaMessage)message).getData();
                }
              }
           }
         }
  
          System.out.println();
       }
    catch(Exception e){println("Suppressed an error"); exit();}
  }
  
  private ArrayList<ShortMessage> removeStuff(ArrayList<ShortMessage> notesPlaying, ShortMessage sm){
    //Do stuff
    int key = sm.getData1();
    for(int x = 0; x < notesPlaying.size(); x++){
      int tempkey = notesPlaying.get(x).getData1();
      if(tempkey == key){
        notesPlaying.remove(x);
        break;
      }
    }
    return notesPlaying;
  }
}