inlets = 1;
outlets = 1;

//if note is out of range of xylobot
//decrement note by an octave to put it back in range
function msg_int(note) {
	
	if(note > 76) {
		outlet(0,note-12);
	}
	
	else{
		outlet(0,note);
	}
}