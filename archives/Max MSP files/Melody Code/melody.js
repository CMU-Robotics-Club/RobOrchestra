inlets = 1
outlets = 3

var test = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76]
var scale = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76]
var out = []

function msg_int(newnote){
	post("Test");
	//Inputs in MIDI
	//Old note is jsarguments[1]
	//New note is newnote
	
	var n1 = 0
	var n2 = 0
	
	//Find n1 and n2
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
			post(randNum);
			if(randNum < 0.5){
				out[c] = scale[x]
				c++
			}
			
		}
		out[c] = scale[x] //End on last note
	}
	if(n1 > n2){
		for(x = n1; x > n2; x--){
			if(Math.random() < 0.5){
				out[c] = scale[x]
				c++
			}
			else{
				post("Omitted")
			}
		}
		out[c] = scale[x] //End on last note
	}
	
	//Output stuff
	outlet(0, out); //Note sequence
	outlet(1, 1000/out.length); //Necessary note length
	outlet(2, jsarguments[1]); //Old note (only for debugging)
	jsarguments[1] = newnote
}