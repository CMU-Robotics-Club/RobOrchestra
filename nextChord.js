inlets = 1;
outlets = 1;

var probabilityMatrix = [[0.20, 0.10, 0.30, 0.10, 0.05, 0.20, 0.05],
						 [0.00, 0.05, 0.00, 0.40, 0.50, 0.00, 0.05],
						 [0.20, 0.20, 0.10, 0.15, 0.30, 0.00, 0.05],
						 [0.50, 0.00, 0.00, 0.10, 0.20, 0.15, 0.05],
						 [0.85, 0.00, 0.00, 0.00, 0.05, 0.15, 0.00],
						 [0.10, 0.10, 0.20, 0.40, 0.10, 0.05, 0.05],
						 [0.95, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]];
						

function msg_int(currentChord) {
	
	var randomNum = Math.random();
	
	for(var i = 0; i < probabilityMatrix[currentChord].length; i++) {
		if(randomNum < probabilityMatrix[currentChord][i]) {
			post(i);
			outlet(0,i);
			break;
		}
		
		else {
			randomNum = randomNum - probabilityMatrix[currentChord][i];
		}
	}
	
}
	