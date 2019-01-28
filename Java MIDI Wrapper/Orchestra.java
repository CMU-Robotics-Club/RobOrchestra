import javax.sound.midi.MidiSystem;
import javax.sound.midi.Receiver;
import javax.sound.midi.*;

//Midi output device
//Used to route NoteMessage objects to specified output
public class Orchestra {

    private MidiDevice outputBus;
    private Receiver outputReceiver;

    //takes as input integer of valid MIDI output port
    //list of valid MIDI output ports are given by DeviceList() class
    public Orchestra(int outputPort) {

        if(outputPort == -1) {
            try {
                this.outputReceiver = MidiSystem.getReceiver();
            } catch (Exception e) {
                System.out.println("Unable to connect to MIDI receiver");
                System.out.println(e);
            }
        }
        else {
            MidiDevice.Info[] infos = MidiSystem.getMidiDeviceInfo();
            try {
                this.outputBus = MidiSystem.getMidiDevice(infos[outputPort]);

                if (!(this.outputBus.isOpen())) {
                    try {
                        this.outputBus.open();
                    } catch (Exception e) {
                        System.out.println("Unable to open MIDI device.");
                        System.out.println(e);
                    }
                }

                try {
                    this.outputReceiver = this.outputBus.getReceiver();
                } catch (Exception e) {
                    System.out.println("Unable to connect to MIDI receiver");
                    System.out.println(e);
                }

            } catch (Exception e) {
                System.out.println("Unable to connect to MIDI device");
                System.out.println(e);
            }
        }
    }

    //takes in a NoteMessage object and creates a noteOn message
    //immediately sends noteOn message to specified Midi Output
    public void sendMidiNote(NoteMessage note) {
        long timestamp = -1;
        outputReceiver.send(note.getNote(), timestamp);
    }
    
    //takes in a NoteMessage object and creates a noteOff message
    //immediate sends noteOff message to specified Midi Output
    public void sendNoteOff(NoteMessage note) {
      ShortMessage noteOff = new ShortMessage();
      try {
          noteOff.setMessage(ShortMessage.NOTE_OFF, note.getChannel(), note.getPitch(), 0);
      } catch(Exception e) {
          System.out.println("Invalid note data.");
          System.out.println(e);
      }
      
      long timestamp = -1;
      outputReceiver.send(noteOff, timestamp);
    }

    public void close() {
        if(this.outputBus != null && this.outputBus.isOpen()){
          this.outputBus.close();
        }
    }

    //Prints name of specified output device
    public String toString(){
        String output =  "MIDI Output Device: ";
        if(outputBus != null) {
            output += outputBus.getDeviceInfo().toString();
        }
        else {
            output += "Default Speakers";
        }
        return output;
    }
}