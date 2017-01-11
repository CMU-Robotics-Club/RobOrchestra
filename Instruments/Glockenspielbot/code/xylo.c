/** 
 * @file: xylo.c
 * @brief: Xylobot hardware code
 *
 * This library controls all the code for the hardware for xylobot
 * That means it controls all the pin handling, pulling it high and low and setting them as outputs
 *
 * @author: Jason Kim (ghunwook)
 *
 */

#include <Arduino.h>
#include "xylo.h"
#include "def.h"

void xylo_init(){
  pinMode(N_A, OUTPUT);
  pinMode(N_A_S, OUTPUT);
  pinMode(N_B, OUTPUT);
  pinMode(N_C, OUTPUT);
  pinMode(N_C_S, OUTPUT);
  pinMode(N_D, OUTPUT);
  pinMode(N_D_S, OUTPUT);
  pinMode(N_E, OUTPUT);
  pinMode(N_F, OUTPUT);
  pinMode(N_F_S, OUTPUT);
  pinMode(N_G, OUTPUT);
  pinMode(N_G_S, OUTPUT);
  pinMode(N_HIGH_A, OUTPUT);
  pinMode(N_HIGH_A_S, OUTPUT);
  pinMode(N_HIGH_B, OUTPUT);
  pinMode(N_HIGH_C, OUTPUT);
  pinMode(N_HIGH_C_S, OUTPUT);
  pinMode(N_HIGH_D, OUTPUT);
  pinMode(N_HIGH_D_S, OUTPUT);
  pinMode(N_HIGH_E, OUTPUT);
  pinMode(N_HIGH_F, OUTPUT);
  pinMode(N_HIGH_F_S, OUTPUT);
  pinMode(N_HIGH_G, OUTPUT);
  pinMode(N_HIGH_G_S, OUTPUT);
  pinMode(N_HIGHER_A, OUTPUT);

  digitalWrite(N_A, LOW);
  digitalWrite(N_A_S, LOW);
  digitalWrite(N_B, LOW);
  digitalWrite(N_C, LOW);
  digitalWrite(N_C_S, LOW);
  digitalWrite(N_D, LOW);
  digitalWrite(N_D_S, LOW);
  digitalWrite(N_E, LOW);
  digitalWrite(N_F, LOW);
  digitalWrite(N_F_S, LOW);
  digitalWrite(N_G, LOW);
  digitalWrite(N_G_S, LOW);
  digitalWrite(N_HIGH_A, LOW);
  digitalWrite(N_HIGH_A_S, LOW);
  digitalWrite(N_HIGH_B, LOW);
  digitalWrite(N_HIGH_C, LOW);
  digitalWrite(N_HIGH_C_S, LOW);
  digitalWrite(N_HIGH_D, LOW);
  digitalWrite(N_HIGH_D_S, LOW);
  digitalWrite(N_HIGH_E, LOW);
  digitalWrite(N_HIGH_F, LOW);
  digitalWrite(N_HIGH_F_S, LOW);
  digitalWrite(N_HIGH_G, LOW);
  digitalWrite(N_HIGH_G_S, LOW);
  digitalWrite(N_HIGHER_A, LOW);

}



