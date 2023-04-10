#include <MIDI.h>
#include <midi_Defs.h>
#include <midi_Namespace.h>
#include <midi_Settings.h>

#include "xylo.h"

#define MYCHANNEL 1

#define STARTNOTE 56
#define ENDNOTE 83 //Equal to the highest note
#define KEY_UP_TIME 40

MIDI_CREATE_DEFAULT_INSTANCE();

unsigned long startTime = 0;

//PWM starts on 2
#define PWMA 3
#define PWMB 3 
#define PWMC 4
#define PWMD 5

const int PWM[] = {PWMA, PWMB, PWMC, PWMD};

//AB on digital ports 30+
#define AIN1 30 //D34
#define AIN2 31//D36
#define BIN1 32
#define BIN2 33
//CD on digital ports 40+
#define CIN1 40
#define CIN2 41
#define DIN1 42
#define DIN2 43

const int IN1[] = {AIN1, BIN1, CIN1, DIN1};
const int IN2[] = {AIN2, BIN2, CIN2, DIN2};

//Potentiometer feedback stuff
const int feedbackA = A0;
const int feedbackB = A1;
const int feedbackC = A2;
const int feedbackD = A3;

const int feedback[]= {feedbackA, feedbackB, feedbackC, feedbackD};

int position_LA = 0; //potentiometer from actuator
int position_LB = 0;
int position_LC = 0;
int position_LD = 0;

int position_L[] = {position_LA, position_LB, position_LC, position_LD};

int target[] = {250, 500, 750, 500};

int mintol = 25; //Min size of dead zone (smaller means more precision but risks oscillation around target)
int maxtol = 100; //Max size of dead zone (smaller lets us move at full speed for longer but risks oscillation around target)
double tolrat = 1.1; //How fast we change the adaptive threshold. Keep this bigger than 1. Bigger means faster convergence but risks oscillation

double dt = 10/1000.0; //seconds
double tol[] = {100, 100, 100, 100};

//Going to assume same positions on all strings, TODO fix later if needed
int positions[] = {100, 200, 300, 400, 500, 600, 700}; //No open for now.

void handleNoteOn(byte channel, byte pitch, byte velocity){
  //This function queues up notes to be unplayed
  if(channel != MYCHANNEL) return; //Only play channel1
  if(velocity == 0){
    handleNoteOff(channel, pitch, velocity);
    return; //Ignore velocity 0
  }
  
  int noteIndex = pitch;
  //Rescale notes
  while(noteIndex < STARTNOTE){
    noteIndex += 12;
  }
  while(noteIndex > ENDNOTE){
    noteIndex -= 12;
  }

  int pos = positions[(noteIndex-STARTNOTE)%7];
  int string = (noteIndex-STARTNOTE)/7;
  target[string] = pos;

  //fingerNote(noteIndex);
  turnOnString(string);

  //digitalWrite(pinnumbers[noteIndex-STARTNOTE], HIGH);
  //pintimes[noteIndex-STARTNOTE] = millis();
}

void handleNoteOff(byte channel, byte pitch, byte velocity){
  //This function queues up notes to be unplayed
  if(channel != MYCHANNEL) return; //Only play channel1
  
  int noteIndex = pitch;
  //Rescale notes
  while(noteIndex < STARTNOTE){
    noteIndex += 12;
  }
  while(noteIndex > ENDNOTE){
    noteIndex -= 12;
  }

  int pos = positions[(noteIndex-STARTNOTE)%7];
  int string = (noteIndex-STARTNOTE)/7;
  target[string] = pos;

  //fingerNote(noteIndex);
  turnOffString(string);

  //digitalWrite(pinnumbers[noteIndex-STARTNOTE], HIGH);
  //pintimes[noteIndex-STARTNOTE] = millis();
}

void setup()
{
  //xylo_init();
  
  pinMode(feedback[0], INPUT);//feedback from actuator
  pinMode(PWM[0], OUTPUT);
  pinMode(IN1[0], OUTPUT);
  pinMode(IN2[0], OUTPUT);
  
  pinMode(feedback[1], INPUT);//feedback from actuator
  pinMode(PWM[1], OUTPUT);
  pinMode(IN1[1], OUTPUT);
  pinMode(IN2[1], OUTPUT);

  pinMode(feedback[2], INPUT);//feedback from actuator
  pinMode(PWM[2], OUTPUT);
  pinMode(IN1[2], OUTPUT);
  pinMode(IN2[2], OUTPUT);

  pinMode(feedback[3], INPUT);//feedback from actuator
  pinMode(PWM[3], OUTPUT);
  pinMode(IN1[3], OUTPUT);
  pinMode(IN2[3], OUTPUT);

  Serial.begin(9600);
  
  MIDI.setHandleNoteOn(handleNoteOn);
  MIDI.begin(MIDI_CHANNEL_OMNI);          // Launch MIDI and listen to channel 1
  MIDI.turnThruOn();
  startTime = millis();
}

void loop()
{
  //Check for and process new MIDI messages, then if it's time to release notes, do that
  MIDI.read();

  for(int i = 0; i < 1; i++){

    int pos = analogRead(feedback[i]);
    int err = target[i] - pos;  // read the input
    
    
    if (abs(err) < tol[i]){
      brake(i);
      if (tol[i] > mintol){
          tol[i] /= tolrat;
      }
    }
    else{
      if(err < -tol[i]){
        rev(i);
        if (tol[i] < maxtol){
          tol[i] *= tolrat;
        }
      }
      if(err > tol[i]){
        fwd(i);
        if (tol[i] < maxtol){
          tol[i] *= tolrat;
        }
      }
    }

    Serial.print(pos);
    Serial.print(" ");
    Serial.print(err);
    Serial.print(" ");
    Serial.println(tol[i]);
    
    delay(dt*1000); //milliseconds
  }

  /*for(int x = 0; x < nPins; x++){
    if(millis() - pintimes[x] > KEY_UP_TIME){
      int keyPin = pinnumbers[x]; // map the note to the pin
      digitalWrite(keyPin, LOW);
    }
  }*/
}

void turnOnString(int string){
  Serial.print("Turning on string ");
  Serial.println(string);
}

void turnOffString(int string){
  Serial.print("Turning off string ");
  Serial.println(string);
}

void fwd(int motor)
{ digitalWrite(IN1[motor], HIGH);
  digitalWrite(IN2[motor], LOW);
  analogWrite(PWM[motor], 0);
}
void rev(int motor)
{ digitalWrite(IN1[motor], LOW);
  digitalWrite(IN2[motor], HIGH);
  analogWrite(PWM[motor], 0);
}
void brake(int motor) 
{ digitalWrite(IN1[motor], HIGH);
  digitalWrite(IN2[motor], HIGH);
  analogWrite(PWM[motor], 0);
}
