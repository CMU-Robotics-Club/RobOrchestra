#define AIN1 2

#define AIN2 4

#define PWMA 5


const int feedback = A0; //potentiometer from actuator
int position_LA = 0; //potentiometer from actuator
int prev;



void setup()
{
  pinMode(feedback, INPUT);//feedback from actuator
  pinMode(PWMA, OUTPUT);
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);

  Serial.begin(9600);
 
}

void loop()
{

prev = position_LA;
position_LA = analogRead(A0);  // read the input on analog pin 0:
Serial.println(position_LA);


if((position_LA >= prev) && position_LA < 750)
  {
    fwd(50);
  }

else if (( position_LA < prev) && position_LA > 250)
{
  rev(50);
}
delay(20);
 
  Serial.print("  Position LA  = ");
  Serial.println(position_LA);


}//end void loop


void fwd(int speed)
{ digitalWrite(AIN1, HIGH);
  digitalWrite(AIN2, LOW);
  analogWrite(PWMA, speed);
}
void rev(int speed)
{ digitalWrite(AIN1, LOW);
  digitalWrite(AIN2, HIGH);
  analogWrite(PWMA, speed);
}
void brake()
{ digitalWrite(AIN1, HIGH);
  digitalWrite(AIN2, HIGH);
  analogWrite(PWMA, 0);
}


/*int input = A0;
int enA = A2;
int in1 = 3;
int in2 = 4;
//int rotDirection = 0;
//int pressed = false;
void setup() {
  pinMode(enA, OUTPUT);
  pinMode(in1, OUTPUT);
  pinMode(in2, OUTPUT);
  pinMode(input, INPUT);
 
  // Set initial rotation direction
  digitalWrite(in1, LOW);
  digitalWrite(in2, HIGH);
  //analogWrite(enA, 100);
  delay(100);
  Serial.begin(9600);
 
}
void loop() {
  analogWrite(enA, 100);
  int positionMotor = analogRead(input);
  Serial.println(positionMotor);
  delay(100);
}
*/
