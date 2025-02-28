final class SpecWhitener extends PApplet
{
    private int bufferSize; // the size of the Fourier Transform
    private float sr; // the sample rate of the samples in the buffer
    private float[] cenFreqs; // center frequencies of bandpass filter banks
    private float[] cenFreqsSteps; // steps of increment
    private int[][] banksRanTable; // each row is a filter; cols are lower band index and upper band index this filter covers
  
    public float[] wSpec; // the whitened specturm
  
    public SpecWhitener(int bufferSize, float sr)
    {
        this.bufferSize = bufferSize;
        this.sr = sr;

        // calculate center frequencies
        cenFreqs = new float[32];
        for (int i = 0; i < cenFreqs.length; ++i)
        {
          cenFreqs[i] = 229 * (pow(10, (i + 1) / 21.4f) - 1);
        }
        
        cenFreqsSteps = new float[32];
        for (int i = 1; i < cenFreqsSteps.length; ++i) cenFreqsSteps[i] = cenFreqs[i] - cenFreqs[i - 1];

        // calculate the filter banks range table
        banksRanTable = new int[32][2];
        float bandIndLow = 0, bandIndMid = 0, bandIndUp = 0;
        for (int i = 1; i < cenFreqs.length - 1; ++i) {
            if (i == 1) {
                bandIndLow = (cenFreqs[i - 1] * bufferSize) / sr;
                bandIndMid = (cenFreqs[i] * bufferSize) / sr;
                bandIndUp = (cenFreqs[i + 1] * bufferSize) / sr;
            } else {
                bandIndLow = bandIndMid;
                bandIndMid = bandIndUp;
                bandIndUp = (cenFreqs[i + 1] * bufferSize) / sr;
            }
            banksRanTable[i][0] = ceil(bandIndLow);
            banksRanTable[i][1] = floor(bandIndUp);
        }

        wSpec = new float[bufferSize / 2 + 1];
    }
  
    public void whiten(float[] spec)
    {
        // calculate bandwise compression coefficients
        float[] bwCompCoef = new float[32];
        for (int j = 1; j < bwCompCoef.length - 1; ++j) {
            float sum = 0;
            for (int i = banksRanTable[j][0]; i <= banksRanTable[j][1]; ++i) {
                float bandFreq = i * sr / bufferSize;
                if (bandFreq < cenFreqs[j]) {
                    sum += pow(spec[i], 2) * (bandFreq - cenFreqs[j - 1]) / cenFreqsSteps[j];
                } else {
                    sum += pow(spec[i], 2) * (cenFreqs[j + 1] - bandFreq) / cenFreqsSteps[j + 1];
                }
            }
            bwCompCoef[j] = pow(pow(sum / bufferSize, .5f), .33f-1);
        }

        // calculate steps of increment of bwCompCoef
        float[] bwCompCoefSteps = new float[32];
        for (int i = 1; i < bwCompCoef.length; ++i) bwCompCoefSteps[i] = bwCompCoef[i] - bwCompCoef[i - 1];

        // whitens
        float compCoef = 0;
        int bankCount = 1;
        for (int i = banksRanTable[1][0]; i <= banksRanTable[30][1]; ++i) {
            float bandFreq = i * sr / bufferSize;
            if (bandFreq > cenFreqs[bankCount]) bankCount++;
            if (bwCompCoefSteps[bankCount] > 0) {
                compCoef = (bwCompCoefSteps[bankCount]*(bandFreq-cenFreqs[bankCount-1])/cenFreqsSteps[bankCount])+bwCompCoef[bankCount-1];
            } else {
                compCoef = (-bwCompCoefSteps[bankCount]*(cenFreqs[bankCount]-bandFreq)/cenFreqsSteps[bankCount])+bwCompCoef[bankCount];
            }
            if (!(compCoef == Float.POSITIVE_INFINITY || compCoef == Float.NEGATIVE_INFINITY))
              wSpec[i] = spec[i] * compCoef;
            else
              wSpec[i] = spec[i];
        }
    }
}
