import java.util.*;

public class Generate{
  
  private float set_interval = 1000;
  private int[] STEPS = {0, 2, 4, 5, 7, 9, 11};
  private Note TONIC;
  
  public ArrayList<ArrayList<Note>> playList;
  
  public Generate(Note TONIC){
    playList = new ArrayList<ArrayList<Note>>();
    this.TONIC = TONIC;
  }
  
  //Generate Chord Progression of length chords
  public ArrayList<Integer> chordProgGen(int length){
    ArrayList<Integer> chords = new ArrayList<Integer>();
    int count = 0;
    Random rand = new Random();
    while (count < length){
      int curr = rand.nextInt(4);
      if(curr == 0){
        chords.add(1);
        chords.add(4);
        chords.add(5);
        chords.add(1);
        count += 4;
      }
      else if(curr == 1){
        chords.add(1);
        chords.add(5);
        chords.add(1);
        count += 3;
      }
      else if(curr == 2){
        chords.add(1);
        chords.add(5);
        chords.add(6);
        chords.add(4);
        chords.add(1);
        count += 5;
      }
      else if(curr == 3){
        chords.add(1);
        chords.add(6);
        chords.add(2);
        chords.add(5);
        chords.add(1);
        count += 5;
      }
    }
    return chords;
  }
  
  
  //Generate Bass Line of length notes
  public ArrayList<Note> bassLineGen(int length){
    ArrayList<Note> bassLine = new ArrayList<Note>();
    ArrayList<Integer> chords = chordProgGen(length);
    int actualLength = chords.size();
    
   // Note prevNote = new Note(channel, 0, 0);
    for(int i = 0; i < actualLength; i++){
      //Some unmade get chord function
      ArrayList<Note> currChord = CHORDGETTER(chords.get(i));
            
      Note bassNote = pickfromList(currChord);     
      while(bassNote.pitch() > bass_high){
        bassNote.setPitch(bassNote.pitch() - 12);
      }
      while(bassNote.pitch() < bass_low){
        bassNote.setPitch(bassNote.pitch() + 12);
      }
      
      bassLine.add(bassNote);
    }
    System.out.println(chords);
    return bassLine;
  }
  
  //Pick Note from list of valid Notes
  public Note pickfromList(ArrayList<Note> options){
    Random rand = new Random();
    int length = options.size();
    int choose = rand.nextInt(length);
    return options.get(choose);
  }
  
  public ArrayList<Note> CHORDGETTER(Integer lol){
    ArrayList<Note> arr = new ArrayList<Note>();
    int base, third, fifth;
    
    base = STEPS[(lol-1)%7]; //root
    third = STEPS[(lol+1)%7];
    fifth = STEPS[(lol+3)%7];
    
    
    arr.add(new Note(channel, TONIC.pitch()+base, 100));
    arr.add(new Note(channel, TONIC.pitch()+third,100));
    arr.add(new Note(channel, TONIC.pitch()+fifth,100));
    arr.add(new Note(channel, TONIC.pitch()+base+12, 100));
    
    return arr;
  }
   
   
  public ArrayList<Note> RULEFILTER(ArrayList<Note> choices, ArrayList<String> rules){
    ArrayList<Note> arr = new ArrayList<Note>(choices);
    
    //if(rules.contains("bassline")){
    //  int bass_note = arr.get(0).pitch();
    //  int n = arr.size();
    //  for (int i = 0; i < n; i++){
    //    if (arr.get(i).pitch() == bass_note+7) arr.remove(i);
    //  }
    //}
      
    return arr;
  }
  
  public ArrayList<Voices> music_gen(int length){
    ArrayList<Note> bass_line = bassLineGen(length);
    
    
    
    
    
    return new ArrayList<Voices>();
  }
  
  
}