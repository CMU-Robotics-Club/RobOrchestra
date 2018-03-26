import java.util.Random;

public class Generate{
  public ArrayList<ArrayList<Note>> playList;
  
  public Generate(){
    playList = new ArrayList<ArrayList<Note>>();
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
    
    for(int i = 0; i < actualLength; i++){
      //Some unmade get chord function
      ArrayList<Note> currChord = CHORDGETTER(chords.get(i));  //NEEDS TO BE IMPLEMENTED, I BELIEVE SOMEONE HAS ALREADY MADE THIS
      currChord = RULEFILTER(currChord); //WILL BE IMPLEMENTED BY ME
      bassLine.add(pickfromList(currChord));      
    }
    
    return bassLine;
  }
  
  //Pick Note from list of valid Notes
  public Note pickfromList(ArrayList<Note> options){
    Random rand = new Random();
    int length = options.size();
    int choose = rand.nextInt(length);
    return options.get(choose);
  }
   
  
}