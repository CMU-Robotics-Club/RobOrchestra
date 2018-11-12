public class Point_Vector{
  
//have the location of where the ball is and then which direction it's going
//make a vector based on previous vectors
//get the most current point vector
//investigate what the CV interaction is outputting



  private int loc_x;
  private int loc_y;
  private int vec_x;
  private int vec_y;
  
  public Point_Vector(int a, int b, int c, int d){
    loc_x = a;
    loc_y = b;
    vec_x = c - a;
    vec_y = d - b;
  }
  
  //Returns x component of direction
  public int get_vector_x(){
    return vec_x; 
  }
  
  //Returns y component of direction
  public int get_vector_y(){
    return vec_y;
  }
  
  //Returns magnitude
  public double get_magnitude(){
    return Math.pow(((Math.pow(vec_x,2))+(Math.pow(vec_y,2))),0.5);
  }
  
  public int get_x(){
    return loc_x;
  }
  
  public int get_y(){
    return loc_y;
  }
  
  
}