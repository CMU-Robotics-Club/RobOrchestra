import processing.serial.*;
import java.util.*;
import java.text.SimpleDateFormat;
import themidibus.*; //Library documentation: http://www.smallbutdigital.com/themidibus.php

MidiBus[] myBus;
int[] toSend = {}; //Which MIDI output to send to - overwrites to everything in setup

int channel = 0; //channel xylobot is on
int noteLen = 5;

int pitch = 60;
int maxpitch = 72;
Note mynote = null;

Serial mySerial;
PrintWriter output;
int lf = 10;    // Linefeed in ASCII
boolean shouldRead;
/*int getDevNumb(String[] devs) {
   for (int i = 0; i < devs.length; i++) {
     if (devs[i].equals("/dev/tty.usbmodem14201")) //Whatever's in Arduino's Tools->Port
       return i;
   }
   return -1;
}*/

void setup() {
   shouldRead = true;
   print("Arduino stuff");
   printArray(Serial.list());
   String[] devs = Serial.list();
   //int dev_numb = getDevNumb(devs);
   mySerial = new Serial( this, devs[6], 115200); //9600 for chromatic, 115200 for theremin
   //If port is busy, close Arduino serial monitor
  
  System.out.println("");   
  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  System.out.println("");

  //Overwrite toSend to send to everything by default - block comment if you want to avoid sending everywhere
  toSend = new int[MidiBus.availableOutputs().length];
  for (int i = 0; i < MidiBus.availableOutputs().length; i++){
    toSend[i] = i;
  }
  
  //Use toSend - this looks silly, but splitting this out is more convenient if we don't want to blast MIDI everywhere
  myBus = new MidiBus[toSend.length];
  for (int i = 0; i < myBus.length; i++){
    myBus[i] = new MidiBus(this, 0, i);
  }
}

void draw() {
    if (mySerial.available() > 0 ) {
         String value = mySerial.readStringUntil(lf);
         if (shouldRead == true && value != null && value.length() > 2) {
              //No need to parse input
              //value = value.substring(0, value.length()-2); //Not sure why -2...
              //println(value);
              
              
              //Stop previous note
              if(mynote != null){
                for (int i = 0; i < myBus.length; i++){
                  myBus[i].sendNoteOff(mynote); 
                }
              }
            
              //int x = parseInt(value);
              mynote = new Note(channel, pitch, 100);
    
              //sends note to Xylobot 
              for (int i = 0; i < myBus.length; i++){
                myBus[i].sendNoteOn(mynote); 
              }
              pitch++;
              if (pitch > maxpitch){pitch = 60;}
              
              System.out.println("test");
                
         }
    }
}
