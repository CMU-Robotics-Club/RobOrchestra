public class Voices{
  
  public Note bass;
  public Note alto;
  public Note soprano;
  public Note tenor;
  public long timestamp;
  
  public Voices(Note bass, Note soprano, long timestamp){
    this.bass = bass;
    this.soprano = soprano;
    this.timestamp = timestamp;
  }
 
}