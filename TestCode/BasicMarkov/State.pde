public class State extends Object implements Comparable<State>{
  public int[] pitches;
  public int[] lengths;
  public int[] delays; //Delay after the last note
  public long[] starttimes; //For chords
  
  //NOTE: We deep-copy all arrays in the constructor to avoid weird stuff happening
  //(This is probably not the standard way to deal with that, but whatever.)
  public State(){
    pitches = new int[] {};
    lengths = new int[] {};
    delays = new int[] {};
  }
  
  public State(int[] p, int[] l){
    pitches = copy(p);
    lengths = copy(l);
    delays = copy(l);
  }
  
  public State(int[] p, int[] l, int[] d){
    pitches = copy(p);
    lengths = copy(l);
    delays = copy(d);
  }
  
  public State(int[] p, int[] l, int[] d, long[] t){
    pitches = copy(p);
    lengths = copy(l);
    delays = copy(d);
    starttimes = copy(t);
  }
  
  public boolean equals(Object o){
    if(o.getClass() != this.getClass()) return false;
    return this.compareTo((State)o)==0;
  }
  
  public int compareTo(State s){
    //println("Comparing");
    int i = 0; int j = 0;
    while(i < pitches.length && j < s.pitches.length){
      if(pitches[i] != s.pitches[j]) return pitches[i]-s.pitches[j];
      i++;
      j++;
    }
    if(i == pitches.length && j != s.pitches.length) return -1;
    if(j == s.pitches.length && i != pitches.length) return 1;
    i = 0; j = 0;
    while(i < lengths.length && j < s.lengths.length){
      if(lengths[i] != s.lengths[j]) return lengths[i]-s.lengths[j];
      i++;
      j++;
    }
    if(i == lengths.length && j != s.lengths.length) return -1;
    if(j == s.lengths.length && i != lengths.length) return 1;
    //println("Comparing delays");
    i = 0; j = 0;
    while(i < delays.length && j < s.delays.length){
      if(delays[i] != s.delays[j]) return delays[i]-s.delays[j];
      i++;
      j++;
    }
    //println("Comparing delay lengths");
    if(i == delays.length && j != s.delays.length) return -1;
    if(j == s.delays.length && i != delays.length) return 1;
    //println("Comparing start times");
    //println("Returning 0");
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
    s += "], delays: [";
    for(int x = 0; x < delays.length; x++){
      s += delays[x];
      if(x < delays.length-1)s += ", ";
    }
    s += "], start times: [";
    for(int x = 0; x < starttimes.length; x++){
      s += starttimes[x];
      if(x < starttimes.length-1)s += ", ";
    }
    s += "]";
    return s;
  }
  
  private int[] copy(int[] A){
    int[] temp = new int[A.length];
    for(int x = 0; x < A.length; x++){
      temp[x] = A[x];
    }
    return temp;
  }
  
  private long[] copy(long[] A){
    long[] temp = new long[A.length];
    for(int x = 0; x < A.length; x++){
      temp[x] = A[x];
    }
    return temp;
  }
}