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
const int gPot = A5; //pot for G string
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

int i = 0;
int counter = 0;
void setup()
{
  pinMode(gPot, INPUT);//feedback from actuator
  pinMode(PWM[1], OUTPUT);
  pinMode(IN1[1], OUTPUT);
  pinMode(IN2[1], OUTPUT);

  pinMode(cPot, INPUT);//feedback from actuator
  pinMode(PWM[0], OUTPUT);
  pinMode(IN1[0], OUTPUT);
  pinMode(IN2[0], OUTPUT);

  pinMode(ePot, INPUT);//feedback from actuator
  pinMode(PWM[2], OUTPUT);
  pinMode(IN1[2], OUTPUT);
  pinMode(IN2[2], OUTPUT);

  pinMode(aPot, INPUT);//feedback from actuator
  pinMode(PWM[3], OUTPUT);
  pinMode(IN1[3], OUTPUT);
  pinMode(IN2[3], OUTPUT);

  Serial.begin(9600);

  calibrate();

}

//int lenIntList(int someList[]) {
//  int res =  sizeof(someList) / sizeof(int);
//  Serial.println(res);
//  return res;
//}


int notesA[] = {69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81};
int notesG[] = {67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79};
int notesC[] = {60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72};
int notesE[] = {64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76};
int notesLen[] = {0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1};
int minVal[] = {0, 0, 0, 0};
int maxVal[] = {1024, 1024, 1024, 1024};
int threshRange[] = {1024, 1024, 1024, 1024};

void loop(){
    if(counter == 10){
      counter = 0;
      i = (i+1) % 26;
//      Serial.print("G: ");
//      Serial.println(analogRead(gPot));
//      Serial.print("E: ");
//      Serial.println(analogRead(ePot));
//      Serial.print("A: ");
//      Serial.println(analogRead(aPot));
//      Serial.print("C: ");
//      Serial.println(analogRead(cPot));
//      Serial.println();
    }
    else counter++;

    int pastErrors[] = {0, 0, 0, 0};
    
    noteToPos(A, notesA[notesLen[i]], pastErrors);
    noteToPos(G, notesG[notesLen[i]], pastErrors);
    noteToPos(C, notesC[notesLen[i]], pastErrors);
    noteToPos(E, notesE[notesLen[i]], pastErrors);
}

//str noteToString(int note) {
//  int strings = 4;
//  int bases[strings] = {67, 60, 64, 69};
//  int smallest;
//  for (int i = 0; i < strings; i++) {
//    int diff = note - bases[i];
//    if (diff < smallest && diff >= 0) {
//      smallest = bases[i];
//    }
//  }
//  
//  if (smallest == bases[0]) {
//    return G;
//  }
//  else if (smallest == bases[1]) {
//    return C;
//  }
//  else if (smallest == bases[2]) {
//    return E;
//  }
//  else if (smallest == bases[3]) {
//    return A;
//  }p
//}

int noteToPos(str curr, int note, int pastErrors[]) {
  str s = curr;
  
  if (s == G && note >= 67 && note <= 79){
    return moveToPos(note, s, 67, pastErrors);
  }
  else if (s == C && note >= 60 && note <= 72){
    return moveToPos(note, s, 60, pastErrors);
  }
  else if (s == E && note >= 64 && note <= 76){
    return moveToPos(note, s, 64, pastErrors);
  }
  else if (s == A && note >= 69 && note <= 81){
    return moveToPos(note, s, 69, pastErrors);
  }
  return -1;
}

int moveToPos(int note, str s, int lowest, int pastErrors[]) {
  int pos;
  int target;
  int pastError;
  switch(s){
    case G:
      pos = analogRead(gPot); //pot for G string
      pastError = pastErrors[0];
      target = (note - lowest) * threshRange[0] / 12 + minVal[0];
      break;
    case C:
      pos = analogRead(cPot); //pot for C string
      pastError = pastErrors[1];
      target = (note - lowest) * threshRange[1] / 12 + minVal[1];
      break;
    case E:
      pos = analogRead(ePot); //pot for E string
      pastError = pastErrors[2];
      target = (note - lowest) * threshRange[2] / 12 + minVal[2];
      break;
    case A:
      pos = analogRead(aPot); //pot for A string
      pastError = pastErrors[3];
      target = (note - lowest) * threshRange[3] / 12 + minVal[3];
      break;
  }
  int actSpeed = 255;
  Serial.println(target);

  int error = pos - target;
  int Kp = 0.1;

  if (abs(error) > 20) {
    if (pos > target) {
      int actSpeed = Kp*error + Kp*(pastError - error);
      rev(actSpeed, s);
    }
    else {
      int actSpeed = Kp*error + Kp*pastError;
      fwd(actSpeed, s);
    }
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
  } else {
    brake(s);
    
  }
  return 0;
}

void calibrate () {
  const int delayTime = 1000;
  
  rev(255, G);
  delay(delayTime);
  minVal[0] = analogRead(gPot);
  fwd(255, G);
  delay(delayTime);
  maxVal[0] = analogRead(gPot);
  brake(G);

  rev(255, C);
  delay(delayTime);
  minVal[1] = analogRead(cPot);
  fwd(255, C);
  delay(delayTime);
  maxVal[1] = analogRead(cPot);
  brake(C);

  rev(255, E);
  delay(delayTime);
  minVal[2] = analogRead(ePot);
  fwd(255, E);
  delay(delayTime);
  maxVal[2] = analogRead(ePot);
  brake(E);

  rev(255, A);
  delay(delayTime);
  minVal[3] = analogRead(aPot);
  fwd(255, A);
  delay(delayTime);
  maxVal[3] = analogRead(aPot);
  brake(A);

  for (int i = 0; i < 4; i++) {
    threshRange[i] = maxVal[i] - minVal[i];
    Serial.println(threshRange[i]);
  }
  Serial.println("Calibration done!");
}

void calibrateTog () {
  const int delayTime = 2000;
  
//  rev(255, G);
//  rev(255, A);
  rev(255, C);
//  rev(255, E);

  delay(delayTime);

  minVal[0] = analogRead(gPot);
  minVal[1] = analogRead(cPot);
  minVal[2] = analogRead(ePot);
  minVal[3] = analogRead(aPot);

//  fwd(255, G);
//  fwd(255, A);
  fwd(255, C);
//  fwd(255, E);

  delay(delayTime);

  maxVal[0] = analogRead(gPot);
  maxVal[1] = analogRead(cPot);
  maxVal[2] = analogRead(ePot);
  maxVal[3] = analogRead(aPot);

  brake(G);
  brake(C);
  brake(E);
  brake(A);

  for (int i = 0; i < 4; i++) {
    threshRange[i] = maxVal[i] - minVal[i];
    Serial.println(threshRange[i]);
  }
  Serial.println("Calibration done!");
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
