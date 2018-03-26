import themidibus.*;

int snare = 37;
int in = 0;
MidiBus snareBus;
Note test;
int channel = 0;

void setup() {
  MidiBus.list();
  snareBus = new MidiBus(this, in, 1);
}

void draw() {
  test = new Note(0, 37, 100);
  snareBus.sendNoteOn(test);
  println("Note");
  delay(500);
  snareBus.sendNoteOff(test);
}