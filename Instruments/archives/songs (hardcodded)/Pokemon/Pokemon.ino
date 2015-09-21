#define NOTE_C 22
#define NOTE_C_SHARP 38
#define NOTE_D 23
#define NOTE_D_SHARP 33
#define NOTE_E 24
#define NOTE_F 25
#define NOTE_F_SHARP 34
#define NOTE_G 26
#define NOTE_G_SHARP 35
#define NOTE_A 27
#define NOTE_A_SHARP 36
#define NOTE_C_HIGH 29
#define NOTE_C_SHARP_HIGH 37
#define NOTE_D_HIGH 30
#define NOTE_D_SHARP_HIGH 39

int rest = 156;

void setup() {
  // put your setup code here, to run once:
  pinMode(NOTE_C, OUTPUT);
  pinMode(NOTE_C_SHARP, OUTPUT);
  pinMode(NOTE_D, OUTPUT);
  pinMode(NOTE_D_SHARP, OUTPUT);
  pinMode(NOTE_E, OUTPUT);
  pinMode(NOTE_F, OUTPUT);
  pinMode(NOTE_F_SHARP, OUTPUT);
  pinMode(NOTE_G, OUTPUT);
  pinMode(NOTE_G_SHARP, OUTPUT);
  pinMode(NOTE_A, OUTPUT);
  pinMode(NOTE_A_SHARP, OUTPUT);
  pinMode(NOTE_C_HIGH, OUTPUT);
  pinMode(NOTE_C_SHARP_HIGH, OUTPUT);
  pinMode(NOTE_D_HIGH, OUTPUT);
  pinMode(NOTE_D_SHARP_HIGH, OUTPUT);
  
  
  digitalWrite(NOTE_C, LOW);
  digitalWrite(NOTE_C_SHARP, LOW);
  digitalWrite(NOTE_D, LOW);
  digitalWrite(NOTE_D_SHARP, LOW);
  digitalWrite(NOTE_E, LOW);
  digitalWrite(NOTE_F, LOW);
  digitalWrite(NOTE_F_SHARP, LOW);
  digitalWrite(NOTE_G, LOW);
  digitalWrite(NOTE_G_SHARP, LOW);
  digitalWrite(NOTE_A, LOW);
  digitalWrite(NOTE_A_SHARP, LOW);
  digitalWrite(NOTE_C_HIGH, LOW);
  digitalWrite(NOTE_C_SHARP_HIGH, LOW);
  digitalWrite(NOTE_D_HIGH, LOW);
  digitalWrite(NOTE_D_SHARP_HIGH, LOW);
  

}
void pulseNote(int note)
{
  digitalWrite(note, HIGH);
  delay(50);
  digitalWrite(note, LOW);
}
void loop() {
  // put your main code here, to run repeatedly: 
  
  //twinkle twinkle little star
  
  /*---*/
  
  pulseNote(NOTE_D_HIGH);
  delay(rest);
  pulseNote(NOTE_D_HIGH);
  delay(rest);
  pulseNote(NOTE_D_HIGH);
  delay(rest*3);
  
  
  pulseNote(NOTE_D_HIGH);
  delay(rest);
  pulseNote(NOTE_C_HIGH);
  delay(rest*2);
  pulseNote(NOTE_A);
  delay(rest);
  pulseNote(NOTE_F);
  delay(rest*4);
  
  pulseNote(NOTE_D_HIGH);
  delay(rest);
  pulseNote(NOTE_D_HIGH);
  delay(rest);
  pulseNote(NOTE_C_HIGH);
  delay(rest*2);
  pulseNote(NOTE_A_SHARP);
  delay(rest);  
  pulseNote(NOTE_C_HIGH);
  delay(rest*3);
//
  pulseNote(NOTE_A_SHARP);
  delay(rest);
  pulseNote(NOTE_A);
  delay(rest);
  pulseNote(NOTE_F);
  delay(rest);
  pulseNote(NOTE_C);
  delay(rest);
  delay(rest*8);
/*****************************/
  pulseNote(NOTE_D_SHARP_HIGH);
  delay(rest);
  pulseNote(NOTE_D_SHARP_HIGH);
  delay(rest);
  pulseNote(NOTE_D_SHARP_HIGH);
  delay(rest);
  pulseNote(NOTE_D_SHARP_HIGH);
  delay(rest*3); 
  pulseNote(NOTE_D_SHARP_HIGH);
  delay(rest);
  pulseNote(NOTE_D_HIGH);
  delay(rest*2);
  pulseNote(NOTE_C_HIGH);
  delay(rest); 
  pulseNote(NOTE_A_SHARP);
  delay(rest*4);
  pulseNote(NOTE_A_SHARP);
  delay(rest);
  pulseNote(NOTE_D_HIGH);
  delay(rest*2);
  pulseNote(NOTE_D_HIGH);
  delay(rest);
  pulseNote(NOTE_C_HIGH);
  delay(rest*2);
  pulseNote(NOTE_A_SHARP);
  delay(rest*2);
  pulseNote(NOTE_D_HIGH);
  delay(rest*3);
/****************************************************/
  pulseNote(NOTE_D);
  delay(rest);
  pulseNote(NOTE_F);
  delay(rest);
  pulseNote(NOTE_G);
  delay(rest*3);
  pulseNote(NOTE_D);
  delay(rest);
  pulseNote(NOTE_D);
  delay(rest);
  pulseNote(NOTE_F);
  delay(rest);
  pulseNote(NOTE_G);
  delay(rest*2);
  pulseNote(NOTE_G);
  delay(rest*2);
  pulseNote(NOTE_F);
  delay(rest);
  pulseNote(NOTE_F);
  delay(rest);
  delay(rest*7);
  /////////
  pulseNote(NOTE_G);
  delay(rest);
  pulseNote(NOTE_G);
  delay(rest);
  pulseNote(NOTE_A);
  delay(rest);
  pulseNote(NOTE_A_SHARP);
  delay(rest);
  pulseNote(NOTE_A);
  delay(rest*2);
  pulseNote(NOTE_G);
  delay(rest*2);
  pulseNote(NOTE_F);
  delay(rest*2);
  pulseNote(NOTE_D);
  delay(rest);
  pulseNote(NOTE_F);
  delay(rest);
  pulseNote(NOTE_G);
  delay(rest*3);
  delay(rest*3);
  ///////////
  pulseNote(NOTE_G);
  delay(rest);
  pulseNote(NOTE_G);
  delay(rest*2);
  pulseNote(NOTE_F);
  delay(rest);
  pulseNote(NOTE_C);
  delay(rest);
  delay(rest*2);
  
  pulseNote(NOTE_D);
  delay(rest);
  pulseNote(NOTE_D_SHARP);
  delay(rest*2);
  pulseNote(NOTE_A_SHARP);
  delay(rest*2);
  pulseNote(NOTE_A_SHARP);
  delay(rest*2);
  pulseNote(NOTE_D_SHARP);
  delay(rest*2);
  pulseNote(NOTE_F);
  delay(rest*2);
  pulseNote(NOTE_A_SHARP);
  delay(rest);
  pulseNote(NOTE_A_SHARP);
  delay(rest*2);
  ////////
  delay(rest);
  pulseNote(NOTE_A_SHARP);
  delay(rest*3);
  pulseNote(NOTE_A_SHARP);
  delay(rest*3);
  pulseNote(NOTE_A_SHARP);
  delay(rest);
  pulseNote(NOTE_A);
  delay(rest*7);
  delay(rest);

///
  pulseNote(NOTE_D);
  delay(rest);
  pulseNote(NOTE_F);
  delay(rest);
  pulseNote(NOTE_G);
  delay(rest*3);
  pulseNote(NOTE_D);
  delay(rest);
  pulseNote(NOTE_D);
  delay(rest);
  pulseNote(NOTE_F);
  delay(rest);
  pulseNote(NOTE_G);
  delay(rest*2);
  pulseNote(NOTE_G);
  delay(rest*2);
}
