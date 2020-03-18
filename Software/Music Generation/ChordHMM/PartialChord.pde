public class PartialChord extends Object implements Comparable<PartialChord> {

  int root;
  int type;
  int len;
  int delay;
  long startTime;
  
  public PartialChord(){
    root = -1;
    type = -1;
    len = -1;
    delay = -1;
    startTime = -1;
  }
  
  public PartialChord(int r, int ty, int l, int d, long t){
    root = r;
    type = ty;
    len = l;
    delay = d;
    startTime = t;
  }
  
  public PartialChord(int r, int ty, long t){
    root = r;
    type = ty;
    len = -1;
    delay = -1;
    startTime = t;
  }
  
  public PartialChord(int r, int ty){
    root = r;
    type = ty;
    len = -1;
    delay = -1;
    startTime = -1;
  }
  
  public int compareTo(PartialChord n){
    return root - n.root;
  }
  
  public boolean equals(Object o){
    if(o.getClass() != this.getClass()) return false;
    return this.compareTo((PartialChord)o)==0;
  }
  
  public int hashCode(){
    return 0;
  }
  
  public String toString(){
    return("Root: " + root + "; type: " + type + "; length: " + len + "; delay: " + delay + "; startTime: " + startTime);
  }
}
