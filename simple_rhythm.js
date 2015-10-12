inlets = 1;
outlets = 1;

function bang() {
	
	rand_num = Math.random();
	
	post(rand_num);
	
	if(rand_num < 0.33) {
		outlet(0,175);
	}
	else if(rand_num < 0.66) {
		outlet(0,350);
	}
	else {
		outlet(0,700);
	}
	
}