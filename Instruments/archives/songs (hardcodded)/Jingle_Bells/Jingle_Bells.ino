#define NOTE_C 22
#define NOTE_C_SHARP 33
#define NOTE_D 23
#define NOTE_D_SHARP 34
#define NOTE_E 24
#define NOTE_F 25
#define NOTE_F_SHARP 35
#define NOTE_G 26
#define NOTE_G_SHARP 36
#define NOTE_A 27
#define NOTE_A_SHARP 37
#define NOTE_B 28
#define NOTE_C_HIGH 29
#define NOTE_C_SHARP_HIGH 38
#define NOTE_D_HIGH 30
#define NOTE_D_SHAP_HIGH 39
#define NOTE_E_HIGH 31

int rest = 200;

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
  pinMode(NOTE_B, OUTPUT);
  pinMode(NOTE_C_HIGH, OUTPUT);
  pinMode(NOTE_C_SHARP_HIGH, OUTPUT);
  pinMode(NOTE_D_HIGH, OUTPUT);
  pinMode(NOTE_D_SHAP_HIGH, OUTPUT);
  pinMode(NOTE_E_HIGH, OUTPUT);
  
  
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
  digitalWrite(NOTE_B, LOW);
  digitalWrite(NOTE_C_HIGH, LOW);
  digitalWrite(NOTE_C_SHARP_HIGH, LOW);
  digitalWrite(NOTE_D_HIGH, LOW);
  digitalWrite(NOTE_D_SHAP_HIGH, LOW);
  digitalWrite(NOTE_E_HIGH, LOW);
  

}
void pulseNote(int note)
{
  digitalWrite(note, HIGH);
  delay(50);
  digitalWrite(note, LOW);
}
void loop() {
  // put your main code here, to run repeatedly: 
  
  //jingle bells
  
  /*---*/
  
  pulseNote(NOTE_E);
  delay(rest);
  pulseNote(NOTE_E);
  delay(rest);
  pulseNote(NOTE_E);
  delay(rest*2);
  
  pulseNote(NOTE_E);
  delay(rest);
  pulseNote(NOTE_E);
  delay(rest);
  pulseNote(NOTE_E);
  delay(rest*2);
  
  pulseNote(NOTE_E);
  delay(rest);
  pulseNote(NOTE_G);
  delay(rest);
  pulseNote(NOTE_C);
  delay(rest);
  pulseNote(NOTE_D);
  delay(rest);
  pulseNote(NOTE_E);
  delay(rest*2);
 
  /*---*/
 
 pulseNote(NOTE_F);
 delay(rest);
 pulseNote(NOTE_F);
 delay(rest);
 pulseNote(NOTE_F);
 delay(rest);
 pulseNote(NOTE_F);
 delay(rest);
 
 pulseNote(NOTE_F);
 delay(rest);
 pulseNote(NOTE_E);
 delay(rest);
 pulseNote(NOTE_E);
 delay(rest);
 pulseNote(NOTE_E);
 delay(rest);
 
 pulseNote(NOTE_D);
 delay(rest);
 pulseNote(NOTE_D);
 delay(rest);
 pulseNote(NOTE_E);
 delay(rest);
 pulseNote(NOTE_D);
 delay(rest*2);
 
 pulseNote(NOTE_G);
 delay(rest*2);
 
 /*---*/
 
  pulseNote(NOTE_E);
  delay(rest);
  pulseNote(NOTE_E);
  delay(rest);
  pulseNote(NOTE_E);
  delay(rest*2);
  
  pulseNote(NOTE_E);
  delay(rest);
  pulseNote(NOTE_E);
  delay(rest);
  pulseNote(NOTE_E);
  delay(rest*2);
  
  pulseNote(NOTE_E);
  delay(rest);
  pulseNote(NOTE_G);
  delay(rest);
  pulseNote(NOTE_C);
  delay(rest);
  pulseNote(NOTE_D);
  delay(rest);
  pulseNote(NOTE_E);
  delay(rest*2);
 
  /*---*/
 
 pulseNote(NOTE_F);
 delay(rest);
 pulseNote(NOTE_F);
 delay(rest);
 pulseNote(NOTE_F);
 delay(rest);
 pulseNote(NOTE_F);
 delay(rest);
 
 pulseNote(NOTE_F);
 delay(rest);
 pulseNote(NOTE_E);
 delay(rest);
 pulseNote(NOTE_E);
 delay(rest);
 pulseNote(NOTE_E);
 delay(rest);
 
 pulseNote(NOTE_G);
 delay(rest);
 pulseNote(NOTE_G);
 delay(rest);
 pulseNote(NOTE_F);
 delay(rest);
 pulseNote(NOTE_D);
 delay(rest);
 pulseNote(NOTE_C);
 delay(rest*2);
 
 pulseNote(NOTE_C_HIGH);
 delay(rest*5);
 
 /*---*/
 
 
}
