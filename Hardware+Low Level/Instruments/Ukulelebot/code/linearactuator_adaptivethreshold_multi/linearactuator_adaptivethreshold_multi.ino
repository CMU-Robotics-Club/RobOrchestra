//PWM starts on 2
#define PWMA 2
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

int target[] = {500, 500, 500, 500};

int mintol = 15; //Min size of dead zone (smaller means more precision but risks oscillation around target)
int maxtol = 100; //Max size of dead zone (smaller lets us move at full speed for longer but risks oscillation around target)
double tolrat = 1.1; //How fast we change the adaptive threshold. Keep this bigger than 1. Bigger means faster convergence but risks oscillation

double dt = 10/1000.0; //seconds
double tol[] = {100, 100, 100, 100};

void setup()
{
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
}

void loop()
{
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

}//end void loop


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
