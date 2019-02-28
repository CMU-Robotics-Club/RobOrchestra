import javax.sound.midi.InvalidMidiDataException;
import javax.sound.midi.MidiSystem;
import javax.sound.midi.MidiUnavailableException;
import javax.sound.midi.ShortMessage;
import javax.sound.midi.Receiver;
import javax.sound.midi.*;
import java.util.ArrayList;
import java.util.List;
  
  MidiDevice device;
  MidiDevice.Info[] infos = MidiSystem.getMidiDeviceInfo();
  for (int i = 0; i < infos.length; i++) {
    try {
      device = MidiSystem.getMidiDevice(infos[i]);
      String output = "[" + i + "]: " + device.getDeviceInfo().toString();
      System.out.println(output);
    } catch(Exception e) {
      System.out.println(e);
    }
  }
  
  try {
    device = MidiSystem.getMidiDevice(infos[2]);
    if (!(device.isOpen())) {
      try {
        device.open();
      } catch (MidiUnavailableException e) {
        System.out.println(e);
      }
    }
  
    ShortMessage myMsg = new ShortMessage();
    // Start playing the note Middle C (60), 
    // moderately loud (velocity = 93).
    try {
      myMsg.setMessage(ShortMessage.NOTE_ON, 0, 60, 93);
    } catch(InvalidMidiDataException e) {
      System.out.println(e);
    }
     
    long timeStamp = -1;
    
    try {
      Receiver rcvr = device.getReceiver();
      rcvr.send(myMsg, timeStamp);
    } catch(MidiUnavailableException e) {
      System.out.println(e);
    }
  } catch(Exception e) {
    System.out.println("Could not open device");
  }