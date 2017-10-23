public class PartialNote implements Comparable<Note>{

  int pitch;
  int len;
  int delay;
  long startTime;
  
  public PartialNote(int p, int l, int d, long t){
    pitch = p;
    len = l;
    delay = d;
    startTime = t;
  }
  
  public PartialNote(int p, long t){
    pitch = p;
    len = -1;
    delay = -1;
    startTime = t;
  }
  
  public PartialNote(int p){
    pitch = p;
    len = -1;
    delay = -1;
    startTime = -1;
  }
  
  public int compareTo(Note n){
    return pitch - n.pitch;
  }
  
  public boolean equals(Note n){
    return compareTo(n) == 0;
  }
  
}