import themidibus.*; //Import midi library
import java.lang.Math; //To get random numbers

MidiBus myBus;
int channel = 0;
int velocity = 120;
int notelen = 1000;
int pitch = 59;

void setup(){
    myBus = new MidiBus(this, 0, 1);
}

void draw(){
   Note note = new Note(channel, pitch, velocity);
   myBus.sendNoteOn(note);
   delay(notelen);
   myBus.sendNoteOff(note);
   pitch = (pitch + 1)%12 + 60;
}

//processes delay in milliseconds
void delay(int time) {
  int current = millis();
  while (millis () < current+time){
    Thread.yield();
  } 
}