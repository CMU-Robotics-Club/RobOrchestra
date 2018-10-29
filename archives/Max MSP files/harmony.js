inlets = 1;
outlets = 1;

var scale = [60, 62, 64, 65, 67, 69, 71]

function msg_int(i) {
	var note = getFirst(jsarguments[1], scale) //Get the last note
	var curchord = []
	var base = i + 60
	curchord[0] = base //outputs root

			//major chords
			if(i == 0 || i == 5 || i == 7) {
				curchord[1] = base+4; //outputs 3rd
				curchord[2] = base+7; //outputs 5th
			}
			
			//minor chords
			else if(i == 2 || i == 9) {
				curchord[1] = base + 3;
				curchord[2] = base + 7;
			}
			
			//dimished chords
			else {
				curchord[1] = base + 3;
				curchord[2] = base + 6;
			}
			
			curchord[3] = base + 12; //outputs root octave
	
	for(var x = 0; x < 100; x++){
		var rand = Math.random()
		if(rand <= 0.33){
			if(inChord(scale[(note+6)%7], curchord)){
				jsarguments[1] = scale[(note+6)%7]
				break
			}
		}
		if(rand >= 0.67){
			if(inChord(scale[(note+1)%7], curchord)){
				jsarguments[1] = scale[(note+1)%7]
				break
			}
		}
		if(rand > 0.33 && rand < 0.67){
			if(inChord(scale[note], curchord)){
				jsarguments[1] = scale[note]
				break
			}
		}
		if(x == 100){
			//Override in case you had really bad luck before
			jsarguments[1] = scale[note]
		}
	}
	outlet(0, jsarguments[1])
	
	return
}

function inChord(note, chord){
	for(var x = 0; x < chord.length; x++){
		if(chord[x] == note){
			return true
		}
	}
	return false
}

function getFirst(val, myArray){
	for(var x = 0; x < myArray.length; x++){
		if(myArray[x] % 12 + 60 == val){
			return x
		}
	}
	return(-1)
}