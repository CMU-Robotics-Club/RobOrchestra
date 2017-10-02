MarkovChain mc;
Comparable curnum;

void setup(){
  String s = "31415926535897932384626433832795028841971693993751";
  ArrayList<Integer> nums = new ArrayList<Integer>();
  ArrayList<ArrayList<Integer>> transitions = new ArrayList<ArrayList<Integer>>();
  Integer prevnum = new Integer(-1);
  Integer firstnum = new Integer(-1);
  for(int x = 0; x < s.length(); x++){
    Integer d = new Integer(Integer.parseInt(s.substring(x, x+1)));
    if(!nums.contains(d)){
      nums.add(d);
      transitions.add(new ArrayList<Integer>());
    }
    if(x == 0){
      firstnum = d;
    }
    else{
      //transitions is an array list of array lists
      //Get the array list corresponding to digit prevnum; tell it to add a transition to d
      //We know there's a valid previous number since we set it on the 0th loop
      transitions.get(nums.indexOf(prevnum)).add(d);
    }
    prevnum = d;
  }
  //Map last digit back to first digit
  Integer lastnum = new Integer(Integer.parseInt(s.substring(s.length()-1, s.length())));
  transitions.get(nums.indexOf(lastnum)).add(firstnum);
  
  mc = new MarkovChain(nums, transitions);
  println("This isn't actually pi, but it'll look close...");
  print("3.");
  curnum = new Integer(3);
}

void draw(){
  curnum = mc.getNext(curnum);
  print(curnum);
  delay(100);
}

//processes delay in milliseconds
void delay(int time) {
  int current = millis();
  while (millis () < current+time) Thread.yield();
}