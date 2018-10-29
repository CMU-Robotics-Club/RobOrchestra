#define NOTE_C 22
#define NOTE_C_SHARP 42
#define NOTE_D 23
#define NOTE_D_SHARP 38                           
#define NOTE_E 24
#define NOTE_F 25
#define NOTE_F_SHARP 34
#define NOTE_G 26
#define NOTE_G_SHARP 35
#define NOTE_A 27
#define NOTE_A_SHARP 36
#define NOTE_B 28
#define NOTE_C_HIGH 29
#define NOTE_C_SHARP_HIGH 37
#define NOTE_D_HIGH 30
#define NOTE_D_SHARP_HIGH 39
#define NOTE_E_HIGH 31

int bpm = 200;

int beat = (60000) / bpm;
String pirates = String("dnxx04--dnxx08--d#xx08--dnxx08--d#xx08--dnxx04--dnxx08--d#xx08--dnxx08--d#xx08--dnxx04--dnxx08--d#xx08--dnxx08--d#xx08--dnxx04--dnxx08--d#xx08--fnxx08--d#xx08--dnxx04--dnxx08--d#xx08--dnxx08--d#xx08--"
                        "dnxx04--dnxx08--d#xx08--dnxx08--d#xx08--dnxx04--dnxx08--d#xx08--dnxx08--d#xx08--dnxx04--dnxx08--d#xx08--fnxx08--d#xx08--dnxx04--dnxx04--dnxx02--"
                        "dnxx08--enxx08--fnxx04--xxxx08--gnxx08--anxx04--gnxx04--fnxx04--enxx04--fnxx04--gnxx04--anxx04--"
                        "gnxx02--fnxx08--gnxx08--anxx04--xxxx08--gnxx08--fnxx04--enxx04--fnxx04--enxx04--dnxx04--xxxx08--enxx08--cnxx04--dnxx08--dnxx08--dnxx08--xxxx04--dnxx08--enxx08--"
                        "fnxx04--xxxx08--enxx08--fnxx04--gnxx04--fnxx04--gnxx04--anxx04--xxxx08--gnxx08--fnxx04--dnxx02--dnxx08--enxx08--fnxx04--gnxx04--anxx04--a#xx04--dnxx04--xxxx08--gnxx08--fnxx04--xxxx08--gnxx08--enxx04--"
                        "dnxx01--"
                        "dnxx04--dnxx08--dnxx04--dnxx08--dnxx04--dnxx08--dnxx08--dnxx08--dnxx08--dnxx04--dnxx08--dnxx04--dnxx08--dnxx04--dnxx08--dnxx08--dnxx08--dnxx08--xxxx04--dnxx08--dnxx08--dnxx08--enxx08--fnxx04--fnxx08--fnxx08--fnxx08--gnxx08--"
                        "enxx04--enxx04--dnxx08--cnxx08--cnxx08--dnxx04--xxxx08--xxxx04--dnxx04--dnxx04--dnxx08--enxx08--fnxx04--fnxx04--fnxx08--gnxx08--enxx04--enxx04--dnxx08--cnxx08--dnxx04--xxxx02--dnxx04--dnxx04--dnxx08--fnxx08--"
                        "gnxx04--gnxx04--gnxx08--anxx08--a#xx04--a#xx08--a#xx08--anxx08--gnxx08--anxx08--dnxx04--dnxx08--dnxx08--enxx08--fnxx04--fnxx04--gnxx04--anxx08--dnxx04--xxxx08--dnxx08--fnxx08--enxx04--enxx08--enxx08--fnxx08--dnxx08--enxx04--xxxx08--"
                        "anxx04--anxx04--anxx04--a#xx08--anxx04--anxx04--xxxx08--gnxx04--gnxx04--gnxx04--gnxx08--anxx02--xxxx08--anxx04--anxx04--anxx04--a#xx08--anxx04--anxx04--xxxx08--gnxx04--fnxx04--enxx04--dnxx02--dnxx08--enxx08--fnxx02--gnxx08--anxx08--gnxx04--fnxx04--enxx04--fnxx04--gnxx04--anxx04--"
                        "gnxx02--fnxx08--gnxx08--anxx02--gnxx08--fnxx08--enxx04--fnxx04--enxx04--dnxx02--enxx08--cnxx08--dnxx02--xxxx04--"
                        "anxx02--xxxx04--a#xx02--xxxx04--anxx04--anxx04--anxx04--anxx08--gnxx08--xxxx02--gnxx02--xxxx04--fnxx02--xxxx04--"
                        "fnxx04--gnxx04--enxx04--dnxx04--xxxx08--dnxx08--enxx08--fnxx08--anxx04--xxxx08--dnxx08--enxx08--fnxx08--a#xx04--xxxx08--dnxx08--enxx08--fnxx08--anxx04--anxx04--Cnxx04--anxx08--gnxx08--xxxx02--gnxx02--xxxx04--fnxx04--gnxx04--enxx04--Dndn02--xxxx04--");

