import processing.serial.*;
import java.util.*;
import java.text.SimpleDateFormat;
import themidibus.*; //Library documentation: http://www.smallbutdigital.com/themidibus.php

MidiBus myBus; //Creates a MidiBus object
int channel = 0; //channel xylobot is on
int noteLen = 5;

int pitch = 60;
int maxpitch = 72;
Note mynote = null;

Serial mySerial;
PrintWriter output;
int lf = 10;    // Linefeed in ASCII
boolean shouldRead;
ArrayList<Long> intervals;
long threshold = 5; // in seconds
long lastNotePlayed; // milliseconds
float bpm;
float millisPerBeat;
long startTime = System.currentTimeMillis();
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
   mySerial = new Serial( this, devs[1], 115200); //9600 for chromatic, 115200 for theremin
   //If port is busy, close Arduino serial monitor
  
  System.out.println("");   
  MidiBus.list(); // List all available Midi devices on STDOUT. Hopefully robots show up here!
  System.out.println("");

  myBus = new MidiBus(this, 0, 2); //Creates bus to send MIDI data to xylobot
  intervals = new ArrayList<Long>();
  bpm = 0; //  intervals.size() * 60.0 / threshold;
  millisPerBeat = 0;  //intervals.size() * 60.0 / threshold;
  
}

void draw() {
    float divisor = threshold;
    if (System.currentTimeMillis() < threshold * 1000 + startTime)
    {
      divisor = (System.currentTimeMillis() - startTime)/1000;
    }
    if (intervals.size() >= 2)
    {
      //println("interval size >= 2");
      bpm = intervals.size() * 60.0 / divisor;
      millisPerBeat = 1 / bpm * 60000;
      //println(millisPerBeat);
    
      if (intervals.size() > 0 && intervals.get(0) < System.currentTimeMillis() - (threshold * 1000))
      {
        intervals.remove(0);
        //println("Removing old interval");
      }
      
      if (lastNotePlayed < System.currentTimeMillis() - (long)millisPerBeat)
      {
        if(mynote != null){
                  myBus.sendNoteOff(mynote);
                }
              
            //int x = parseInt(value);
            mynote = new Note(channel, pitch, 100);
  
            //sends note to Xylobot 
            myBus.sendNoteOn(mynote);
            //println("Playing note");
            pitch++;
            if (pitch > maxpitch){pitch = 60;}
                
           lastNotePlayed = System.currentTimeMillis();
      }
    }        
    
    if (mySerial.available() > 0 ) {
         String value = mySerial.readStringUntil(lf);
         //println("read");
         if (shouldRead == true && value != null && value.length() > 2) {
              //No need to parse input
              //value = value.substring(0, value.length()-2); //Not sure why -2...
              //println(value);
              intervals.add(System.currentTimeMillis());
              
              //Stop previous note
              //print(lastNotePlayed);
              println("beat");
              
         }
    }
    
}
