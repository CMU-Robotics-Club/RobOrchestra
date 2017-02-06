import javax.sound.midi.ShortMessage;

public class NoteMessage {
    public int pitch;
    public int volume;
    public int channel;
    private ShortMessage note;

    public NoteMessage(int pitch, int volume, int channel){
        this.pitch = pitch;
        this.volume = volume;
        this.channel = channel;

        this.note = new ShortMessage();
        try {
            this.note.setMessage(ShortMessage.NOTE_ON, channel, pitch, volume);
        } catch(Exception e) {
            System.out.println("Invalid note data.");
            System.out.println(e);
        }
    }

    public int getPitch(){
        return this.pitch;
    }

    public int getVolume(){
        return this.volume;
    }

    public int getChannel(){
        return this.channel;
    }

    public ShortMessage getNote() {
        return this.note;
    }

    public String toString(){
        String output = "Note On\n";
        output += "Pitch: " + getPitch() + "\n";
        output += "Volume: " + getVolume() + "\n";
        output += "Channel: " + getChannel() + "\n";

        return output;
    }
}