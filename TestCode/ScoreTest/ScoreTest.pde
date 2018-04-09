import arb.soundcipher.*;

void setup(){
  SCScore score = new SCScore();
  for(double x = 0; x < 12; x++){
    score.addNote(0.5*x, 60+x, 100, 0.5);
  }
  score.writeMidiFile(dataPath("test.mid"));
  score.play();
}

void loop(){
  //Does nothing; waits for score to finish then keeps looping forever
}
