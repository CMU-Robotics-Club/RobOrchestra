#include <SoftwareSerial.h>

#define LED 13

#define ComputerID 0
#define MasterID 1
#define XylobotID 2
#define FlutophoneID 3
#define BrassbotID 4
#define HihatID 5
#define BassbotID 6
#define WhamolaID 7
#define SnareID 8
#define NumID 9
#define NumInstruments 7

#define NoBoard -1
#define XylobotBoard 0
#define FlutophoneBoard 1
#define PercussionBoard 2
#define WhamolaBoard 3
#define NumBoards 4


#define STARTPIN 22
#define TXOFFSET 0
#define RXOFFSET 1
#define DIGINOFFSET 2
#define DIGOUTOFFSET 3
#define BOARDOFFSET 4

#define PACNOTE 1
#define PACADMIN 2
#define PACINST 3
#define PACREST 4
#define PACNONE 0

#define Qcap 500
#define QLcap 10
#define QFULL 0.7
#define QEMPTY 0.3

char Q[Qcap][QLcap] ;
int Qptr;
int Qlen;
char inBuffer[QLcap];
byte inBufLen;

byte play;
int mspd;
long nextAt;
long LEDoff;


SoftwareSerial boards[NumBoards] = SoftwareSerial(STARTPIN+RXOFFSET,STARTPIN+TXOFFSET);
//SoftwareSerial xyloTest = SoftwareSerial(23,22);

byte boardByID[NumInstruments];
byte enableByID[NumInstruments];

void setup(){
  
  Serial.begin(9600);
  
  for(int i = 0; i < NumBoards; ++i){
    pinMode(STARTPIN+(i*BOARDOFFSET)+TXOFFSET,OUTPUT);
    pinMode(STARTPIN+(i*BOARDOFFSET)+RXOFFSET,INPUT);
    pinMode(STARTPIN+(i*BOARDOFFSET)+DIGOUTOFFSET,OUTPUT);
    pinMode(STARTPIN+(i*BOARDOFFSET)+DIGINOFFSET,INPUT);
    boards[i] = SoftwareSerial(STARTPIN+(i*BOARDOFFSET)+RXOFFSET,STARTPIN+(i*BOARDOFFSET)+TXOFFSET);
    boards[i].begin(9600);
  }
  
  pinMode(LED,OUTPUT);
  digitalWrite(LED,LOW);
  
  boardByID[ComputerID] = NoBoard;
  boardByID[MasterID] = NoBoard;
  boardByID[XylobotID] = XylobotBoard;
  boardByID[FlutophoneID] = FlutophoneBoard;
  boardByID[HihatID] = PercussionBoard;
  boardByID[BassbotID] = PercussionBoard;
  boardByID[WhamolaID] = WhamolaBoard;
  boardByID[SnareID] = PercussionBoard;
  
  
  for(int i = 0; i < NumInstruments; ++i){
    enableByID[i] = 1;
  }

  Qptr = 0;
  Qlen = 0;

  play = 0;
  mspd = 32;
  nextAt = millis();
  LEDoff = millis();
  
  
  
}

void loop(){
  
  boardByID[WhamolaID] = WhamolaBoard;
  boardByID[SnareID] = PercussionBoard;
  
  if(Serial.available()){
    readSerial();
  }
  if(play > 0 && millis() > nextAt && Qlen > 0){
    playDiv();
  }
  if(digitalRead(LED) == HIGH && millis() > LEDoff){
    digitalWrite(LED,LOW);
  }
}

void readSerial(){
  if(!(Serial.available())) return;
  inBuffer[0] = Serial.read();
  inBufLen = 1;
  if(getPacketType(inBuffer[0]) <= 0) return;
  if(getPacketType(inBuffer[0]) == PACREST){
    addToQ(inBuffer);
    return;
  }
  while(getPacketType(inBuffer[inBufLen-1]) >= 0){
    while(!(Serial.available()));
    inBuffer[inBufLen] = Serial.read();
    inBufLen++;
    if(inBufLen >= QLcap) return;
  }
  //now that we have legit packet, we need to do something
  if(inBuffer[1] - '0'== MasterID){
    if(getPacketType(inBuffer[0]) == PACINST) parseMasterInstant();
    if(getPacketType(inBuffer[0]) == PACADMIN) parseMasterAdmin();
  } else if(inBuffer[1] - '0' > MasterID && getPacketType(inBuffer[0]) == PACINST){
      sendPacket(inBuffer);
  } else if(inBuffer[1] - '0' > MasterID){
    
      addToQ(inBuffer);
  }
}

void playDiv(){
  nextAt = millis() + mspd;
  while(Qlen > 0 && getPacketType(Q[Qptr][0]) != PACREST){
    sendPacket(Q[Qptr]);
    Qptr = (Qptr+1)%Qcap;
    Qlen--;
    if(Qlen < (Qcap*QEMPTY)){
      Serial.print("A");//start sending
    }
  }
  Qptr = (Qptr+1)%Qcap;//get rid of '.'
  Qlen--;
}

void addToQ(char packet[]){
  if(Qlen > (Qcap*QFULL)){
    Serial.print("B");//stop sending
  }
  if(Qlen >= Qcap) return;
  for(int i = 0; i < QLcap; ++i){
    Q[(Qptr+Qlen)%Qcap][i] = packet[i];
  }
  Qlen++;
}
void sendPacket(char packet[]){
  

  byte boardID = boardByID[packet[1]-'0'];
  for(int i = 0; i < QLcap; ++i){
    boards[boardID].print(packet[i]);
    if(getPacketType(packet[i]) < 0) return;
  }
}

void parseMasterInstant(){
  switch(inBuffer[2]){
    case 'A'://play
      play = 1;
      if(Qlen < (Qcap*QFULL)){
        Serial.print("A");//start sending
      } else {
        Serial.print("B");//stop sending
      }
      break;
    case 'B'://pause
      play = 0;
      break;
    case 'C'://stop
      play = 0;
      Qptr = 0;
      Qlen = 0;
      break;
    default:
      break;
  }
}
void parseMasterAdmin(){
  switch(inBuffer[2]){
    case 'A'://poll
      Serial.print("{0A}");
      break;
    case 'B'://set division
      mspd = inBuffer[5]-'A';
      mspd += (inBuffer[4]-'A')*16;
      mspd += (inBuffer[3]-'A')*256;
      digitalWrite(LED,HIGH);
      LEDoff = millis()+500;
      break;
  }
}

int getPacketType(char c){
  switch(c){
    case '[':
      return PACNOTE;
    case '{':
      return PACADMIN;
    case '(':
      return PACINST;
    case ']':
      return (PACNOTE * -1);
    case '}':
      return (PACADMIN * -1);
    case ')':
      return (PACINST * -1);
    case '.':
      return PACREST;
    default:
      return PACNONE;
  }
}