void setup() {
  // put your setup code here, to run once:
  
  Serial.begin(9600);
  
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
  pinMode(NOTE_D_SHARP_HIGH, OUTPUT);
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
  digitalWrite(NOTE_D_SHARP_HIGH, LOW);
  digitalWrite(NOTE_E_HIGH, LOW);
}

void pulseNotes(int note1, int note2)
{
  if(note1 != 0) digitalWrite(note1, HIGH);
  if(note2 != 0) digitalWrite(note2, HIGH);
  if(!(note1 == 0 && note2 == 0)) delay(50);
  if(note1 != 0) digitalWrite(note1, LOW);
  if(note2 != 0) digitalWrite(note2, LOW);
}

void playSong(String song)
//requires a string with an even number of characters
{
  for(int i = 0; i < song.length()-1; i += 4)
  {
    String s1 = song.substring(i, i+2);
    String s2 = song.substring(i+2, i+4);
    int note1 = 0;
    int note2 = 0;
    
    if(s1 == "01") delay((beat*4) - 50);
    else if(s1 == "02") delay((beat*2) - 50);
    else if(s1 == "04") delay(beat - 50);
    else if(s1 == "08") delay((beat/2) - 50);
    else if(s1 == "16") delay((beat/4) - 50);
    else if(s1 == "32") delay((beat/8) - 50);
    else if(s1 == "cn") note1 = NOTE_C;
    else if(s1 == "c#") note1 = NOTE_C_SHARP;
    else if(s1 == "dn") note1 = NOTE_D;
    else if(s1 == "d#") note1 = NOTE_D_SHARP;
    else if(s1 == "en") note1 = NOTE_E;
    else if(s1 == "fn") note1 = NOTE_F;
    else if(s1 == "f#") note1 = NOTE_F_SHARP;
    else if(s1 == "gn") note1 = NOTE_G;
    else if(s1 == "g#") note1 = NOTE_G_SHARP;
    else if(s1 == "an") note1 = NOTE_A;
    else if(s1 == "a#") note1 = NOTE_A_SHARP;
    else if(s1 == "bn") note1 = NOTE_B;
    else if(s1 == "Cn") note1 = NOTE_C_HIGH;
    else if(s1 == "C#") note1 = NOTE_C_SHARP_HIGH;
    else if(s1 == "Dn") note1 = NOTE_D_HIGH;
    else if(s1 == "D#") note1 = NOTE_D_SHARP_HIGH;
    else if(s1 == "En") note1 = NOTE_E_HIGH;
    
    if(s2 == "cn") note2 = NOTE_C;
    else if(s2 == "c#") note2 = NOTE_C_SHARP;
    else if(s2 == "dn") note2 = NOTE_D;
    else if(s2 == "d#") note2 = NOTE_D_SHARP;
    else if(s2 == "en") note2 = NOTE_E;
    else if(s2 == "fn") note2 = NOTE_F;
    else if(s2 == "f#") note2 = NOTE_F_SHARP;
    else if(s2 == "gn") note2 = NOTE_G;
    else if(s2 == "g#") note2 = NOTE_G_SHARP;
    else if(s2 == "an") note2 = NOTE_A;
    else if(s2 == "a#") note2 = NOTE_A_SHARP;
    else if(s2 == "bn") note2 = NOTE_B;
    else if(s2 == "Cn") note2 = NOTE_C_HIGH;
    else if(s2 == "C#") note2 = NOTE_C_SHARP_HIGH;
    else if(s2 == "Dn") note2 = NOTE_D_HIGH;
    else if(s2 == "D#") note2 = NOTE_D_SHARP_HIGH;
    else if(s2 == "En") note2 = NOTE_E_HIGH;
    
    pulseNotes(note1, note2);
  }
}
  
void loop() {
  // put your main code here, to run repeatedly: 
  playSong(pirates);
}
