public class Point_Vector{

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
  
  public int get_x(){
    return loc_x;
  }
  
  public int get_y(){
    return loc_y;
  }
  
  
}
