import javax.sound.midi.MidiSystem;
import javax.sound.midi.*;

public class DeviceList {
    private MidiDevice.Info[] outputDevices;

    public DeviceList() {
        this.outputDevices = MidiSystem.getMidiDeviceInfo();
    }

    public MidiDevice.Info[] getDeviceList(){
        return this.outputDevices;
    }

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
