#include <ROsolenoid.h>
#include <ROcomms.h>

#define H_ID 5
#define B_ID 6
#define S_ID 8
#define numID 3

#define P_H_OPEN 4
#define P_H_CLOSED 5
#define P_H_S1 8
#define P_H_S2 9
#define P_B_RETRACT 6
#define P_B_EXTEND 7
#define P_S_HIT 12
#define P_L 13

#define H_S_DELAY 20
#define H_F_DELAY 80
#define B_F_DELAY 100
#define S_DELAY 10
#define L_DELAY 100

#define RETRACT 0
#define EXTEND 1
#define OPEN 0
#define CLOSED 1

byte ID[3] = {H_ID,B_ID,S_ID}; //hi-hat, bassbot, snare

ROcomms com;

ROsolenoid H_F[2];
ROsolenoid H_S[2];
ROsolenoid B_F[2];
ROsolenoid S;
ROsolenoid L;

byte s_H_F;

void setup(){
  com = ROcomms(ID,numID,parseData);
  
  H_F[OPEN] = ROsolenoid(P_H_OPEN);
  H_F[CLOSED] = ROsolenoid(P_H_CLOSED);
  H_S[0] = ROsolenoid(P_H_S1);
  H_S[1] = ROsolenoid(P_H_S2);
  B_F[RETRACT] = ROsolenoid(P_B_RETRACT);
  B_F[EXTEND] = ROsolenoid(P_B_EXTEND);
  S = ROsolenoid(P_S_HIT);
  L = ROsolenoid(P_L);
  
  s_H_F = OPEN;
  H_F[OPEN].setState(HIGH);
  H_F[CLOSED].setState(LOW);
  H_S[0].setState(LOW);
  H_S[1].setState(LOW);
  B_F[RETRACT].setState(HIGH);
  B_F[EXTEND].setState(LOW);
  S.setState(HIGH);
  L.setState(LOW);
}



void loop() {
  com.loop();
  H_F[0].loop();
  H_F[1].loop();
  H_S[0].loop();
  H_S[1].loop();
  B_F[0].loop();
  B_F[1].loop();
  S.loop();
  L.loop();
}

void parseData(byte ID, int type, char* data, byte len){
  switch(ID){
  case H_ID:
    if(H_F[CLOSED].getState() == HIGH) return;
    H_F[OPEN].setTime(LOW,H_F_DELAY);
    H_F[CLOSED].setTime(HIGH,H_F_DELAY);
    L.setTime(HIGH,L_DELAY);
    return;
  case B_ID:
    if(B_F[EXTEND].getState() == HIGH) return;
    B_F[RETRACT].setTime(LOW,B_F_DELAY);
    B_F[EXTEND].setTime(HIGH,B_F_DELAY);
    L.setTime(HIGH,L_DELAY);
    return;
  case S_ID:
    S.setTime(LOW,S_DELAY);
    L.setTime(HIGH,L_DELAY);
    return;
  }
}


