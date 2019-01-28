import themidibus.*;

MidiBus drumPlayer;
boolean[] bass = {true, false, false, false, true, false, false, false};
boolean[] hiHat = {false, false, true, false, false, false, true, false};
boolean[] snare = {true, true, true, true, true, true, true, true};
int beatCount = 0;
int numBeats = 8;
int beatLength = 500;

int drumChannel = 10;
int input = 0;
int output = 1;

void setup(){
  size(200,200);
  background(0);
  
  MidiBus.list();
  
  drumPlayer = new MidiBus(this, input, output);
}

void draw() {
  if(bass[beatCount]){
    drumPlayer.sendMessage(0x9c, drumChannel, 38, 100);
  }
  if(hiHat[beatCount]){
    drumPlayer.sendMessage(0x9c, drumChannel, 42, 100);
  }
  if(snare[beatCount]){
    drumPlayer.sendMessage(0x9c, drumChannel, 36, 100);
  }
  
  if(beatCount == 7) beatCount = 0;
  else beatCount++;
  
  delay(beatLength);
}