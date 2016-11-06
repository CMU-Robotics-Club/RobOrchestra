
//Gets list of available MIDI output devices
DeviceList midiOutputs = new DeviceList();
System.out.println(midiOutputs);

//Opens a connection to a specified MIDI output device
//-1 defaults to computer speakers
int deviceIndex = -1;
Orchestra robo = new Orchestra(deviceIndex);
System.out.println(robo);

//plays a chromatic C scale
for(int i = 60; i < 72; i++) {
  
  //creates a MIDI message
  //arguments: pitch, velocity, channel
  NoteMessage note = new NoteMessage(i, 100, 1);
  
  //sends MIDI message to output device
  robo.sendMidiNote(note);
  
  //delay program for length of note
  delay(500);
  
  //end the MIDI note
  robo.sendNoteOff(note);
}

//Closes the MIDI output device
robo.close();