#define AIN1 50//38 //D2

#define AIN2 52//40//D4

#define PWMA 8//3 // 


const int feedback = A8; //potentiometer from actuator
int position_LA = 0; //potentiometer from actuator
int err;

int target = 500;
double dt = 10/1000.0; //seconds
double tol = 100;

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

position_LA = analogRead(feedback);  // read the input on analog pin 0:
err = target - position_LA;

int mintol = 15; //Min size of dead zone (smaller means more precision but risks oscillation around target)
int maxtol = 100; //Max size of dead zone (smaller lets us move at full speed for longer but risks oscillation around target)
double tolrat = 1.1; //How fast we change the adaptive threshold. Keep this bigger than 1. Bigger means faster convergence but risks oscillation

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

delay(dt*1000); //milliseconds

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
