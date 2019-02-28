public class PartialNote extends Object implements Comparable<PartialNote> {

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
  
  public int compareTo(PartialNote n){
    return pitch - n.pitch;
  }
  
  public boolean equals(Object o){
    if(o.getClass() != this.getClass()) return false;
    return this.compareTo((PartialNote)o)==0;
  }
  
  public int hashCode(){
    return 0;
  }
  
  public String toString(){
    return("Note: " + pitch + "; length: " + len + "; delay: " + delay + "; startTime: " + startTime);
  }
}