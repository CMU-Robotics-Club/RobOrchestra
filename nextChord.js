inlets = 1;
outlets = 5;

//Probability Matrix
//Row is current chord, column is next chord

                          //I   no    ii    no    no    IV    no    V     no    vi    no    viid
var probabilityMatrix = [[0.20, 0.00, 0.10, 0.00, 0.00, 0.30, 0.00, 0.15, 0.00, 0.20, 0.00, 0.05], //I
						 [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], //no
						 [0.00, 0.00, 0.05, 0.00, 0.00, 0.00, 0.00, 0.90, 0.00, 0.00, 0.00, 0.05], //ii
						 [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], //no
						 [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], //iii but no
						 [0.20, 0.00, 0.20, 0.00, 0.00, 0.10, 0.00, 0.45, 0.00, 0.00, 0.00, 0.05], //IV
						 [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], //no
						 [0.50, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.20, 0.00, 0.15, 0.00, 0.15], //V
						 [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], //no
						 [0.10, 0.00, 0.10, 0.00, 0.00, 0.20, 0.00, 0.50, 0.00, 0.05, 0.00, 0.05], //vi
						 [0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00], //no
						 [0.95, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00, 0.05]];//vii(dim)
						
//calculates and outputs next chord to be played
//value is the number of half steps the next chord is from tonic
function msg_int(currentChord) {
	
	var randomNum = Math.random();
	var sum = 0;
	
	for(var i = 0; i < probabilityMatrix[currentChord].length; i++) {
		sum += probabilityMatrix[currentChord][i];
		
		if(randomNum < sum) {
			var base = i+60 //root
			
			outlet(0,i); //Keeps track of chord in array
			
			outlet(1,base); //outputs root
			
			//major chords
			if(i == 0 || i == 5 || i == 7) {
				outlet(2,base+4); //outputs 3rd
				outlet(3,base+7); //outputs 5th
			}
			
			//minor chords
			else if(i == 2 || i == 9) {
				outlet(2,base+3);
				outlet(3,base+7);
			}
			
			//dimished chords
			else {
				outlet(2,base+3);
				outlet(3,base+6);
			}
			
			outlet(4,base+12); //outputs root octave
			break;
		}
	
	}
	
}
	