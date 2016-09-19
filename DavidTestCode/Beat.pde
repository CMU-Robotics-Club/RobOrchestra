public class Beat{
   int nsubbeats;
   ArrayList<Note>[] notes;
   public Beat(){
       nsubbeats = 1;
       notes = new ArrayList[1];
       return;
   }
   public Beat(int n, ArrayList<Note>[] nnotes){
       nsubbeats = n;
       notes = nnotes;
       return;
   }
   
   //I'd like a function to generate a beat
   //runSubbeat() generates melody notes on appropriate subbeats
   //chooseChord() picks the next chord, then calls playChord
   //playChord() plays the chord and picks the subbeat length
   //So... hack together bits and pieces of all of these to generate a beat?
}