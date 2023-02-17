#define AIN1 50//38 //D2

#define AIN2 52//40//D4

#define PWMA 8//3 // 


const int feedback = A8; //potentiometer from actuator
int position_LA = 0; //potentiometer from actuator
int err;
int errprev;
int errdiff;
int errint;

int target = 500;
double kp = 0.1;//0.1;
double kd = 0;//0.1;
double ki = 0.0;

double dt = 10/1000.0; //seconds
double tol = 100;

void setup()
{
  pinMode(feedback, INPUT);//feedback from actuator
  pinMode(PWMA, OUTPUT);
  pinMode(AIN1, OUTPUT);
  pinMode(AIN2, OUTPUT);

  Serial.begin(9600);

  position_LA = analogRead(feedback);  // read the input on analog pin 0:
  err = target - position_LA;
  errprev = err;
}

void loop()
{

position_LA = analogRead(feedback);  // read the input on analog pin 0:
//Serial.println(position_LA);
err = target - position_LA;
errdiff = err-errprev;
errint += err*dt;
double power = kp*err + kd*(errdiff)/dt + ki*errint;

double cap = 0.01;
if (abs(power) > cap){
  power = power/abs(power)*cap;
}

fwd(0);
power = 0;

int mintol = 15;
int maxtol = 100;
double tolrat = 1.1; //tolrat > 1. How fast we change the adaptive threshold
//Big tolrat tries to converge faster but might oscillate near mintol

if (abs(err) < tol){
  brake();
  if (tol > mintol){
      tol /= tolrat;
  }
}
else{
  if(err < -tol){
    rev(abs(power));
    if (tol < maxtol){
      tol *= tolrat;
    }
  }
  if(err > tol){
    fwd(abs(power));
    if (tol < maxtol){
      tol *= tolrat;
    }
  }
}

Serial.print(err);
Serial.print(" ");
  Serial.println(tol);

/*
if((position_LA >= prev) && position_LA < 250)
  {
    fwd(10);
  }

else if (( position_LA < prev) && position_LA > 750)
{
  rev(10);
}*/
delay(dt*1000); //milliseconds
 
  /*Serial.print("  Position LA  = ");
  Serial.println(position_LA);*/

  /*Serial.println(errdiff);
  Serial.println(errint);*/

  errprev = err;

  //Serial.println(power);


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
