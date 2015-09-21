#include <Servo.h>
#include <ROsolenoid.h>
#include <ROcomms.h>

#define P_RX 0
#define P_TX 1
#define P_DIGIN 2
#define P_DIGOUT 3

#define P_FIN0 4
#define NUMFIN 7
#define P_AIR 11
#define P_LED 13

#define ID 3
#define numNotes 11
#define airDelay 50

byte closed[NUMFIN] = {40,40,35,45,60,55,50};
byte open[NUMFIN] = {70,70,65,75,90,85,90};
//1=finger covering, 0=hole open
byte notes[numNotes][NUMFIN] = {{1,1,1,1,1,1,1},//NONE
                           {1,1,1,1,1,1,1},//C
                           {1,1,1,1,1,1,0},//D
                           {1,1,1,1,1,0,0},//E
                           {1,1,1,1,0,0,0},//F
                           {1,1,1,0,1,0,0},//Fs
                           {1,1,1,0,0,0,0},//G
                           {1,1,0,0,0,0,0},//A
                           {1,0,0,1,0,0,0},//Bf
                           {1,0,0,0,0,0,0},//B
                           {0,0,0,0,0,0,0}};//C

long noteTime = 0;

Servo fingers[NUMFIN];
ROsolenoid LED = ROsolenoid(P_LED);
ROsolenoid AIR = ROsolenoid(P_AIR);

ROcomms com;


void setup(){
  com = ROcomms(ID,handleData);
  for(byte i = 0; i < NUMFIN; ++i){
    fingers[i].attach(P_FIN0+i);
    fingers[i].write(closed[i]);
  }
  AIR.setState(LOW);
  LED.setState(LOW);
}

void loop(){
  com.loop();
  AIR.loop();
  LED.loop();
  checkNoteTime();
}


void handleData(int type, char* data, byte len){
  if(type == PACNOTE){
    if(len != 5) return; //should always have 5
    playNote(data[1]-'A',com.ourHexToLong(&data[2],3));
  }
}


void playNote(byte note, long duration){
  AIR.setTime(LOW,airDelay);
  LED.setTime(LOW,airDelay);
  for(byte i = 0; i < NUMFIN; ++i)//sets each finger for the note
    fingers[i].write((notes[note][i]==0)?open[i]:closed[i]);
  noteTime = millis()+duration;
}
void checkNoteTime(){
  if(noteTime == 0 || millis() < noteTime)
    return;//keeps the note playing
  //TURN OFF THE NOTE
  for(byte i = 0; i < NUMFIN; ++i)//close fingers
    fingers[i].write(closed[i]);
  AIR.setState(LOW);
  LED.setState(LOW);
}
