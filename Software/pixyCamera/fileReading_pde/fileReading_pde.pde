import processing.serial.*;
import java.util.*;
Serial mySerial;
PrintWriter output;

int getDevNumb(String[] devs) {
   for (int i = 0; i < devs.length; i++) {
     if (devs[i].equals("/dev/cu.usbmodem14111"))
       return i;
   }
   return -1;
}


boolean validInput(String s)
{
  System.out.println(s);
  String[] res = s.split(",");
  int count = 0;
  for(String curr : res)
  {
    System.out.println("a" + curr + "a");
    try
    {
      double d = Double.parseDouble(curr);
    }
    catch(NumberFormatException e)
    {
      //System.out.println(curr);
      return false;
    }
  } 
  return true;
}

void setup() {
   printArray(Serial.list());
   String[] devs = Serial.list();
   int dev_numb = getDevNumb(devs);
   mySerial = new Serial( this, devs[dev_numb], 115200 );
   output = createWriter( "position.txt" );
}
void draw() {
    if (mySerial.available() > 0 ) {
         String value = mySerial.readString();
         if ( value != null && validInput(value)) {
              output.println( value );
         }
    }
}

void keyPressed() {
    output.flush();  // Writes the remaining data to the file
    output.close();  // Finishes the file
    exit();  // Stops the program
}
