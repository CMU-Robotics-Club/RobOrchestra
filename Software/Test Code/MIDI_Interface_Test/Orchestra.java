import javax.sound.midi.MidiSystem;
import javax.sound.midi.Receiver;
import javax.sound.midi.*;

public class Orchestra {

    private MidiDevice outputBus;
    private Receiver outputReceiver;

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

    public void sendMidiNote(NoteMessage note) {
        long timestamp = -1;
        outputReceiver.send(note.getNote(), timestamp);
    }
    
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