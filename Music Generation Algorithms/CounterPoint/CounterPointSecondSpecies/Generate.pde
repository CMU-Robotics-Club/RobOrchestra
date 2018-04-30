import java.util.*;
import arb.soundcipher.*;

public class Generate{
  
  private GenerateFirstSpecies gen1;
  private Note TONIC;
  private SCScore score;
  
  public Generate(Note TONIC){
    gen1 = new GenerateFirstSpecies(TONIC);
    this.TONIC = TONIC;
    score = gen1.score;
  }
  
  
  
  
}