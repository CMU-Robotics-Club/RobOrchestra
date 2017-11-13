class PlayNoteThread extends Thread{
  Note note;
  int len;
  int chord;
  boolean noteOff;
  
  public PlayNoteThread(Note n, int l, boolean b, int c){
    note = n;
    len = l;
    noteOff = b;
    chord = c;
  }
  
  public void run(){
    if(note.pitch == 61) {
      note.pitch = 73;
    }
    else if(note.pitch == 75) {
      note.pitch = 63;
    }
    
    
    myBus.sendNoteOn(note);
    scaleOn(chord);
    delay((int)(lenmult*len*legato));
    if(noteOff){
      myBus.sendNoteOff(note);
    }
    scaleOff(chord);
    delay((int)(lenmult*len*(1-legato)));
  }
  
  private void scaleOn(int c){
    if(c!=-1){
      compBus.sendNoteOn(new Note(1, (c%12)+60, 100));
      if(c == 9) {
        compBus.sendNoteOn(new Note(1, ((c+3)%12)+60, 100));
      }
      else {
        compBus.sendNoteOn(new Note(1, ((c+4)%12)+60, 100));
      }
      compBus.sendNoteOn(new Note(1, ((c+7)%12)+60, 100));
    }
  }
  
  private void scaleOff(int c){
    if(c!=-1){
      compBus.sendNoteOff(new Note(1, (c%12)+60, 100));
      compBus.sendNoteOff(new Note(1, ((c+4)%12)+60, 100));
      compBus.sendNoteOff(new Note(1, ((c+7)%12)+60, 100));
    }
  }
}