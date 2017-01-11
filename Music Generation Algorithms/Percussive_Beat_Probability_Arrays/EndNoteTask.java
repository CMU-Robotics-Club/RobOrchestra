import java.util.TimerTask;
import java.util.Date;

// Create a class extends with TimerTask
// Schedules end of a note
public class EndNoteTask extends TimerTask {

	NoteMessage note;
	Orchestra robo;

	public EndNoteTask(NoteMessage n, Orchestra r) {
		note = n;
		robo = r;
	}

	public void run() {
		robo.sendNoteOff(note);
	}
}