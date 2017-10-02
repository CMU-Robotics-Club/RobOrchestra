public class State implements Comparable<State>{
  public int[] pitches;
  public int[] lengths;
  
  public State(int[] p, int[] l){
    pitches = p;
    lengths = l;
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
    return 0;
  }
}