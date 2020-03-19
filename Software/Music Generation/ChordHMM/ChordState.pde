public class ChordState extends Object implements Comparable<ChordState>{
  public int[] roots;
  public int[] types;
  public int[] lengths;
  public int[] delays; //Delay after the last note
  public long[] starttimes; //For chords
  
  //NOTE: We deep-copy all arrays in the constructor to avoid weird stuff happening
  //(This is probably not the standard way to deal with that, but whatever.)
  public ChordState(){
    roots = new int[] {};
    types = new int[] {};
    lengths = new int[] {};
    delays = new int[] {};
  }
  
  public ChordState(int[] r, int[] t, int[] l){
    roots = copy(r);
    types = copy(t);
    lengths = copy(l);
    delays = copy(l);
  }
  
  public ChordState(int[] r, int[] t, int[] l, int[] d){
    roots = copy(r);
    types = copy(t);
    lengths = copy(l);
    delays = copy(d);
  }
  
  public ChordState(int[] r, int[] t, int[] l, int[] d, long[] tt){
    roots = copy(r);
    types = copy(t);
    lengths = copy(l);
    delays = copy(d);
    starttimes = copy(tt);
  }
  
  public boolean equals(Object o){
    if(o.getClass() != this.getClass()) return false;
    return this.compareTo((ChordState)o)==0;
  }
  
  public int compareTo(ChordState s){
    //println("Comparing");
    int i = 0; int j = 0;
    while(i < roots.length && j < s.roots.length){
      if(roots[i] != s.roots[j]) return roots[i]-s.roots[j];
      i++;
      j++;
    }
    if(i == roots.length && j != s.roots.length) return -1;
    if(j == s.roots.length && i != roots.length) return 1;
    while(i < types.length && j < s.types.length){
      if(types[i] != s.types[j]) return types[i]-s.types[j];
      i++;
      j++;
    }
    if(i == types.length && j != s.roots.length) return -1;
    if(j == s.types.length && i != roots.length) return 1;
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
    /*i = 0; j = 0;
    while(i < starttimes.length && j < s.starttimes.length){
      if(starttimes[i] != s.starttimes[j]) return (int)((starttimes[i]-s.starttimes[j])/abs(starttimes[i]-s.starttimes[j]));
      i++;
      j++;
    }
    //println("Comparing start time lengths");
    if(i == starttimes.length && j != s.starttimes.length) return -1;
    if(j == s.starttimes.length && i != starttimes.length) return 1;*/
    //println("Returning 0");
    return 0;
  }
  
  public String toString(){
    String s = "{Roots: [";
    for(int x = 0; x < roots.length; x++){
      s += roots[x];
      if(x < roots.length-1)s += ", ";
    }
    s += "], types: [";
    for(int x = 0; x < types.length; x++){
      s += types[x];
      if(x < types.length-1)s += ", ";
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
    s += "]}";
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
