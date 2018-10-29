#include <Servo.h>
#include <ROservo.h>

ROservo s1 = ROservo(4,85,180);
ROservo s2 = ROservo(5,85,180);
ROservo s3 = ROservo(6,85,180);
ROservo s4 = ROservo(7,85,180);
ROservo s5 = ROservo(8,85,180);
ROservo s6 = ROservo(9,85,180);
ROservo s7 = ROservo(10,85,180);

void setup()
{
  s1.setTime(100,5000);
  s2.setTime(100,5000);
  s3.setTime(100,5000);
  s4.setTime(100,5000);
  s5.setTime(100,5000);
  s6.setTime(100,5000);
  s7.setTime(100,5000);
}

void loop()
{
  s1.loop();
  s2.loop();
  s3.loop();
  s4.loop();
  s5.loop();
  s6.loop();
  s7.loop();
}
