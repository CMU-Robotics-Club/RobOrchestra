inlets = 1
outlets = 4

var test = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76]
var scale = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76]
var out = []
var curchord = []

var defpnum = 4 //Default phrase number

//Random jsarguments stuff:
//0: Filename
//1: Old note
//2: Number of phrases left
//3: Current chord
//4: Boolean flag tracking whether you're overcounting

//Good transitions: 0, 7, 11
//Bad transitions: 5

function msg_int(newchord){
	//WARNING: This code may or may not be a complete mess.
	//I started trying to clean it up, so it's better now, but it's still not great.
	
	//Inputs in MIDI
	//Old note is jsarguments[1]
	//New note is newnote
	if(newchord == 0){
		post(jsarguments[3]) //Old chord (for debugging)
		post("\n")
	}
	else{
		jsarguments[4] = 0 //No longer potentially double-counting the tonic
	}
	jsarguments[3] = newchord
	
	var n1 = 0
	var n2 = 0
	
	//Get new note. Pull a note from the current chord
	var i = jsarguments[3]
	var base = i+60 //root
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
			
	//Force tonic chord to output a tonic note
	if(i == 0){
		curchord[0] = 60
		curchord[1] = 60
		curchord[2] = 72
		curchord[3] = 72
	}
			
	//curchord now has the four notes to consider; pick one
	var r = Math.random()
	for(x = 0; x < 4; x++){
		r -= 0.25
		if(r < 0){
			var newnote = curchord[x]
			break
		}
	}
	
	//Find n1 and n2 (respective MIDI values for old and new notes
	for(x = 0; x < scale.length; x++){
		if(scale[x] == jsarguments[1]){
			n1 = x
		}
		if(scale[x] == newnote){
			n2 = x
		}
	}
	
	//Create output list
	out = []
	var c = 0
	if(n1 == n2){ //No note change
		out = [newnote]
	}
	if(n1 < n2){
		for(x = n1; x < n2; x++){
			var randNum = Math.random();
			if(randNum < 0.2){
				out[c] = scale[x]
				c++
			}
			
		}
		out[c] = scale[x] //End on last note
	}
	if(n1 > n2){
		for(x = n1; x > n2; x--){
			var randNum = Math.random();
			if(randNum < 0.2){
				out[c] = scale[x]
				c++
			}
		}
		out[c] = scale[x] //End on last note
	}
	
	//Output stuff
	outlet(0, out); //Note sequence
	outlet(1, 1000/out.length); //Necessary note length
	jsarguments[1] = newnote
	outlet(2, jsarguments[1]); //New note (only for debugging)
	
	//Check if phrase ended
	if((newnote == 60 || newnote == 72)  && jsarguments[3] == 0 && jsarguments[4] == 0){
		//Print final note (should be 60 or 72), number of phrases remaining, current chord (should be 0)
		post(jsarguments[1])
		post(jsarguments[2] - 1)
		post(jsarguments[3])
		post("\n")
		jsarguments[2] -=1
		jsarguments[4] = 1
	}

	if(jsarguments[2] <= 0){
		post("Done\n")
		jsarguments[2] = defpnum //Reset phrase counter
		outlet(3, "bang") //Stop program
	}
}