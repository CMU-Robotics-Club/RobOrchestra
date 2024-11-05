import processing.sound.*; //Input from computer mic
import themidibus.*; //MIDI output to instruments/SimpleSynth
import java.util.ArrayList;
import javax.sound.midi.*; //For reading MIDI file

void setup()
{
  String fileName = "WWRY.mid";
  midiCompress.getBestPattern(new File(dataPath(fileName)), 32);
}

void draw()
{
}
