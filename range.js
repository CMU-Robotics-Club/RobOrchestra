inlets = 4;
outlets = 4;

function msg_int(note) {
	
	if(inlet == 1) {
		if(note > 76) {
			outlet(1,note-8);
		}
	}
	
	else if(inlet == 2) {
		if(note > 76) {
			outlet(2,note-8);
		}
	}
	
	else if(inlet == 3) {
		if(note > 76) {
			outlet(3,note-8);
		}
	}
	
	else {
		if(note > 76) {
			outlet(4,note-8);
		}
	}
	
}