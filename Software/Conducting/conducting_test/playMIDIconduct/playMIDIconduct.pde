import processing.serial.*;
import java.util.*;
import java.text.SimpleDateFormat;
import themidibus.*; //Library documentation: http://www.smallbutdigital.com/themidibus.php

MidiBus myBus; //Creates a MidiBus object
int channel = 0; //channel xylobot is on
int noteLen = 5;

int pitch = 60;
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
   printArray(Serial.list());
   String[] devs = Serial.list();
   //int dev_numb = getDevNumb(devs);
   mySerial = new Serial( this, devs[3], 115200); //9600 for chromatic, 115200 for theremin
   //If port is busy, close Arduino serial monitor
  
  System.out.println("");   
  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  System.out.println("");

  myBus = new MidiBus(this, 0, 1); //Creates bus to send MIDI data to xylobot
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
                myBus.sendNoteOff(mynote);
              }
            
              //int x = parseInt(value);
              mynote = new Note(channel, pitch, 100);
    
              //sends note to Xylobot 
              myBus.sendNoteOn(mynote);
              pitch++;
              if (pitch > 72){pitch = 60;}
                
         }
    }
}
