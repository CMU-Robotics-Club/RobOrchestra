/**
 *  @file: def.h
 *  @brief: Lists the definitions of keys to pins and index to keys
 *
 *  @author: Audrey Yeoh (ayeoh)
 *
 *
 */

#ifndef _DEF_H_
#define _DEF_H_

#ifdef __cplusplus
extern "C"{
#endif

    //Taken care of in the main file. Don't need this anymore.

    /* PLACE DEFINITIONS HERE */
    // Define notes to arduino pins here
    #define N_C 22
    #define N_C_S 13 // to be confirmed tentative use D# space
    #define N_D 23 // to be confirmed
    #define N_D_S 38 // supposed to be 38
    #define N_E 24
    #define N_F 25
    #define N_F_S 34
    #define N_G 26
    #define N_G_S 35
    #define N_A 27
    #define N_A_S 36
    #define N_B 28
    #define N_HIGH_C 29
    #define N_HIGH_C_S 37
    #define N_HIGH_D 30
    #define N_HIGH_D_S 39
    #define N_HIGH_E 31
    //{22, 13, 23, 38, 24, 25, 34, 26, 35, 27, 36, 28, 29, 37, 30, 39, 31}

    // Define key index to notes here
    #define NOTE_C 60
    #define NOTE_C_S 61
    #define NOTE_D 62
    #define NOTE_D_S 63
    #define NOTE_E 64
    #define NOTE_F 65
    #define NOTE_F_S 66
    #define NOTE_G 67
    #define NOTE_G_S 68
    #define NOTE_A 69
    #define NOTE_A_S 70
    #define NOTE_B 71
    #define NOTE_HIGH_C 72
    #define NOTE_HIGH_C_S 73
    #define NOTE_HIGH_D 74
    #define NOTE_HIGH_D_S 75
    #define NOTE_HIGH_E 76

#ifdef __cplusplus
}   // extern "C"

#endif // __cplusplus
#endif // _DEF_H_

