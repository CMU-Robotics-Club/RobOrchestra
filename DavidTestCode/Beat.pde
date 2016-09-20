public class Beat{
   
   //These should probably be private, but I'll leave them as public for convenience
   public int nsubbeats; //Number of subbeats we're "supposed" to have
   public int arrlength; //Actual array length for convenience (generally stays constant)
   public ArrayList<Note>[] notes;
   public ArrayList<String>[] notetext;
   
   public Beat(){
       nsubbeats = 1;
       arrlength = 1;
       notes = new ArrayList[1];
       notes[0] = new ArrayList<Note>();
       getTextFromNotes();
       return;
   }
   public Beat(int n, ArrayList<Note>[] nnotes){
       nsubbeats = n;
       notes = nnotes;
       arrlength = nnotes.length;
       getTextFromNotes();
       return;
   }
   public Beat(int n, ArrayList<Note>[] nnotes, ArrayList<String>[] nnotetext){
       nsubbeats = n;
       notes = nnotes;
       arrlength = nnotes.length;
       notetext = nnotetext;
       return;
   }
   public Beat(int n, int a, ArrayList<Note>[] nnotes){
       nsubbeats = n;
       arrlength = a;
       notes = nnotes;
       getTextFromNotes();
       return;
   }
   public Beat(int n, int a, ArrayList<Note>[] nnotes, ArrayList<String>[] nnotetext){
       nsubbeats = n;
       arrlength = a;
       notes = nnotes;
       notetext = nnotetext;
       return;
   }
   
   public void getTextFromNotes(){
      notetext = new ArrayList[arrlength];
      for(int x = 0; x < notes.length; x++){
          notetext[x] = new ArrayList<String>();
          for(int y = 0; y < notes[x].size(); y++){
             notetext[x].add("" + notes[x].get(y).pitch()); 
          }
      }
   }
}