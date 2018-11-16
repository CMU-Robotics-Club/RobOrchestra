import gab.opencv.*;
import processing.video.*;
import java.awt.Rectangle;

Capture video;
OpenCV opencv;
PImage src, colorFilteredImage;
ArrayList<Contour> contours;

// <1> Set the range of Hue values for our filter
int rangeLow = 20;
int rangeHigh = 35;

int[] p1 = {0, 0};
int[] p2 = {0, 0};
int time1 = 0;
int time2 = 0;
double prevV = 0;
double currV = 0;
int beat_count = 0;
int beat_buffer = 0;

int index = 0;

double velocity() {
  //System.out.println(p2[0] + " " +  p3[0] + " " + p2[1] + " " + p3[1]);
  int[] v1 = {p1[0] - p2[0], p1[1] - p2[1]};
  double v1Length = Math.sqrt(Math.pow(v1[0], 2) + Math.pow(v1[1], 2));
  int time = time1 - time2;
  double velocity = v1Length/time;
  return velocity;
}

void setup() {
  video = new Capture(this, 640, 480);
  video.start();
  
  opencv = new OpenCV(this, video.width, video.height);
  contours = new ArrayList<Contour>();
  
  size(1280, 480, P2D);
}

void draw() {
  
  // Read last captured frame
  if (video.available()) {
    video.read();
  }

  // <2> Load the new frame of our movie in to OpenCV
  opencv.loadImage(video);
  
  // Tell OpenCV to use color information
  opencv.useColor();
  src = opencv.getSnapshot();
  
  // <3> Tell OpenCV to work in HSV color space.
  opencv.useColor(HSB);
  
  // <4> Copy the Hue channel of our image into 
  //     the gray channel, which we process.
  opencv.setGray(opencv.getH().clone());
  
  // <5> Filter the image based on the range of 
  //     hue values that match the object we want to track.
  opencv.inRange(rangeLow, rangeHigh);
  
  // <6> Get the processed image for reference.
  colorFilteredImage = opencv.getSnapshot();
  
  // <7> Find contours in our range image.
  //     Passing 'true' sorts them by descending area.
  contours = opencv.findContours(true, true);
  
  // <8> Display background images
  image(src, 0, 0);
  image(colorFilteredImage, src.width, 0);
  
  // <9> Check to make sure we've found any contours
  if (contours.size() > 0) {
    // <9> Get the first contour, which will be the largest one
    Contour biggestContour = contours.get(0);
    
    // <10> Find the bounding box of the largest contour,
    //      and hence our object.
    Rectangle r = biggestContour.getBoundingBox();
    
    // <11> Draw the bounding box of our object
    noFill(); 
    strokeWeight(2); 
    stroke(255, 0, 0);
    rect(r.x, r.y, r.width, r.height);
    
    p2[0] = p1[0];
    p2[1] = p1[1];
    time2 = time1;
    p1[0] = r.x + r.width/2;
    p1[1] = r.y + r.height/2;
    time1 = millis();
  }
  prevV = currV;
  currV = velocity();
  if (prevV > currV*2.5 && millis() > beat_buffer + 1000){
    System.out.println("BEAT");
    System.out.println(beat_count);
    beat_count++;
    beat_buffer = millis();
  }
}

void mousePressed() {
  color c = get(mouseX, mouseY);
  println("r: " + red(c) + " g: " + green(c) + " b: " + blue(c));
   
  int hue = int(map(hue(c), 0, 255, 0, 180));
  println("hue to detect: " + hue);
  
  rangeLow = hue - 5;
  rangeHigh = hue + 5;
}
