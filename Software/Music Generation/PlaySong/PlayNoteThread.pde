class PlayNoteThread extends Thread{
  Note note;
  int len;
  int[] chord;
  boolean noteOff = false;
  ArrayList<Note> chordNotes;
  MidiBus myBus;
  
  public PlayNoteThread(Note n, int l, boolean b, int[] c, MidiBus m){
    note = n;
    len = l;
    noteOff = b;
    chord = c;
    chordNotes = new ArrayList<Note>();
    myBus = m;
  }
  
  public void run(){
    myBus.sendNoteOn(note);
    delay((int)(lenmult*len*legato));
    if(noteOff){
      myBus.sendNoteOff(note);
    }
  }
}
