void drumRudiments(byte leftHit, byte rightHit, byte cycles) {
  int m;
  for (k=0;k<cycles;k++) {
    for (m=0;m<leftHit;m++) {
      leftServo.write(LEFT_DOWN); delay(DELAY_DOWN);
      leftServo.write(LEFT_ROLL_UP_LOW); delay(55);
    }
    for (m=0;m<rightHit;m++) {
      rightServo.write(RIGHT_DOWN); delay(DELAY_DOWN);
      rightServo.write(RIGHT_ROLL_UP_LOW); delay(55);
    }
  }
}

//Single paradiddle RLRR LRLL
void singleParadiddle(int duration, int DELAY_PARADIDDLE) {
  int m;
  int cycles = (duration/DELAY_PARADIDDLE) >> 4;
  
  for (m=0;m<cycles;m++) {
    rightServo.write(RIGHT_DOWN); delay(DELAY_DOWN);
    rightServo.write(RIGHT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);      
      leftServo.write(LEFT_DOWN); delay(DELAY_DOWN);
      leftServo.write(LEFT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);    
    rightServo.write(RIGHT_DOWN); delay(DELAY_DOWN);
    rightServo.write(RIGHT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);  
    rightServo.write(RIGHT_DOWN); delay(DELAY_DOWN);
    rightServo.write(RIGHT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);  
    
      leftServo.write(LEFT_DOWN); delay(DELAY_DOWN);
      leftServo.write(LEFT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);    
    rightServo.write(RIGHT_DOWN); delay(DELAY_DOWN);
    rightServo.write(RIGHT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);     
      leftServo.write(LEFT_DOWN); delay(DELAY_DOWN);
      leftServo.write(LEFT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);
      leftServo.write(LEFT_DOWN); delay(DELAY_DOWN);
      leftServo.write(LEFT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);
  }
}

//Double Paradiddle RLRLRR LRLRLL
void doubleParadiddle(int duration, int DELAY_PARADIDDLE) {
  int m;
  int cycles = duration/(3*(DELAY_PARADIDDLE<<3));
  
  for (m=0;m<cycles;m++) {
    rightServo.write(RIGHT_DOWN); delay(DELAY_DOWN);
    rightServo.write(RIGHT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);
      leftServo.write(LEFT_DOWN); delay(DELAY_DOWN);
      leftServo.write(LEFT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);  
    rightServo.write(RIGHT_DOWN); delay(DELAY_DOWN);
    rightServo.write(RIGHT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);
      leftServo.write(LEFT_DOWN); delay(DELAY_DOWN);
      leftServo.write(LEFT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);    
    rightServo.write(RIGHT_DOWN); delay(DELAY_DOWN);
    rightServo.write(RIGHT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);  
    rightServo.write(RIGHT_DOWN); delay(DELAY_DOWN);
    rightServo.write(RIGHT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);  
    
      leftServo.write(LEFT_DOWN); delay(DELAY_DOWN);
      leftServo.write(LEFT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);    
    rightServo.write(RIGHT_DOWN); delay(DELAY_DOWN);
    rightServo.write(RIGHT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);     
      leftServo.write(LEFT_DOWN); delay(DELAY_DOWN);
      leftServo.write(LEFT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);    
    rightServo.write(RIGHT_DOWN); delay(DELAY_DOWN);
    rightServo.write(RIGHT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);
      leftServo.write(LEFT_DOWN); delay(DELAY_DOWN);
      leftServo.write(LEFT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);
      leftServo.write(LEFT_DOWN); delay(DELAY_DOWN);
      leftServo.write(LEFT_ROLL_UP_LOW); delay(DELAY_PARADIDDLE);
  }
}

void singleStrokeRoll(int durationMS) {

  int total = (durationMS/(DELAY_ROLL_MEDIUM)) >> 1;
  for (int i=0; i<total; i++) {
    leftServo.write(LEFT_DOWN); delay(DELAY_ROLL_MEDIUM);
    rightServo.write(RIGHT_DOWN); leftServo.write(LEFT_ROLL_UP_LOW);
    delay(DELAY_ROLL_MEDIUM); rightServo.write(RIGHT_ROLL_UP_LOW);
  }
}

void drumRoll2(int delayMS) {
  for (k=0;k<40;k++) {
    hitAll(); delay(delayMS);
  }
}

//THIS IS A TEMPORARY FUNCTION
void buzzRoll(int duration) {
  int cycles=(duration>>5)/10;
  for (k=0;k<cycles;k++) {
    drumHit(LEFT, false); hitAll();
    drumHit(RIGHT, false); hitAll();
  }
}

//THIS IS TEMPORARY BUT IMPORTANT
void drumStir(byte cycles) {
  //for single stick: down, 300, up, 40
  for (k=0;k<cycles;k++) {  
    leftServo.write(LEFT_DOWN); delay(130);
    rightServo.write(RIGHT_ROLL_UP_LOW); delay(40);
    rightServo.write(RIGHT_DOWN); delay(130);
    leftServo.write(LEFT_ROLL_UP_LOW); delay(40);
  }
}

//120bpm
//Q note == 500ms
//E note == 250ms
//H note == 1000ms
//T note == 166ms
//triplet{RLR} eighth{L} triplet{LRL} eighth{R}
void singleStrokeFour(int duration) {
  int DELAY_E = 166-DELAY_DOWN_SHORT;
  int DELAY_T = 111-DELAY_DOWN_SHORT;

  for(k=0;k<20;k++) {
    rightServo.write(RIGHT_DOWN); delay(DELAY_DOWN_SHORT);
    rightServo.write(RIGHT_ROLL_UP_LOW); delay(DELAY_T);
      leftServo.write(LEFT_DOWN); delay(DELAY_DOWN_SHORT);
      leftServo.write(LEFT_ROLL_UP_LOW); delay(DELAY_T);   
    rightServo.write(RIGHT_DOWN); delay(DELAY_DOWN_SHORT);
    rightServo.write(RIGHT_ROLL_UP_LOW); delay(DELAY_T);
      leftServo.write(LEFT_DOWN); delay(DELAY_DOWN_SHORT);
      leftServo.write(LEFT_ROLL_UP_LOW); delay(DELAY_E);
      
      leftServo.write(LEFT_DOWN); delay(DELAY_DOWN_SHORT);
      leftServo.write(LEFT_ROLL_UP_LOW); delay(DELAY_T);   
    rightServo.write(RIGHT_DOWN); delay(DELAY_DOWN_SHORT);
    rightServo.write(RIGHT_ROLL_UP_LOW); delay(DELAY_T);
      leftServo.write(LEFT_DOWN); delay(DELAY_DOWN_SHORT);
      leftServo.write(LEFT_ROLL_UP_LOW); delay(DELAY_T);
    rightServo.write(RIGHT_DOWN); delay(DELAY_DOWN_SHORT);
    rightServo.write(RIGHT_ROLL_UP_LOW); delay(DELAY_E);
  }
}
