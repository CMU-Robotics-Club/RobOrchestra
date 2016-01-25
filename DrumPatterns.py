import time

#Utility function to see if a list has anything close to an input
#Args: x: value to be checked; myList: list to be checked; res: acceptable tolerance
def fuzzyContains(x, myList, res):
    for n in myList:
        if(abs(n-x) < res):
            return 1
    return 0

#beat: beat in measure
#res: Amount of subdivision
def getCountSyllable(beat, res):
    if(res == 2):
        if(beat == 1):
            return "+"
    if(res == 3):
        if(beat == 1):
            return "trip"
        if(beat == 2):
            return "let"
    if(res == 4):
        if(beat == 1):
            return "e"
        if(beat == 2):
            return "+"
        if(beat == 3):
            return "a"
    return beat

#Function to print MIDI values for percussion in a rhythm
#Arguments: nbeats: number of beats per measure
#bpm: Number of beats per minute
#nmeasures: Number of measures to be played
#resolution: Amount of subdivision (2 for 8th notes, 4 for 16ths, etc.)
#snarebeats: List of beats on which the snare should play
#bassbeats: List of beats on which the bass drum should play

def playDrum(nbeats, bpm, nmeasures, resolution, snarebeats, bassbeats):
    for w in range(0, nmeasures):
        print("")
        print("Measure " + str(w+1))
        for x in range(0, nbeats*resolution):
            time.sleep(60.0 /bpm/resolution)

            if(x % resolution == 0):
                print("Bt " + str(x/resolution + 1))
            else:
                print(getCountSyllable(x % resolution + 1, resolution))
            
            if(fuzzyContains(1.0*x/resolution + 1, snarebeats, 0.01)):
                print("Snare: MIDI 36")
            if(fuzzyContains(1.0*x/resolution + 1, bassbeats, 0.01)):
                print("Bass drum: MIDI 38")

print("Starting code")
playDrum(4, 180, 3, 5, [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5], [4])
