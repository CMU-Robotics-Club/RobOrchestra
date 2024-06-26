public class MarkovChainState {
  public ArrayList<State> objects;
  public double[][] probs;
  
  //Cleanest way to do this?
  //Need to keep all states distinct (may have different chords)
  //Regenerate transition matrices each time? That's horrible... maybe do it anyway?
  
  //Okay, so assume we've magically got a list of which state goes to which other state...
  //If we were smart, we'd sort the states and only sample from those
  //If we weren't, we'd randomly sample any state, check if the pre-state meets the conditions, resample if not. This is probably not sustainable.
  
  //We need some kind of database thing, really...
  
  //Okay, so what are we sorting on? Care about pitch only, pitch+delay, pitch+delay+length
  //Want, for each combination of pitch, pitch+delay, etc, a list of all states with those attributes
  //How would I make this? Loop through all states, for each combination if the combination exists add to that list, if not don't
  //Really looks like this part goes in the MIDIReader class
  //Need a list of combinations, a list of states that satisfy each combination, a list of combo->combo transitions
  
  //So pretend that's done, then need a getNext for each combination
  //Sample from the combo->combo matrix to get the next state, then sample from the combo->states list for the next state
  
  //Constructor for if you already did all the hard work
  public MarkovChainState(ArrayList<State> o, double[][]p){
    objects = o;
    probs = p;
  }
  
  //Constructor if you've got a list of states and transitions
  //Bad variable names; copy/pasted from music note Markov chain
  public MarkovChainState(ArrayList<State> notes, ArrayList<ArrayList<State>> transitions){
    for(int x = 0; x < notes.size(); x++){
       for(int y = 1; y < notes.size(); y++){
         //Bubble-sort notes; move transitions accordingly
         //Could probably merge sort instead, but didn't want to implement that
         if((notes.get(y)).compareTo(notes.get(y-1))<0){
            State temp = notes.get(y);
            notes.set(y, notes.get(y-1));
            notes.set(y-1, temp);
            ArrayList templ = transitions.get(y);
            transitions.set(y, transitions.get(y-1));
            transitions.set(y-1, templ);
         }
       }
    }
    objects = notes;
    //Compute probabilities based on list of transitions
    probs = new double[notes.size()][notes.size()];
    for(int x = 0; x < notes.size(); x++){
      int total = transitions.get(x).size();
      if(total == 0){
        //Obviously, if there are no transitions, probability of switching to a given state is undefined
        println("Error: No transitions from " + notes.get(x));
        probs[x][0] = 1; //So arbitrarily always go to first state
      }
      for(int y = 0; y < total; y++){
        probs[x][notes.indexOf(transitions.get(x).get(y))] += 1.0/total;
      }
    }
  }
  
 State getNext(State note){
    //Using distribution from probs, pick a next note and send it out
    double rand = Math.random();
    int i = objects.indexOf(note);
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
}
