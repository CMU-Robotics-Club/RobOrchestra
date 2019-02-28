public class Measure{
  int nbeats;
  Beat[] beats;
  ArrayList<OutputTuple> output;
  public Measure(){
      nbeats = 4;
      beats = new Beat[nbeats];
      for(int x = 0; x < nbeats; x++){
        beats[x] = new Beat(); 
      }
      output = new ArrayList();
      return;
  }
  public Measure(int b){
      nbeats = b;
      beats = new Beat[nbeats];
      for(int x = 0; x < nbeats; x++){
        beats[x] = new Beat(); 
      }
      output = new ArrayList();
      return;
  }
  
  public void setBeat(int i, Beat b){
      if(i < 0 || i >= nbeats) return;
      beats[i] = b;
  }
  public Beat getBeat(int i){
      if(i < 0 || i >= nbeats) return null;
      return beats[i];
  }
  public void addOutput(String s, int i){
    output.add(new OutputTuple(s, i));
  }
  
  public String toString(){
     String temp = "New measure: \nNumber of beats: " + nbeats + "\n\n";
     for(int x = 0; x < nbeats; x++){
        temp+=beats[x].toString() + "\n";
     }
     return temp;
  }
}