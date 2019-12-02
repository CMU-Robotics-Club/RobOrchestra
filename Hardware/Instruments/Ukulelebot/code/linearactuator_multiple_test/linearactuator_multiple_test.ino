
#define BIN1 30 //D30

#define BIN2 32//D32

#define PWMA 4 //PWM 4 
#define PWMB 5 //PWM 5 

#define AIN1 34 //D34

#define AIN2 36//D36

#define CIN1 38
#define CIN2 40

#define DIN1 42
#define DIN2 44

#define PWMC 3
#define PWMD 2



int IN1[] = {AIN1, BIN1, CIN1, DIN1};
int IN2[] = {AIN2, BIN2, CIN2, DIN2};
int PWM[] = {PWMA, PWMB, PWMC, PWMD};

const int feedbackB = A0; //potentiometer from actuator A0
const int feedbackA = A1; //potentiometer from actuator A1
const int feedbackC = A3;
const int feedbackD = A2;

const int feedback[]= {feedbackA, feedbackB, feedbackC, feedbackD};

int position_LA = 0; //potentiometer from actuator
int position_LB = 0;
int position_LC = 0;
int position_LD = 0;

int position_L[] = {position_LA, position_LB, position_LC, position_LD};

int prev[4];

int targets[] = {500, 500, 500, 500};

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

void loop()
{
for(int i = 3; i > -1;i--){
  prev[i] = position_L[i];
  position_L[i] = analogRead(feedback[i]);  // read the input on analog pin 0:
  Serial.println(position_L[i]);
  if (targets[i] - position_L[i] > 30){
        fwd(75,i);
  }
  else if (targets[i] - position_L[i] < -30){
        rev(75,i);
  }
  else brake(i);
/*
  if((position_L[i] >= prev[i]) && position_L[i] < 500)
   {
      fwd(50,i);
    }

  else if (( position_L[i] < prev[i]) && position_L[i] > 300)
  {
  rev(50,i);
  }
 
*/

}
delay(20);
 
  //Serial.print("  Positions = ");
 // Serial.println(position_L[]);


}//end void loop


void fwd(int speed, int motor)
{ digitalWrite(IN1[motor], HIGH);
  digitalWrite(IN2[motor], LOW);
  analogWrite(PWM[motor], speed);
}
void rev(int speed, int motor)
{ digitalWrite(IN1[motor], LOW);
  digitalWrite(IN2[motor], HIGH);
  analogWrite(PWM[motor], speed);
}
void brake(int motor) 
{ digitalWrite(IN1[motor], HIGH);
  digitalWrite(IN2[motor], HIGH);
  analogWrite(PWM[motor], 0);
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
