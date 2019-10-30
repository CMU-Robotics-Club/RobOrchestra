import processing.serial.*;
import java.util.*;
Serial mySerial;
PrintWriter output;
int lf = 10;    // Linefeed in ASCII
boolean shouldRead;
int getDevNumb(String[] devs) {
   for (int i = 0; i < devs.length; i++) {
     if (devs[i].equals("/dev/cu.usbmodem14111"))
       return i;
   }
   return -1;
}

void setup() {
   shouldRead = false;
   printArray(Serial.list());
   String[] devs = Serial.list();
   int dev_numb = getDevNumb(devs);
   mySerial = new Serial( this, devs[0], 9600 );
   output = createWriter( "position.txt" );
}
void draw() {
    if (mySerial.available() > 0 ) {
         String value = mySerial.readStringUntil(lf);
         if (shouldRead == true && value != null) {
              output.println( value );
         }
         if(value != null && value.startsWith("error:"))
              shouldRead = true;
    }
}

void keyPressed() {
    output.flush();  // Writes the remaining data to the file
    output.close();  // Finishes the file
    exit();  // Stops the program
}
