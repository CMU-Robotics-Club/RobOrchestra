import processing.sound.*; //Input from computer mic
import themidibus.*; //MIDI output to instruments/SimpleSynth
import java.util.ArrayList;
import javax.sound.midi.*; //For reading MIDI file

void setup()
{
  String fileName = "Megalovania.mid";
  midiCompress mc = new midiCompress(fileName, 16);
}

void draw()
{
}
