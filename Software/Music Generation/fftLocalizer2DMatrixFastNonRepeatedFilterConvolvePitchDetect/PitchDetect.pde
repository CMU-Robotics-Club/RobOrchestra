import processing.core.*;
import processing.sound.PitchDetector; //Input from computer mic
import Jama.*; //Matrix math

import ddf.minim.*;
import ddf.minim.analysis.*;

public class PitchDetect extends PApplet
{
    /** size of the buffer */
    private int timeSize;

    /** sample rate of the samples in the buffer */
    private float sampleRate;

    /** FFT object for Fast-Fourier Transform */
    //private FFT fft;

    /** spectrum "whitener" for pre-processing */
    private SpecWhitener sw;

    /** spectrum to be analyzed */
    private float[] spec;

    /** array to hold fzeros info, 1 := positive, 0 := negative */
    public int[] fzeros;
    
    private PitchDetector pd;

    public final float[] PITCHES = { 41.2f, 43.7f, 46.2f, 49.0f, 51.9f, 55.0f, 58.3f, 61.7f, 65.4f, 69.3f, 
                                    73.4f, 77.8f, 82.4f, 87.3f, 92.5f, 98.0f, 103.8f, 110.0f, 116.5f, 123.5f, 
                                    130.8f, 138.6f, 146.8f, 155.6f, 164.8f, 174.6f, 185.0f, 196.0f, 207.7f, 220.0f, 
                                    233.1f, 246.9f, 261.6f, 277.2f, 293.7f, 311.1f, 329.6f, 349.2f, 370.0f, 392.0f, 
                                    415.3f, 440.0f, 466.2f, 493.9f, 523.3f, 554.4f, 587.3f, 622.3f, 659.3f, 698.5f, 
                                    740.0f, 784.0f, 830.6f, 880.0f, 932.3f, 987.8f, 1046.5f, 1108.7f, 1174.7f, 1244.5f, 
                                    1318.5f, 1396.9f, 1480.0f, 1568.0f, 1661.2f, 1760.0f, 1864.7f, 1979.5f, 2093.0f }; // 69 tones

    public PitchDetect(int timeSize, float sampleRate)
    {
        this.timeSize = timeSize;
        this.sampleRate = sampleRate;
        //fft = new FFT(timeSize, sampleRate);
        //fft.window(FFT.HAMMING);
        sw = new SpecWhitener(timeSize, sampleRate);
        spec = new float[timeSize/2+1];
        fzeros = new int[PITCHES.length];
        //pd = new PitchDetector(this, 0.55);
        //pd.input(in);
    }
  
    /**
     *  This method takes an AudioBuffer object as argument.
     *  It detects all notes in presence in buffer.
     */
    public float[] detect(float[] spec2)
    {
        fzeros = new int[PITCHES.length];
        // perform fft on the buffer
        //for (int i = 0; i < spec2.length; i++) 
        //{
        //  spec2[i] = 1000 * spec2[i];
        //  //println(spec[i]);
        //}
        
        // spectrum pre-processing
        sw.whiten(spec2);
        spec = sw.wSpec;
        spec = spec2;

        // iteratively find all presented pitches
        float test = 0, lasttest = 0;
        int loopcount = 1;
        float[] fzeroInfo = new float[3]; // ind 0 is the pitch, ind 1 its salience, ind 2 its ind in PITCHES
        //println("start loop");
        while (true) {
            
            detectfzeronew(spec2, fzeroInfo);
            lasttest = test;
            test = (test + fzeroInfo[1]) / pow(loopcount, .7f);
            if (test <= lasttest) break;
            loopcount++;
            if (loopcount > 5) break;

            // subtract the information of the found pitch from the current spectrum
            for (int i = 1; i * fzeroInfo[0] < sampleRate / 2; ++i) {
                int partialInd = floor(i * fzeroInfo[0] * timeSize / sampleRate);
                if (partialInd < 1) continue;
                if (partialInd > 510) continue;
                float weighting = (fzeroInfo[0] + 52) / (i * fzeroInfo[0] + 320);
                spec[partialInd] *= (1 - 0.89f * weighting);
                spec[partialInd-1] *= (1 - 0.89f * weighting);    
            }

            // update fzeros
            if ((int) fzeroInfo[2] >= PITCHES.length) break;
            if (fzeros[(int) fzeroInfo[2]] == 0) fzeros[(int) fzeroInfo[2]] = 1;
            //else fzeros[(int) fzeroInfo[2]] = 0;
            
        }
        //println("end loop");
        return spec2;
    }
  
    // utility function for detecting a single pitch
    private void detectfzero(float[] spec, float[] fzeroInfo)
    {
        float maxSalience = -1000000.0f;
        for (int j = 0; j < PITCHES.length; ++j) {
            float cSalience = 0; // salience of the candidate pitch
            float val = 0;
            for (int i = 1; i * PITCHES[j] < sampleRate / 2; ++i) {
                int bin = round(i * PITCHES[j] * timeSize / sampleRate);
                // use the largest value of bins in vicinity
                if (bin < 3) continue;
                if (bin > 510) continue;
                if (bin == timeSize/2) val = max(spec[bin-3], spec[bin-2], spec[bin-1]);
                else if (bin == timeSize/2-1) val = max(max(spec[bin-3], spec[bin-2], spec[bin-1]), spec[bin]);
                else val = max(max(spec[bin-3], spec[bin-2], spec[bin-1]), spec[bin], spec[bin+1]);
                // calculate the salience of the current candidate
                float weighting = (PITCHES[j] + 52) / (i * PITCHES[j] + 320);
                if (Float.isNaN(val)) continue;
                //print("val : " + val);
                //println("weighting : " + weighting);
                cSalience += val * weighting;
            }
            //println(cSalience);
            if (cSalience > maxSalience) {
                maxSalience = cSalience;
                fzeroInfo[0] = PITCHES[j];
                fzeroInfo[1] = cSalience;
                fzeroInfo[2] = j;
            }
        }
    }
    
    private void detectfzeronew(float[] spec3, float[] fzeroInfo)
    {
      float max = 0;
      int maxind = 0;
      for (int i = 0; i < spec3.length; i++)
      {
        if (spec3[i] > max)
        {
          max = spec3[i];
          maxind = i;
        }
      }
      fzeroInfo[0] = max(1, maxind * sampleRate / (2*spec3.length));
      //println("calculated frequency: " + fzeroInfo[0]);
      
      fzeroInfo[1] = max;
      for (int i = 1; i < PITCHES.length; i++)
      {
        if (PITCHES[i] > fzeroInfo[0])
        {
          if (fzeroInfo[0] - PITCHES[i-1] < PITCHES[i] - fzeroInfo[0])
          {
            fzeroInfo[2] = i-1;
            //println("found " + PITCHES[i-1]);
            break;
          }
          else
          {
             fzeroInfo[2] = i;
            //println("found " + PITCHES[i]);
            break;
          }
        }
      }
      //println("pitches : " + PITCHES[(int) fzeroInfo[2]]);
      
    }
    
    void dispProbArray(Matrix A, boolean isBeat){

      
      int n = A.getRowDimension();
      for(int i = 0; i < n; i++){
        fill(0);
        if(isBeat){
          fill(200, 100, 0);
        }
        rect(i*width/n, (1- (float)A.get(i, 0))*height, width/n, (float) A.get(i, 0)*height);
      }
    }
}
