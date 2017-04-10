import controlP5.*; //For GUI stuff

public class LogSlider extends Slider{
  public LogSlider(ControlP5 cp5, String name){
     super(cp5, name);
  }
  
  @Override public Slider setValue( float theValue ) {
    if ( isMousePressed && theValue == getValue( ) ) {
      return this;
    }
    _myInternalValue = theValue;
    _myValue = PApplet.map( theValue , _myMinReal , _myMaxReal , 0 , 1 );
    snapValue( _myValue );
    _myValue = ( _myValue <= _myMin ) ? _myMin : _myValue;
    _myValue = ( _myValue >= _myMax ) ? _myMax : _myValue;
    _myValuePosition = ( ( _myValue - _myMin ) / _myUnit );
    _myValueLabel.set( adjustValue( exp(getValue( )) ) );
    _myValue = exp(_myValue);
    _myInternalValue = exp(_myInternalValue);
    if ( triggerId == PRESSED ) {
      broadcast( FLOAT );
    }
    return this;
  }
  
  //Want to somehow override all the position stuff but not the underlying value
  //Documentation for Slider: https://github.com/sojamo/controlp5/blob/master/src/controlP5/Slider.java
  //Not sure what exactly needs to be overwritten
  
  
}