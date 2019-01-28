import time

#Utility function to see if a list has anything close to an input
#Args: x: value to be checked; myList: list to be checked; res: acceptable tolerance
def fuzzyContains(x, myList, res):
    for n in myList:
        if(abs(n-x) < res):
            return 1
    return 0

#count: count in measure
#res: Amount of subdivision
def getCountSyllable(count, res):
    if(res == 2):
        if(count == 2):
            return "+"
    if(res == 3):
        if(count == 1):
            return "trip"
        if(count == 3):
            return "let"
    if(res == 4):
        if(count == 2):
            return "e"
        if(count == 3):
            return "+"
        if(count == 4):
            return "a"
    return count

#Function to print MIDI values for percussion in a rhythm
#Arguments: ncounts: number of counts per measure
#bpm: Number of counts per minute
#nmeasures: Number of measures to be played
#resolution: Amount of subdivision (2 for 8th notes, 4 for 16ths, etc.)
#snarecounts: List of counts on which the snare should play
#basscounts: List of counts on which the bass drum should play

def playDrum(ncounts, bpm, nmeasures, resolution, snarecounts, basscounts):
    for w in range(0, nmeasures):
        print("")
        print("Measure " + str(w+1))
        for x in range(0, ncounts*resolution):
            time.sleep(60.0 /bpm/resolution)

            if(x % resolution == 0):
                print("Bt " + str(x/resolution + 1))
            else:
                print(getCountSyllable(x % resolution + 1, resolution))
            
            if(fuzzyContains(1.0*x/resolution + 1, snarecounts, 0.01)):
                print("Snare: MIDI 36")
            if(fuzzyContains(1.0*x/resolution + 1, basscounts, 0.01)):
                print("Bass drum: MIDI 38")

print("Starting code")
#Arguments: Time signature, tempo, nmeasures, subdivision, snare, bass
playDrum(3, 180, 3, 4, [1, 1.5, 2, 2.5, 3, 3.5, 4, 4.5], [4])
