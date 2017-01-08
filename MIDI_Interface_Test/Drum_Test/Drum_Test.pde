import java.lang.Math;
import java.util.Timer;
import java.util.TimerTask;
import java.util.Date;


//Gets list of available MIDI output devices
DeviceList midiOutputs = new DeviceList();
System.out.println(midiOutputs);

//Opens a connection to a specified MIDI output device
//-1 defaults to computer speakers
int deviceIndex = 0;
Orchestra robo = new Orchestra(deviceIndex);
System.out.println(robo);

float[] xylo = {1.0, 0.2, 0.5, 0.1, 0.8, 0.1, 0.7, 0.2, 1.0, 0.1, 0.4, 0.1, 1.0, 0.0, 0.8, 0.0};
int[] xyloNotes = {59, 60, 62, 64, 65, 67, 69, 71};
int xyloStart = 1;

//Probability arrays for each drum, length 16 beats
//kick
float[] kick = {0.7, 0.0, 0.4, 0.1, 0.0, 0.0, 0.0, 0.2, 0.0, 0.0, 0.5, 0.0, 0.0, 0.0, 0.0, 0.3};
//hihat
float[] hihat = {0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.7, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0, 0.7};
//snare
float[] snare = {0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.5, 0.0, 0.2, 0.0, 0.0, 1.0, 0.0, 0.0, 0.3};

//Creates scheduler for MIDI messages
Timer timer = new Timer();
long t = System.currentTimeMillis() + 500;
Date date = new Date(t);

//plays for 8 bars of 16 beats
for(int i = 0; i < 128; i++) {
  
  double checkK = Math.random();
  double checkH = Math.random();
  double checkS = Math.random();
  double checkX = Math.random();
  double checkNote = Math.random();
  
  System.out.println(checkX);
  
  //creates a MIDI message
  //arguments: pitch, velocity, channel
  //9 is the percussion channel
  //default to 0 indicating didn't play
  NoteMessage kickNote = new NoteMessage(0,100,9);
  NoteMessage hiNote = new NoteMessage(0,100,9);
  NoteMessage snareNote = new NoteMessage(0,100,9);
  NoteMessage xyloNote = new NoteMessage(0,100,0);
  
  date = new Date(t);
  
  //schedules start of Notes
  if(checkK <= kick[i % 16]) {
    kickNote = new NoteMessage(36, 100, 9);
    StartNoteTask kickTask = new StartNoteTask(kickNote, robo);
    timer.schedule(kickTask, date);
  }
  if(checkH <= hihat[i % 16]) {
    hiNote = new NoteMessage(44, 100, 9);
    StartNoteTask hiTask = new StartNoteTask(hiNote, robo);
    timer.schedule(hiTask, date);
  }
  if(checkS <= snare[i % 16]) {
    snareNote = new NoteMessage(38, 100, 9);
    StartNoteTask snareTask = new StartNoteTask(snareNote, robo);
    timer.schedule(snareTask, date);
  }
  if(checkX <= xylo[i % 16]) {
    if(checkNote < 0.5 && xyloStart > 0) {
      xyloStart--;
    }
    else if(checkNote >= 0.5 && xyloStart < (xyloNotes.length - 1)) {
      xyloStart++;
    }
    xyloNote = new NoteMessage(xyloNotes[xyloStart],100,1);
    StartNoteTask xyloTask = new StartNoteTask(xyloNote, robo);
    timer.schedule(xyloTask, date);
  }
  
  //delay program for length of note
  t = t + 75;
  date = new Date(t);
  
  //schedules end of MIDI notes that played
  if(kickNote.getPitch() != 0) {
    EndNoteTask endKick = new EndNoteTask(kickNote, robo);
    timer.schedule(endKick, date);
  }
  if(hiNote.getPitch() != 0) {
    EndNoteTask endHi = new EndNoteTask(hiNote, robo);
    timer.schedule(endHi, date);
  }
  if(snareNote.getPitch() != 0) {
    EndNoteTask endSnare = new EndNoteTask(snareNote, robo);
    timer.schedule(endSnare, date);
  }
  if(xyloNote.getPitch() != 0) {
    System.out.println("hi");
    EndNoteTask endXylo = new EndNoteTask(xyloNote, robo);
    timer.schedule(endXylo, date);
  }
  
  t = t + 75;
}

//schedules close of the MIDI output device
t = t + 200;
date = new Date(t);
CloseReceiver close = new CloseReceiver(robo);
timer.schedule(close, date);