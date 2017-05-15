import themidibus.*;

int snare = 37;
int in = 0;
int out = 4;
MidiBus snareBus;
Note test;
int channel = 0;

void setup() {
  MidiBus.list();
  snareBus = new MidiBus(this, in, 1);
}

void draw() {
  test = new Note(0, 37, 100);
  //snareBus.sendMessage(0x91, 30, 100);
  //test = new Note(0, 60, 100, 500);
  snareBus.sendNoteOn(test);
  delay(500);
}