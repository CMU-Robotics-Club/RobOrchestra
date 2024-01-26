public class HMM<T extends Comparable<T>>{
  public ArrayList<T> objects;
  public ArrayList<State> states;
  public double[][] probs;
  public double[][] probsToStates;
  //Constructor for if you already did all the hard work
  public HMM(ArrayList<T> o, double[][]p){
    objects = o;
    probs = p;
  }
  
  //Constructor if you've got a list of states and transitions
  //Bad variable names; copy/pasted from music chord Markov chain
  public HMM(ArrayList<T> chords, ArrayList<ArrayList<T>> transitions, ArrayList<State> statesIn, ArrayList<ArrayList<State>> transitionsToStates){
    for(int x = 0; x < chords.size(); x++){
       for(int y = 1; y < chords.size(); y++){
         //Bubble-sort chords; move transitions accordingly
         //Could probably merge sort instead, but didn't want to implement that
         if((chords.get(y)).compareTo(chords.get(y-1))<0){
            T temp = chords.get(y);
            chords.set(y, chords.get(y-1));
            chords.set(y-1, temp);
            ArrayList templ = transitions.get(y);
            transitions.set(y, transitions.get(y-1));
            transitions.set(y-1, templ);
            templ = transitionsToStates.get(y);
            transitionsToStates.set(y, transitionsToStates.get(y-1));
            transitionsToStates.set(y-1, templ);
         }
       }
    }
    objects = chords;
    //Compute probabilities based on list of transitions
    probs = new double[chords.size()][chords.size()];
    for(int x = 0; x < chords.size(); x++){
      int total = transitions.get(x).size();
      if(total == 0){
        //Obviously, if there are no transitions, probability of switching to a given state is undefined
        println("Error: No transitions from " + chords.get(x));
        probs[x][0] = 1; //So arbitrarily always go to first state
      }
      for(int y = 0; y < total; y++){
        probs[x][chords.indexOf(transitions.get(x).get(y))] += 1.0/total;
      }
    }
    states = statesIn;
    for(int x = 0; x < states.size(); x++){
       for(int y = 1; y < states.size(); y++){
         //Bubble-sort chords; move transitions accordingly
         //Could probably merge sort instead, but didn't want to implement that
         if((states.get(y)).compareTo(states.get(y-1))<0){
            State temp = states.get(y);
            states.set(y, states.get(y-1));
            states.set(y-1, temp);
         }
       }
    }
    //Compute probabilities based on list of transitions
    System.out.println("states size: " + states.size());
    probsToStates = new double[chords.size()][states.size()];
    for(int x = 0; x < chords.size(); x++){
      int total = transitionsToStates.get(x).size();
      if(total == 0){
        //Obviously, if there are no transitions, probability of switching to a given state is undefined
        println("Error: No transitions from " + chords.get(x));
        probsToStates[x][0] = 1; //So arbitrarily always go to first state
      }
      for(int y = 0; y < total; y++){
        //System.out.println(states);
        //System.out.println(transitionsToStates.get(x).get(y));
        //System.out.println(transitionsToStates.get(x));
        probsToStates[x][states.indexOf(transitionsToStates.get(x).get(y))] += 1.0/total;
      }
    }
  }
  
  T getNext(T chord){
    //Using distribution from probs, pick a next chord and send it out
    double rand = Math.random();
    int i = objects.indexOf(chord);
    //Remember, probs is an array of arrays
    for(int x = 0; x < probs[i].length; x++){
      //Pick a new state index by subtracting the corresponding probs from the random number until we hit 0
      rand -= probs[i][x];
      if(rand <= 0){
        //Return the state at the picked index once we hit 0
        return objects.get(x);
      }
    }
    //Should never get here, but if we do:
    println("Error picking next state. Returning the first one for no good reason");
    return objects.get(0);
  }
  
  State getNote(T chord)
  {
    double rand = Math.random();
    int i = objects.indexOf(chord);
    //Remember, probs is an array of arrays
    for(int x = 0; x < probsToStates[i].length; x++){
      //Pick a new state index by subtracting the corresponding probs from the random number until we hit 0
      rand -= probsToStates[i][x];
      if(rand <= 0){
        //Return the state at the picked index once we hit 0
        return states.get(x);
      }
    }
    //Should never get here, but if we do:
    println("Error picking next state. Returning the first one for no good reason");
    return states.get(0);
  }
}
