import controlP5.*; //For GUI stuff

public class LogSlider extends Slider{
  public LogSlider(ControlP5 cp5, String name){
     super(cp5, name);
  }
  //Want to somehow override all the position stuff but not the underlying value
  //Documentation for Slider: https://github.com/sojamo/controlp5/blob/master/src/controlP5/Slider.java
  //Not sure what exactly needs to be overwritten
}