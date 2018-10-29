//Put in code for webcam stream here (takes no input, constantly outputs location of ball)

public class Webcam_Stream{
  
  int TIME_DELAY;
 
  public Webcam_Stream(int delay){
    //NEEDS TO BE FILLED IN
    TIME_DELAY = delay;
  }
  
  public int[] get_ball_center(){
    //NEEDS TO BE FILLED IN (this is open cv part)
    
    
    
    return new int[]{};
  }
  
  
  public Point_Vector ball_vec(){
    int[] point1 = get_ball_center();
    delay(TIME_DELAY);
    int[] point2 = get_ball_center();
    return new Point_Vector(point1[0],point1[1],point2[0],point2[1]);
  }
  
}
