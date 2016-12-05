/** 
 * @file: ukulele.c
 * @brief: Ukulele hardware code
 *
 * This library controls all the code for the hardware for xylobot
 * That means it controls all the pin handling, pulling it high and low and setting them as outputs
 *
 * @author: Jason Kim (ghunwook)
 *          Rohan Yadav (rohany)
 *
 */

#include <Arduino.h>
#include "ukulele.h"
#include "def.h"

void ukulele_init(){
  pinMode(A_1, OUTPUT);
  pinMode(A_2, OUTPUT);
  pinMode(A_3, OUTPUT);
  pinMode(A_4, OUTPUT);
  pinMode(B_1, OUTPUT);
  pinMode(B_2, OUTPUT);
  pinMode(B_3, OUTPUT);
  pinMode(B_4, OUTPUT);
  pinMode(C_1, OUTPUT);
  pinMode(C_2, OUTPUT);
  pinMode(C_3, OUTPUT);
  pinMode(C_4, OUTPUT);
  pinMode(D_1, OUTPUT);
  pinMode(D_2, OUTPUT);
  pinMode(D_3, OUTPUT);
  pinMode(D_4, OUTPUT);

  digitalWrite(A_1, LOW);
  digitalWrite(A_2, LOW);
  digitalWrite(A_3, LOW);
  digitalWrite(A_4, LOW);
  digitalWrite(B_1, LOW);
  digitalWrite(B_2, LOW);
  digitalWrite(B_3, LOW);
  digitalWrite(B_4, LOW);
  digitalWrite(C_1, LOW);
  digitalWrite(C_2, LOW);
  digitalWrite(C_3, LOW);
  digitalWrite(C_4, LOW);
  digitalWrite(D_1, LOW);
  digitalWrite(D_2, LOW);
  digitalWrite(D_3, LOW);
  digitalWrite(D_4, LOW);
}



