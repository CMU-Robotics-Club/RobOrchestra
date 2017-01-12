import javax.sound.midi.MidiSystem;
import javax.sound.midi.*;


//List of available MIDI outputs
public class DeviceList {
    private MidiDevice.Info[] outputDevices;

    public DeviceList() {
        this.outputDevices = MidiSystem.getMidiDeviceInfo();
    }


    //Returns an array of available MIDI outputs
    //Array items are of the type MidiDevice.Info
    public MidiDevice.Info[] getDeviceList(){
        return this.outputDevices;
    }

    //Prints an indexed list of available MIDI outputs to the console
    public String toString() {
        MidiDevice device;
        String output = "Available MIDI Output Ports: \n";
        for (int i = 0; i < outputDevices.length; i++) {
            try {
                device = MidiSystem.getMidiDevice(outputDevices[i]);
                output += "[" + i + "]: " + device.getDeviceInfo().toString() + "\n";
            } catch(Exception e) {
                System.out.println("Error getting MIDI devices");
                System.out.println(e);
            }
        }

        return output;
    }
}
