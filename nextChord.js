inlets = 1;
outlets = 1;

/*var probabilityMatrix = [[0.20, 0.10, 0.30, 0.10, 0.05, 0.20, 0.05]]
						[[0.00, 0.05, 0.00, 0.40, 0.50, 0.00, 0.05]]
						[[0.20, 0.20, 0.10, 0.15, 0.30, 0.00, 0.05]]
						[[0.50, 0.00, 0.00, 0.10, 0.20, 0.15, 0.05]]
						[[0.85, 0.00, 0.00, 0.00, 0.05, 0.15, 0.00]]
						[[0.10, 0.10, 0.20, 0.40, 0.10, 0.05, 0.05]]
						[[0.95, 0.00, 0.00, 0.00, 0.00, 0.00, 0.00]];
						
var curChord = 0;

function bang() {
	outlet(0,curChord);
}

function msg_int(currentChord) {
	
	var randomNum = Math.random();
	
	for(int i = 0; i < probabilityMatrix[currentChord].length; i++) {
		if(randomNum < probabilityMatrix[currentChord][i]) {
			curChord = i;
			outlet(0,i);
			break;
		}
	}
	
	bang();
} */
	


var myval=0;

if (jsarguments.length>1)
	myval = jsarguments[1];

function bang()
{
	outlet(0,"myvalue","is",myval);
}

function msg_int(v)
{
	post("received int " + v + "\n");
	myval = v;
	bang();
}

function msg_float(v)
{
	post("received float " + v + "\n");
	myval = v;
	bang();
}

function list()
{
	var a = arrayfromargs(arguments);
	post("received list " + a + "\n");
	myval = a;
	bang();
}

function anything()
{
	var a = arrayfromargs(messagename, arguments);
	post("received message " + a + "\n");
	myval = a;
	bang();
}
	