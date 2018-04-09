import arb.soundcipher.*;

void setup(){
  SCScore score = new SCScore();
  for(double x = 0; x < 12; x++){
    score.addNote(0.5*x, 60+x, 100, 0.5);
  }
  //Don't have to add things in timestamp order; this is good.
  for(double x = 0; x < 12; x++){
    score.addNote(0.5*x, 64+x, 100, 0.5);
  }
  score.writeMidiFile(dataPath("test.mid"));
  //NOTE: score.play() doesn't have built-in delay!!!
  score.play(); //Should play chromatic chord things.
}

void loop(){
  //Does nothing; waits for score to finish then keeps looping forever
}
