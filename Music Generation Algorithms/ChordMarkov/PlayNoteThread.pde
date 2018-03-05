class PlayNoteThread extends Thread{
  Note note;
  int len;
  int[] chord;
  boolean noteOff = false;
  ArrayList<Note> chordNotes;
  
  public PlayNoteThread(Note n, int l, boolean b, int[] c){
    note = n;
    len = l;
    noteOff = b;
    chord = c;
    chordNotes = new ArrayList<Note>();
  }
  
  public void run(){
    
    myBus.sendNoteOn(note);
    scaleOn(chord);
    delay((int)(lenmult*len*legato));
    if(noteOff){
      myBus.sendNoteOff(note);
    }
    scaleOff(chord);
    //delay((int)(lenmult*len*(1-legato)));
  }
  
  private void scaleOn(int[] c){
    
    double r = Math.random();
    //if(r > 0.25) return;
    
    if(r > 0.2){
      chordVolume *= 0.9;
      if(chordVolume < 40) chordVolume = 40;
    }
    else{
      chordVolume = 100;
    }
    
    //Hopefully this works; mostly written with if statements and Wikipedia, and no idea what's supposed to happen, so...
    if(c[0]!=-1){
      //Tonic
      chordNotes.add(new Note(1, (c[0]%12)+60, chordVolume));
      
      //Third
      if(c[1] == 2 ||c[1] == 4 || c[1] == 6 || c[1] == 7) {
        chordNotes.add(new Note(1, ((c[0]+3)%12)+60, chordVolume));
      }
      if(c[1] == 1 ||  c[1] == 3 || c[1] == 5) {
        chordNotes.add(new Note(1, ((c[0]+4)%12)+60, chordVolume));
      }
      
      //Fifth
      if(c[1] == 4 || c[1] == 7){
        chordNotes.add(new Note(1, ((c[0]+6)%12)+60, chordVolume));
      }
      if(c[1] == 1 || c[1] == 2 || c[1] == 3 || c[1] == 5 || c[1] == 6){
        chordNotes.add(new Note(1, ((c[0]+7)%12)+60, chordVolume));
      }
      
      //Seventh
      if(c[1] == 7){
        chordNotes.add(new Note(1, ((c[0]+9)%12)+60, chordVolume));
      }
      
      if(c[1] == 3 || c[1] == 6){
        chordNotes.add(new Note(1, ((c[0]+10)%12)+60, chordVolume));
      }
      if(c[1] == 5){
        chordNotes.add(new Note(1, ((c[0]+11)%12)+60, chordVolume));
      }
    }
    
    //Take chords down an octave
    /*for(Note n: chordNotes){
      n.pitch -= 12;
    }*/
    
    //Play the chord
    for(int x = 0; x < chordNotes.size(); x++){
      compBus.sendNoteOn(chordNotes.get(x));
    }
  }
  
  private void scaleOff(int[] c){
    //Stop playing the chord
    for(int x = 0; x < chordNotes.size(); x++){
      compBus.sendNoteOff(chordNotes.get(x));
    }
  }
}