void lookAroundCircle() {
  headMove(HEAD_TILT_UP,HEAD_PAN_RIGHT); eyeLook(EYE_RIGHT); delay(1000);
  headMove(HEAD_TILT_UP,HEAD_PAN_LEFT);  eyeLook(EYE_LEFT); delay(1000);
  mouthOpen(MOUTH_OPEN, 500); mouthOpen(MOUTH_OPEN_WIDE, 1000);
  headMove(HEAD_TILT_DOWN,HEAD_PAN_RIGHT);  eyeLook(EYE_RIGHT); delay(1000);
  headMove(HEAD_TILT_UP,HEAD_PAN_RIGHT); delay(1000);
  headMove(HEAD_TILT_DOWN,HEAD_PAN_LEFT);  eyeLook(EYE_LEFT); delay(1000);
  headTilt(HEAD_TILT_NORMAL);
  eyeLook(EYE_NORMAL); delay(1000);
  mouthChatter();
}

void lookAroundCorners() {
 look(UpLeft); delay(1000);
 look(UpRight); delay(1000);
 look(DownLeft); delay(1000);
 look(DownRight); delay(1000);
 look(Up); delay(1000);
 look(Down); delay(2000);
}

//welcome/intro sequence
void seqWelcome() {
  //while playing audio, bow and look around
  //introduce the group, wiggle eyebrows a little
}

//move the eyes to a random position (Left, Right, Forward)
//could put positions into an array and point to random index...
void eyeWander() {
  int pos;
  int position = random(1,4);
  switch (position) {
    case 1:
      pos = EYE_NORMAL; break;
    case 2:
      pos = EYE_LEFT; break;
    case 3:
      pos = EYE_RIGHT; break;
    default:
      pos = EYE_NORMAL;
    }
  eyeServo.write(pos);
}

void SerialControl() {
   if (Serial.available()) {
      command = Serial.read();
      Serial.flush();
      
      switch (command) {
        case 'o':
          mouthOpen(MOUTH_OPEN,200);
          break;
        case 'w':
          look(Up);
          break;
        case 'a':
          look(UpLeft);
          break;
        case 'd':
          look(UpRight);
          break;
        case 's':
          mouthChatter();
          break;
        default: look(Forward);
      }
  } 
}

void lookAroundRandom() {
  headNod(2); delay(100);
  mouthOpen(MOUTH_OPEN_WIDE,1000);
  eyeWander();
  headTurn(HEAD_PAN_RIGHT); delay(500);
  eyeWander(); delay(500); eyeWander();
  mouthOpen(MOUTH_OPEN,2000);
  eyeWander(); delay(500); eyeWander();
  headTurn(HEAD_PAN_LEFT); delay(500);
  headTurn(HEAD_PAN_NORMAL); delay(500);
}
