public class State implements Comparable<State>{
  public int[] pitches;
  public int[] lengths;
  
  public State(){
    pitches = new int[] {};
    lengths = new int[] {};
  }
  
  public State(int[] p, int[] l){
    pitches = p;
    lengths = l;
  }
  
  public boolean equals(Object o){
    if(o.getClass() != this.getClass()) return false;
    return this.compareTo((State)o)==0;
  }
  
  public int compareTo(State s){
    int i = 0; int j = 0;
    while(i < pitches.length && j < s.pitches.length){
      if(pitches[i] != s.pitches[i]) return pitches[i]-s.pitches[i];
      i++;
      j++;
    }
    if(i == pitches.length && j != s.pitches.length) return -1;
    if(j == s.pitches.length && i != pitches.length) return 1;
    while(i < lengths.length && j < s.lengths.length){
      if(lengths[i] != s.lengths[i]) return lengths[i]-s.lengths[i];
      i++;
      j++;
    }
    if(i == lengths.length && j != s.lengths.length) return -1;
    if(j == s.lengths.length && i != lengths.length) return 1;
    return 0;
  }
  
  public String toString(){
    String s = "Pitches: [";
    for(int x = 0; x < pitches.length; x++){
      s += pitches[x];
      if(x < pitches.length-1)s += ", ";
    }
    s += "], lengths: [";
    for(int x = 0; x < lengths.length; x++){
      s += lengths[x];
      if(x < lengths.length-1)s += ", ";
    }
    s += "]";
    return s;
  }
}