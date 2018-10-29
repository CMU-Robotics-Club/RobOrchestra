import javax.sound.midi.ShortMessage;

//A Midi note
public class NoteMessage {
    private int pitch;
    private int volume;
    private int channel;
    private ShortMessage note;

    //arguments: Midi pitch(> 0), volume(0-127) and channel(0-15)
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

    //returns pitch as integer
    public int getPitch(){
        return this.pitch;
    }

    //returns volume/velocity as integer
    public int getVolume(){
        return this.volume;
    }

    //returns channel as integer
    public int getChannel(){
        return this.channel;
    }

    //returns note as type ShortMessage
    public ShortMessage getNote() {
        return this.note;
    }

    //prints pitch, volume and channel of note to console
    public String toString(){
        String output = "Note On\n";
        output += "Pitch: " + getPitch() + "\n";
        output += "Volume: " + getVolume() + "\n";
        output += "Channel: " + getChannel() + "\n";

        return output;
    }
}
