import java.io.File;
import java.util.Arrays;


public static final String KEY = "D";
public static final String[] NOTE_NAMES = {"C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"};
public static final int[] KEY_NOTES = {0,2,4,5,7,9,11,12};

void setup() {
  ArrayList<Integer> notes = new ArrayList<Integer>();

  ArrayList<ArrayList<Integer>> pattern_list = new ArrayList<ArrayList<Integer>>();
  
  int k = Arrays.asList(NOTE_NAMES).indexOf(KEY);
  
  for(int i=0; i<100; i++) {
    notes.add((KEY_NOTES[(int)(Math.random()*8)]+k)%13);
  }
  
  if(notes.size()>=10) {
    for(int i=10; i<notes.size(); i+=10) {  
    ArrayList<Integer> pattern = new ArrayList<Integer>();
    
      for(int j=i-10; j<i; j++) {
        pattern.add(notes.get(j));
      }
    pattern_list.add(pattern);
    }
  }
  else { pattern_list.add(notes); }
  
  for(int i=0; i<pattern_list.size(); i++) {
    System.out.println(pattern_list.get(i));
  }
}