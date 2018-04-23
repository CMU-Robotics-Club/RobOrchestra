import java.util.*;
import arb.soundcipher.*;
//Need to have soundcipher library downloaded in Processing libraries

public class Generate{
  
  private float set_interval = 1000;
  private int[] STEPS = {0, 2, 4, 5, 7, 9, 11};
  private Note TONIC;
  public SCScore score;
  public ArrayList<Integer> chords; 
  
  public ArrayList<ArrayList<Note>> playList;
  
  public Generate(Note TONIC){
    playList = new ArrayList<ArrayList<Note>>();
    this.TONIC = TONIC;
    score = new SCScore();
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
    Random rand = new Random();
    ArrayList<Note> bassLine = new ArrayList<Note>();
    ArrayList<Integer> Chords = chordProgGen(length);
    int actualLength = Chords.size();
    
   // Note prevNote = new Note(channel, 0, 0);
    for(int i = 0; i < actualLength; i++){
      //Some unmade get chord function
      ArrayList<Note> currChord = CHORDGETTER(Chords.get(i));
            
      Note bassNote = pickfromList(currChord);     
      while(bassNote.pitch() > bass_high){
        bassNote.setPitch(bassNote.pitch() - 12);
      }
      while(bassNote.pitch() < bass_low){
        bassNote.setPitch(bassNote.pitch() + 12);
      }
      
      bassLine.add(bassNote);
    }
    
    bassLine.set(bassLine.size()-2, new Note(channel, TONIC.pitch()-1+3*(rand.nextInt(2)), 100));
    
    chords = Chords;
    bassLine.set(bassLine.size()-1, TONIC); 
    bassLine.set(0, TONIC);
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
   
   
  //public ArrayList<Note> RULEFILTER(ArrayList<Note> choices, ArrayList<String> rules){
  //  ArrayList<Note> arr = new ArrayList<Note>(choices);
    
      
  //  return arr;
  //}
  
  
  
  
  
  
  
  
  
  public void music_gen(int length){
    Random rand = new Random();
    ArrayList<Note> bass_line = bassLineGen(length);
    for (int i = 0; i < bass_line.size(); i++){
      score.addNote(TIME*i, bass_line.get(i).pitch(), bass_line.get(i).velocity(), TIME);
    }
    
    int prevNote = -1;
    int prevChord = -1;
    int prevInterval = -1;
    
    for (int i = 0; i < bass_line.size()-2; i++){
      ArrayList<Note> currChord = CHORDGETTER(chords.get(i));
      if (prevInterval == 8 || prevInterval == 5){
        currChord = removeByNote(currChord, bass_line.get(i));
        currChord = removeByNote(currChord, new Note(channel, bass_line.get(i).pitch() + 7, 100));
        currChord = removeByNote(currChord, new Note(channel, bass_line.get(i).pitch() + 6, 100));
      }
      
      
      for (int j = prevNote - 12; j < prevNote + 12; j++) {
        if (Math.abs(j - prevNote) > 5) currChord = removeByNote(currChord, new Note(channel, j, 100));
      }
      
      
      int newPitch = pickfromList(currChord).pitch() + 12;
      Note NoteToAdd = new Note(channel, newPitch, 100, 1);
      score.addNote(TIME*i, NoteToAdd.pitch(), 100, TIME);
      
      int dif = (NoteToAdd.pitch() - bass_line.get(i).pitch())%12;
      if (dif == 7 || dif == 6){
        prevInterval = 5;
      }
      else if (dif == 0){
        prevInterval = 8;
      }
      else{
        prevInterval = -1;
      }
      
      prevNote = NoteToAdd.pitch();
      
      System.out.println("----");
      System.out.println(midiToNote(NoteToAdd.pitch()));
      System.out.println(midiToNote(bass_line.get(i).pitch()));
      
    }
    
    int secondLastPitch = TONIC.pitch() + 11;
    if (bass_line.get(bass_line.size()-2).pitch()%12 == 11) secondLastPitch = TONIC.pitch() + 14;
    
    score.addNote(TIME*(bass_line.size()-2.0), secondLastPitch, 100, TIME); 
    
    score.addNote(TIME*(bass_line.size()-1.0), TONIC.pitch() + 12, 100, TIME);
    
    
  }
  
  
  
  
  
  public ArrayList<Note> removeByNote(ArrayList<Note> arr, Note toBeRemoved){
    int n = arr.size();
    int check = 0;
    while(check < n && arr.size() > 1){
      if (arr.get(check).pitch() % 12 == toBeRemoved.pitch() % 12){
        arr.remove(check);
        check = 0;
        n = n -1;
      }
      
      check++;
    }
    
    return arr;
  }
  
  
}