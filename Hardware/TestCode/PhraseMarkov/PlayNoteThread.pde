class PlayNoteThread extends Thread{
  Note note;
  int len;
  boolean noteOff;
  
  public PlayNoteThread(Note n, int l, boolean b){
    note = n;
    len = l;
    noteOff = b;
  }
  
  public void run(){
    myBus.sendNoteOn(note);
    delay((int)(lenmult*len*legato));
    if(noteOff){
      myBus.sendNoteOff(note);
    }
    delay((int)(lenmult*len*(1-legato)));
  }
}