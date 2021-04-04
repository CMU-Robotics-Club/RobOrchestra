//Write fx, noteToPos, that sets the linear actuator to the correct note location given a string
/*@param: int note: Represents MIDI note number (ex. C4 is 60)
 *@param: str s: Represents a ukelele string (G, C, E, or A)
 *@return: int status: 0 on success, -1 on failure
 */
//Note: Strings are G4 - C4 - E4 - A4
//Assume 12 frets/string: return -1 if out of range
//For now: assume equal spacing inbetween notes. That is, Each fret is 1024/12 units
//Use interface functions found in linearactuator_single_test.ino (Will clean this up later)


//WIRING CONSTANTS
const int gPot = A3; //pot for G string
const int cPot = A0; //pot for C string
const int ePot = A1; //pot for E string
const int aPot = A2; //pot for A string


const int gMotIn = 42; //mot for G string
const int cMotIn = 34; //mot for C string
const int eMotIn = 30; //mot for E string
const int aMotIn = 38; //mot for A string

const int gMotOut = 44; //mot for G string
const int cMotOut = 36; //mot for C string
const int eMotOut = 32; //mot for E string
const int aMotOut = 40; //mot for A string

const int gPWMA = 2; //PWMA for G string
const int cPWMA = 4; //PWMA for C string
const int ePWMA = 5; //PWMA for E string
const int aPWMA = 3; //PWMA for A string

const int IN1[] = {gMotIn, cMotIn, eMotIn, aMotIn};
const int IN2[] = {gMotOut, cMotOut, eMotOut, aMotOut};

enum str {
  G, C, E, A
};

int PWM[]= {gPWMA, cPWMA, aPWMA, ePWMA};

const int feedbackB = A0; //potentiometer from actuator A0
const int feedbackA = A1; //potentiometer from actuator A1
const int feedbackC = A3;
const int feedbackD = A2;
const int feedback[]= {feedbackA, feedbackB, feedbackC, feedbackD};

void setup()
{
  pinMode(feedback[1], INPUT);//feedback from actuator
  pinMode(PWM[1], OUTPUT);
  pinMode(IN1[1], OUTPUT);
  pinMode(IN2[1], OUTPUT);

  pinMode(feedback[0], INPUT);//feedback from actuator
  pinMode(PWM[0], OUTPUT);
  pinMode(IN1[0], OUTPUT);
  pinMode(IN2[0], OUTPUT);

   pinMode(feedback[2], INPUT);//feedback from actuator
  pinMode(PWM[2], OUTPUT);
  pinMode(IN1[2], OUTPUT);
  pinMode(IN2[2], OUTPUT);

  pinMode(feedback[3], INPUT);//feedback from actuator
  pinMode(PWM[3], OUTPUT);
  pinMode(IN1[3], OUTPUT);
  pinMode(IN2[3], OUTPUT);

  Serial.begin(9600);

}
void loop(){
    int note= 65;  //test note
    noteToPos(note);
//broken    fwd(50, C);
//broken    fwd(50, G);
}

str noteToString(int note) {
  int strings = 4;
  int bases[strings] = {67, 60, 64, 69};
  int smallest;
  for (int i = 0; i < strings; i++) {
    int diff = note - bases[i];
    if (diff < smallest && diff >= 0) {
      smallest = bases[i];
    }
  }
  
  if (smallest == bases[0]) {
    return G;
  }
  else if (smallest == bases[1]) {
    return C;
  }
  else if (smallest == bases[2]) {
    return E;
  }
  else if (smallest == bases[3]) {
    return A;
  }
}

int noteToPos(int note) {
  str s = noteToString(note);
  //Serial.println(s);
  
  if (s == G && note >= 67 && note <= 79){
    return moveToPos(note, s, 67);
  }
  else if (s == C && note >= 60 && note <= 72){
    return moveToPos(note, s, 60);
  }
  else if (s == E && note >= 64 && note <= 76){
    return moveToPos(note, s, 64);
  }
  else if (s == A && note >= 69 && note <= 81){
    return moveToPos(note, s, 69);
  }
  return -1;
}

int moveToPos(int note, str s, int lowest) {
  int pos;
  switch(s){
    case G:
      pos = analogRead(gPot); //pot for G string
      break;
    case C:
      pos = analogRead(cPot); //pot for C string
      break;
    case E:
      pos = analogRead(ePot); //pot for E string
      break;
    case A:
      pos = analogRead(aPot); //pot for A string
      break;
  }
  int target = (note - lowest) * 1024 / 12;
  Serial.println("pos, target: ");
  Serial.println(pos);
  Serial.println(target);
  while (abs(pos - target) > 50) {
    if (pos > target) {
      rev(1, s); //50 is arbitrary speed
    }
    else {
      fwd(1, s);
    }

    Serial.println("pos, target: ");
    Serial.println(pos);
    Serial.println(target);
    
    switch(s){
      case G:
        pos = analogRead(gPot); //pot for G string
        break;
      case C:
        pos = analogRead(cPot); //pot for C string
        break;
      case E:
        pos = analogRead(ePot); //pot for E string
        break;
      case A:
        pos = analogRead(aPot); //pot for A string
        break;
    }
  }
  brake(s);
  return 0;
}

void fwd(int speedS, str s)
{
  int AIN1 = 0;
  int AIN2 = 0;
  int PWMA = 0;
    switch(s){
    case G:
      AIN1 = gMotIn;
      AIN2 = gMotOut;
      PWMA = gPWMA;
      break;
    case C:
      AIN1 = cMotIn;
      AIN2 = cMotOut;
      PWMA = cPWMA;
      break;
    case E:
      AIN1 = eMotIn;
      AIN2 = eMotOut;
      PWMA = ePWMA;   
      break;
    case A:
      AIN1 = aMotIn;
      AIN2 = aMotOut;
      PWMA = aPWMA;  
      break;
  }
  digitalWrite(AIN1, HIGH);
  digitalWrite(AIN2, LOW);
  analogWrite(PWMA, speedS);
}
void rev(int speedS, str s)
{ 
  int AIN1 = 0;
  int AIN2 = 0;
  int PWMA = 0;
    switch(s){
    case G:
      AIN1 = gMotIn;
      AIN2 = gMotOut;
      PWMA = gPWMA;
      break;
    case C:
      AIN1 = cMotIn;
      AIN2 = cMotOut;
      PWMA = cPWMA;
      break;
    case E:
      AIN1 = eMotIn;
      AIN2 = eMotOut;
      PWMA = ePWMA;
      break;
    case A:
      AIN1 = aMotIn;
      AIN2 = aMotOut;
      PWMA = aPWMA;
      break;
  }
  digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, HIGH);
  analogWrite(PWMA, speedS);
}

void brake(str s)
{ 
  int AIN1 = 0;
  int AIN2 = 0;
  int PWMA = 0;
  
    switch(s){
    case G:
      AIN1 = gMotIn;
      AIN2 = gMotOut;
      PWMA = gPWMA;
      break;
    case C:
      AIN1 = cMotIn;
      AIN2 = cMotOut;
      PWMA = cPWMA;
      break;
    case E:
      AIN1 = eMotIn;
      AIN2 = eMotOut;
      PWMA = ePWMA;
      break;
    case A:
      AIN1 = aMotIn;
      AIN2 = aMotOut;
      PWMA = aPWMA;
      break;
  }
  digitalWrite(AIN1, HIGH);
  digitalWrite(AIN2, HIGH);
  analogWrite(PWMA, 0);
}
