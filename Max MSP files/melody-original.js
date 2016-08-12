inlets = 4;
outlets = 1;

function list(notes) {
	
	if(inlet == 0) {
		var currentNote = notes;
		post(currentNote);
	}
	
	else if(inlet == 1) {
		var tonic = notes;
		post(tonic);
	}
	
	else if(inlet == 2) {
		var third = notes;
		post(third);
	}
	
	else {
		var fifth = notes;
		post(fifth);
	}
	
	var nextNotes = [tonic, third, fifth];
	
	var difference = Math.abs(currentNote-notes[0]);
	var next = notes[0];
	
	for(var i = 0; i < nextNotes.length; i++) {
    	if(Math.abs(currentNote-nextNotes[i]) < difference) {
			difference = Math.abs(currentNote-nextNotes[i]);
			next = nextNotes[i];
		}
	}
	
	outlet(0, next);

}