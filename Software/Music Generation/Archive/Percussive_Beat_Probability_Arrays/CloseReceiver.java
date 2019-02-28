import java.util.TimerTask;
import java.util.Date;


// Create a class extends with TimerTask
// Schedules closing of receiver at end of MIDI messages
public class CloseReceiver extends TimerTask {

	Orchestra robo;

	public CloseReceiver(Orchestra r) {
		robo = r;
	}

	public void run() {
		robo.close();
	}
}