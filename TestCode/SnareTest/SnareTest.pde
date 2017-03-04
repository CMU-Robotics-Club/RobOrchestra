import themidibus.*;

int snare = 38;
int in = 0;
int out = 4;
MidiBus snareBus;
Note test;
int channel = 3;
int counter = 0;

void setup() {
  MidiBus.list();
  snareBus = new MidiBus(this, in, out);
  snareBus.addOutput(1);
}

void draw() {
  if(counter == 1) snare = 37;
  if(counter == 2) snare = 38;
  if(counter == 3) {
    counter = 0;
  }
  test = new Note(channel, snare, 100, 500);
  //snareBus.sendMessage(0x91, 30, 100);
  //test = new Note(0, 60, 100, 500);
  snareBus.sendNoteOn(test);
  delay(500);
  counter++;
}