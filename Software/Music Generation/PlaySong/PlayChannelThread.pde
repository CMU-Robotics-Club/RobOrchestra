class PlayChannelThread extends Thread{
  File myFile;
  int[] trackNumbers;
  
  double mspertick;
  int noteCount;
  
  private ArrayList<PartialNote> activeNotes = new ArrayList<PartialNote>();
  private int[] pitchBuffer = new int[0];
  private int[] lengthBuffer = new int[0];
  private int[] delayBuffer = new int[0];
  private long[] timeBuffer = new long[0];
  
  private MidiBus myBus;
    
  public PlayChannelThread(File inFile, int trackNumber, MidiBus m){
    myFile = inFile;
    trackNumbers = new int[1];
    trackNumbers[0] = trackNumber;

    myBus = m;
  }
  
  public void run(){
    PartialNote dummyNote = new PartialNote(0, mintimestamp);
    dummyNote.len = 0;
    activeNotes.add(dummyNote);
     try{
  Sequence sequence = MidiSystem.getSequence(myFile);
      
  double mspertick = 1.0*sequence.getMicrosecondLength()/sequence.getTickLength()/1000;
    
  Track[] tracks = sequence.getTracks();
  for(int trackNumber:trackNumbers){
//  for(int trackNumber = 0; trackNumber < tracks.length; trackNumber++){
      Track track = tracks[trackNumber];
      int prevNote = 0;
      
      //TODO start thread here
      System.out.println("Track " + trackNumber + ": size = " + track.size());
      System.out.println();
      for (int i=0; i < track.size(); i++) { 
          MidiEvent event = track.get(i);
          long timestamp = event.getTick();
          qprint("@" + event.getTick() + " ");
          MidiMessage message = event.getMessage();
          if (message instanceof ShortMessage) {
              ShortMessage sm = (ShortMessage) message;
              qprint("Channel: " + sm.getChannel() + " ");
              if (sm.getCommand() == NOTE_ON) {
                  int key = sm.getData1();
                  int octave = (key / 12)-1;
                  int note = key % 12;
                  
                  if(sm.getData2() > 0){ //Make sure you're not just setting the velocity to 0...
                    //key is the numerical value for the pitch
                    
                    //Add a new note for the new pitch
                    activeNotes.add(new PartialNote(key, timestamp));
                    //Update the delay for the previous pitch
                    if(prevNote != -1){
                      PartialNote p = activeNotes.get(activeNotes.indexOf(new PartialNote(prevNote)));
                      p.delay = (int)(timestamp - p.startTime);
                      p.delay*=mspertick;
                    }
                    //Check if notes finished
                    checkCompletedNotes(stateLength, trackNumber, myBus);
                    //Update the previous pitch
                    prevNote = key;
                    noteCount++;
                  }
                  else{
                    //Note is actually 0 velocity
                    //Compute length of whatever note stopped
                    PartialNote p = activeNotes.get(activeNotes.indexOf(new PartialNote(key)));
                    p.len = (int)(timestamp - p.startTime);
                    p.len *= mspertick;
                    checkCompletedNotes(stateLength, trackNumber, myBus);
                  }
                  
                  //Print stuff
                  String noteName = NOTE_NAMES[note];
                  int velocity = sm.getData2();
                  qprint("Note on, " + noteName + octave + " key=" + key + " velocity: " + velocity);  
        } else if (sm.getCommand() == NOTE_OFF) {
                  int key = sm.getData1();
                  int octave = (key / 12)-1;
                  int note = key % 12;
                  
                  //Compute length of whatever note stopped
                  PartialNote p = activeNotes.get(activeNotes.indexOf(new PartialNote(key)));
                  p.len = (int)(timestamp - p.startTime);
                  p.len *= mspertick;
                  checkCompletedNotes(stateLength, trackNumber, myBus);
                  
                  String noteName = NOTE_NAMES[note];
                  int velocity = sm.getData2();
                  qprint("Note off, " + noteName + octave + " key=" + key + " velocity: " + velocity);
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
      }
      System.out.println();
      
      //At this point we've read the entire track. Last note should be tied up in activeNotes, everything else done
      if(activeNotes.size() > 0){
        activeNotes.get(0).delay = activeNotes.get(0).len;
        checkCompletedNotes(stateLength, trackNumber, myBus);
      }
      //Rerun initial notes so the piece loops
      /*activeNotes = new ArrayList<PartialNote>(initialNotes); //Shallow copy is fine here
      checkCompletedNotes(stateLength, trackNumber, myBus); //Re-process starting notes to close the loop
      */
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
  }
  
  private void checkCompletedNotes(int stateLength, int channel, MidiBus myBus){
    //Process any notes that are done (have to go in order, so stop at first incomplete)
    while(activeNotes.size() != 0){
      PartialNote p = activeNotes.get(0);
      if(p.delay >= 0 && p.len >= 0){
        //Note is done; put it in buffers, and possibly state/transition arrays
        pitchBuffer = cappedAdd(pitchBuffer, p.pitch, stateLength);
        lengthBuffer = cappedAdd(lengthBuffer, p.len, stateLength);
        delayBuffer = cappedAdd(delayBuffer, p.delay, stateLength);
        timeBuffer = cappedAdd(timeBuffer, p.startTime, stateLength);
        
        activeNotes.remove(p);
        
        //NEW in PlaySong - play the finished note
        channel = 0;
        if(p.pitch > 30 && p.pitch < 40){
          //Percussion, send on channel 1
          channel = 1;
        }
        Note snareNote = new Note(channel, p.pitch, globalVolume);
        int[] chord = {-1, -1};
        println(trackNumbers);
        println(p);
        PlayNoteThread t = new PlayNoteThread(snareNote, p.len, sendNoteOffCommands, chord, myBus);
        t.start();
        delay(p.delay);
      }
      else{
        return;
      }
    }
  }
  
  private void qprint(String toPrint){
    if(printThings){
       System.out.println(toPrint); 
    }
  }
  
  private int[] cappedAdd(int[] array, int newval, int maxlen){
    if(array.length < maxlen){
      int[] temp = new int[array.length + 1];
      for(int x = 0; x < array.length; x++){
        temp[x] = array[x];
      }
      temp[temp.length-1] = newval;
      return temp;
    }
    else{
      return shiftArrayBack(array, newval);
    }
  }
  
  private long[] cappedAdd(long[] array, long newval, int maxlen){
    if(array.length < maxlen){
      long[] temp = new long[array.length + 1];
      for(int x = 0; x < array.length; x++){
        temp[x] = array[x];
      }
      temp[temp.length-1] = newval;
      return temp;
    }
    else{
      return shiftArrayBack(array, newval);
    }
  }
  
  private int[] shiftArrayBack(int[] array, int newval){
    for(int x = 0; x < array.length-1; x++){
      array[x] = array[x+1];
    }
    array[array.length-1] = newval;
    return array;
  }
  
  private long[] shiftArrayBack(long[] array, long newval){
    for(int x = 0; x < array.length-1; x++){
      array[x] = array[x+1];
    }
    array[array.length-1] = newval;
    return array;
  }
}
