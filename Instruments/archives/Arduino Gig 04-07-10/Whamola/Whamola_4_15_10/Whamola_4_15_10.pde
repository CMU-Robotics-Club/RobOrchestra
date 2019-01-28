#include <ROcomms.h>

#define P_LED 13
#define P_P_PWM 8
#define P_T_PWM 9
#define P_P_A 22
#define P_P_B 23
#define P_T_A 24
#define P_T_B 25

#define P_P_IN 0
#define P_T_IN 8

#define P_Speed 100
#define P_Time 100
#define T_Speed 100

#define DIR_Tension 1
#define DIR_Loosen -1

#define S_zero 0
#define S_ready 1
#define S_startPick 2
#define S_endPick 3
#define P_ir_close 100
#define P_ir_done 120
#define P_speed_far 100
#define P_speed_close 15
#define P_delay_H 80
#define P_delay_Z 30
#define P_delay_B 180

#define T_max 910
#define T_min 390
#define T_pot_close 70
#define T_pot_done 5
#define T_speed_far 100
#define T_speed_close 25

#define PAC_getT 0 //'A'
#define PAC_getH 1 //etc
#define PAC_setT 2
#define PAC_setH 3
#define PAC_toggleP 4

#define NumNotes 11

int notes[NumNotes] = {400,450,500,550,600,650,700,750,800,850,900};

ROcomms com;

byte ID = 7;

int note;
byte P_stage;
long P_time;

byte D_print;

void setup(){
  com = ROcomms(&ID,1,parseData);
  pinMode(P_P_PWM,OUTPUT);
  pinMode(P_T_PWM,OUTPUT);
  pinMode(P_P_A,OUTPUT);
  pinMode(P_P_B,OUTPUT);
  pinMode(P_T_A,OUTPUT);
  pinMode(P_T_B,OUTPUT);
  pinMode(P_P_IN,INPUT);
  pinMode(P_T_IN,INPUT);
  
  note = notes[2];
  P_stage = S_zero;
  P_time = 1;
  setTensionSpeed(0);
  setPickSpeed(0);
  
  D_print = 0;
  
  delay(200);
}

void loop(){
  com.loop();
  T_loop();
  P_loop();
  if(D_print == 1) printInputs();
}

void T_loop(){
  if(getT() > note){//too tense
    if(getT() > note + T_pot_close){
      setTensionSpeed(DIR_Loosen*T_speed_far);
    } else if(getT() > note + T_pot_done){
      setTensionSpeed(DIR_Loosen*T_speed_close);
    } else {
      setTensionSpeed(0);
    }
  } else if(getT() < note){//not tense enough
    if(getT() < note - T_pot_close){
      setTensionSpeed(DIR_Tension*T_speed_far);
    } else if(getT() < note - T_pot_done){
      setTensionSpeed(DIR_Tension*T_speed_close);
    } else {
      setTensionSpeed(0);
    }
  }
}
void P_loop(){
  switch(P_stage){
  case S_zero:
    if(getP() > P_ir_done){
      setPickSpeed(0);
      P_stage = S_ready;
      return;
    }
    setPickSpeed(P_speed_close);
    return;
  case S_ready:
    setPickSpeed(0);
    return;
  case S_startPick:
    setPickSpeed(P_speed_far);
    if(P_time > 0 && P_time < millis()){
      P_stage = S_endPick;
      P_time = millis() + P_delay_B;
      setPickSpeed(-1*P_speed_close);
    }
    return;
  case S_endPick:
    setPickSpeed(-1*P_speed_close);
    if(P_time < millis()){
      P_stage = S_zero;
      P_time = 0;
      setPickSpeed(P_speed_close);
    }
    return;
  default:
    setPickSpeed(0);
  }
}




void parseData(byte ID, int type, char* data, byte len){
  switch(type){
  case PACNOTE:
    if(len < 2) return;
    if(data[1]-'A' >= 0 && data[1]-'A' < NumNotes){
      note = notes[data[1]-'A'];
      P_time = millis() + P_delay_H;
      if(P_stage != S_ready){
        P_time += P_delay_Z;
      }
      P_stage = S_startPick;
    }
    break;
  case PACADMIN:
    parseAdmin(data,len);
  }
}
void parseAdmin(char* data, byte len){
  if(len < 1) return;
  byte type = data[0]-'A';
  switch(type){
  case PAC_getT:
    com.print("TENSION (POT): ");
    com.print(getT());
    com.print("/");
    com.print(note);
    com.print(" [");
    com.print(T_min);
    com.print(",");
    com.print(T_max);
    com.println("]");
    break;
  case PAC_getH:
    com.print("PICWHEEL (IR): ");
    com.print(getP());
    com.print("/");
    com.println(P_ir_done);
    break;
  case PAC_setT:
    if(len < 4) com.println("IMPROPER INPUT");
    note = (100*(data[1]-'0')) + (10*(data[2]-'0')) + (data[3]-'0');
    break;
  case PAC_setH:
    P_time = millis() + P_delay_H;
    P_stage = S_startPick;
    break;
  case PAC_toggleP:
    D_print = (D_print==1)?0:1;
    break;
  }
}

void setPickSpeed(int s){//[0,100]
  if(s < -100 || s > 100) return;
  if(s == 0){
    digitalWrite(P_P_A,LOW);
    digitalWrite(P_P_B,LOW);
    analogWrite(P_P_PWM,0);
    return;
  } 
  if(s > 0){
    digitalWrite(P_P_A,LOW);
    digitalWrite(P_P_B,HIGH);
  } else if(s < 0){
    digitalWrite(P_P_A,HIGH);
    digitalWrite(P_P_B,LOW);
  }
  analogWrite(P_P_PWM,map(abs(s),0,100,0,255));
}
void setTensionSpeed(int s){
  if(s < -100 || s > 100) return;
  if(s > 0 && getT() < T_max){
    digitalWrite(P_T_A,HIGH);
    digitalWrite(P_T_B,LOW);
  } else if(s < 0 && getT() > T_min){
    digitalWrite(P_T_A,LOW);
    digitalWrite(P_T_B,HIGH);
  } else {
    digitalWrite(P_T_A,LOW);
    digitalWrite(P_T_B,LOW);
    analogWrite(P_T_PWM,0);
    return;
  }
  analogWrite(P_T_PWM,map(abs(s),0,100,0,255));
}

int getT(){
  return (1023-analogRead(P_T_IN));
}
int getP(){
  return analogRead(P_P_IN);
}

void printInputs(){
  com.print("POT: ");
  com.print(getT());
  com.print("/");
  com.print(note);
  com.print("\t\t\tPIC: ");
  com.print(getP());
  com.print("/");
  com.print(P_ir_done);
  com.println("");
}
