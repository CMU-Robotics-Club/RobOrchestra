import processing.sound.*;
import themidibus.*;
import java.io.File;
import java.lang.*;
import java.util.Arrays;
import java.util.ArrayList;
import java.io.FileInputStream;

import javax.sound.midi.MetaMessage;
import javax.sound.midi.MidiEvent;
import javax.sound.midi.MidiMessage;
import javax.sound.midi.MidiSystem;
import javax.sound.midi.Sequence;
import javax.sound.midi.ShortMessage;
import javax.sound.midi.Track;
import javax.sound.midi.InvalidMidiDataException;

FFT fft; //Not used, we're using PitchDetector apparently
AudioIn in;
PitchDetector pd;
MidiBus myBus;
Amplitude amp;
int bands = 128;
float[] spectrum = new float[bands];
void setup()
{

  size(1000, 800);
  background(255);
  System.out.println(Sound.list());
  
  
  // Create an Input stream which is routed into the Amplitude analyzer
  //fft = new FFT(this, bands);
  pd = new PitchDetector(this, 0.55); //Last arg is confidence - increase to filter out more garbage
  in = new AudioIn(this, 0);
  amp = new Amplitude(this);
  fft = new FFT(this, bands);

  in.amp(1);
  // start the Audio Input
  in.start();
  
  // patch the AudioIn
  //fft.input(in);
  pd.input(in);
  amp.input(in);
  fft.input(in);
  background(255);
}    

void draw()
{
  background(255);
  fft.analyze(spectrum);
  float freq = pd.analyze();
  float amplitude = amp.analyze();
  System.out.println(amplitude);
  
  for(int i = 0; i < bands; i++)
  {
  // The result of the FFT is normalized
  // draw the line for frequency band i scaling it up by 5 to get more amplitude.
  line( i * (1024/bands), height, i * (1024/bands), height - spectrum[i]*height );
  }/*
    yOld = y;
    y = freq;
    x++;
    stroke(255, 0, 0);
    line(x-1, height - yOld, x, height - y);
    stroke(0, 0, 255);
    line(x-1, height - ampOld * ampScale, x, height - amplitude * ampScale);
    ampOld = amplitude;
    //System.out.println(freq);
  
  midi = MIDIfromPitch(y);
  
  if (midi > 0 && amplitude > ampThreshold)
  {
    //if (notes.size() > 0) notes.remove(0);
    notes.add(midi);
    
    //Note newNote = new Note(0, midi, 50);
    
    //if (oldNote != null)
    //{
    //  myBus.sendNoteOff(oldNote);
    //}
    //myBus.sendNoteOn(newNote);
    //oldNote = newNote;
    
      Note newNote = new Note(0, midi, 0); //Low volume for now so we don't pick up ourself
      if (oldNote != null){
        myBus.sendNoteOff(oldNote);
      }
      myBus.sendNoteOn(newNote);
      oldNote = newNote;
      
      osc.freq((float)pitchFromMIDI(midi));
      osc.play();
      println(MIDIfromPitch(y));
  }
  else{
    osc.stop();
  }

  */
  delay(10);
  
  //System.out.println(notes);
}
