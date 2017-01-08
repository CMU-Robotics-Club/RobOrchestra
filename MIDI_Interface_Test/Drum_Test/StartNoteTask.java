import java.util.TimerTask;
import java.util.Date;


// Create a class extends with TimerTask
// Schedules start of a note
public class StartNoteTask extends TimerTask {

	NoteMessage note;
	Orchestra robo;

	public StartNoteTask(NoteMessage n, Orchestra r) {
		note = n;
		robo = r;
	}

	public void run() {
		robo.sendMidiNote(note);
	}
}