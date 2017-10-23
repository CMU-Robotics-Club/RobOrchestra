public class TempNote implements Comparable<Note>{

  int pitch;
  int len;
  int delay;
  
  public TempNote(int p, int l, int d){
    pitch = p;
    len = l;
    delay = d;
  }
  
  public int compareTo(Note n){
    return pitch - n.pitch;
  }
  
  public boolean equals(Note n){
    return compareTo(n) == 0;
  }
  
}