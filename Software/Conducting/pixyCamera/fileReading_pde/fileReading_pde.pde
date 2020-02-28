import processing.serial.*;
import java.util.*;
import java.text.SimpleDateFormat;  

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
   SimpleDateFormat formatter = new SimpleDateFormat("dd/MM/yyyy HH:mm:ss");  
   Date date = new Date();  
   String datevar = formatter.format(date);
   String filename = "position"+datevar+".txt";
   filename = filename.replace('/', '_');
   filename = filename.replace(' ', '_');
   filename = filename.replace(':', '_');
   filename = "positionData/" + filename;
   shouldRead = false;
   printArray(Serial.list());
   String[] devs = Serial.list();
   int dev_numb = getDevNumb(devs);
   mySerial = new Serial( this, devs[7], 9600 );
   output = createWriter( filename );
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
