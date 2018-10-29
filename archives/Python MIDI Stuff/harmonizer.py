
##################### Note Object #####################
# Note.note returns the alphabetical name of the note
# Note.octave returns the octave of the note
# Note.deg returns the degree of the note
# Note.solfege returns the solfege name of the note
#######################################################

#The above seems to be a note about Note. Hmm...

#Apparently pygame.midi is a thing to look into

#Bad progressions:
    #Parallel fifths
    #Parallel octaves
        #if we don't count the bass line for this, this should never come up, since there's no octave in 1, 3, 5
        #if we count the bass, we have to be careful with implementation
        #so I assume we aren't counting the bass for now
    #Anything else I'm missing

#Planned implementation:
    #Pass in a list of stuff that doesn't work (6 possible cases, determined by S and A lines)
        #so we could even pass in a length 6 boolean array (3 by 2 might be cleaner), or, if we feel really clever, a number between 0 and 63
    #Create an order for S (best to worst)
    #Try best. If only one valid alto note, use it. If no valid alto note, pick the next soprano note
    #If this creates a bad condition, add this to the set of bad conditions and rerun the function
    #If you're good, run the next chord
    #If you run out of soprano notes, throw an error and backtrack

class Note(object):
    NOTES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    SOLFEGE = ['Do','Re','Mi','Fa','So','La','Ti']
    INTERVALS = [0,2,4,5,7,9,11]

    def __init__(self, midi_val, rescale = 1):
        self.midi_val = midi_val

        if(rescale):
            self.rescale()

        self.octave = self.midi_val//12
        self.note_val = self.midi_val%12
        self.note = Note.NOTES[self.note_val]
        if(self.note_val == 0):
            self.deg = 1
        elif(self.note_val == 2):
            self.deg = 2
        elif(self.note_val == 4):
            self.deg = 3
        elif(self.note_val == 5):
            self.deg = 4
        elif(self.note_val == 7):
            self.deg = 5
        elif(self.note_val == 9):
            self.deg = 6
        elif(self.note_val == 11):
            self.deg = 7
        else:
            self.deg = None
        if(self.deg == None):
            self.solfege = None
        else:
            self.solfege = Note.SOLFEGE[self.deg-1]

    def __sub__(self, other):
        # defaults to giving unsigned interval, not difference
        return abs(self.midi_val - other.midi_val)

    def __repr__(self):
        return self.note + str(self.octave)

    def __eq__(self, other):
        return self.midi_val == other.midi_val

    def rescale(self):
        if(self.midi_val < 0):
            self.midi_val += 12
        elif(self.midi_val > 127):
            self.midi_val -= 12

# prev_chord is an array of notes (SATB)
# chord is an integer between I and VII (1 and 7)
def voice_next_chord(prev_chord, chord):
    next_chord = next_other(prev_chord, chord)

    # bass
    next_chord[3] = next_bass(prev_chord, chord)

    return next_chord

def next_bass(prev_chord, chord):
    b1 = Note(prev_chord[3].octave*12 + Note.INTERVALS[chord-1])
    b2 = Note(prev_chord[3].octave*12 + 12 + Note.INTERVALS[chord-1])
    b3 = Note(prev_chord[3].octave*12 - 12 + Note.INTERVALS[chord-1])
    pb = prev_chord[3]

    i1,i2,i3 = b1 - pb,b2 - pb,b3 - pb
    if(i1 <= i2 and i1 <= i3):
        return b1
    elif(i2 <= i1 and i2 <= i3):
        return b2
    elif(i3 <= i1 and i3 <= i2):
        return b3

def get_best(n1, n2, n3, n):
    i1, i2, i3 = n1-n, n2-n, n3-n
    if(i1 <= i2 and i1 <= i3):
        return n1
    elif(i2 <= i1 and i2 <= i3):
        return n2
    elif(i3 <= i1 and i3 <= i2):
        return n3

def next_other(prev_chord, chord):
    pc = [prev_chord[0], prev_chord[1], prev_chord[2], prev_chord[3]] #Copy pvev_chord
    #I'm going to be changing this later; hopefully I don't overwrite anything useful
    nc = [None, None, None, None]
    dmsdone = [0, 0, 0] #Tracks which do/mi/so notes were used
    for x in range(0, 3): #Loop through soprano, alto, tenor
        dms = [None, None, None] #Do mi so (best notes); not degree minute second
        for y in range(0, 3): #Loop through do, mi, so
            if(dmsdone[y] == 1):
                dms[y] = Note(1000000, 0)
                continue
            #We're going to loop through do, mi, so, and get the optimal octave for each, then get the optimal note from that
            n1 = Note(pc[x].octave*12 + Note.INTERVALS[(chord+2*y-1)%7])
            n2 = Note(pc[x].octave*12 + 12 + Note.INTERVALS[(chord+2*y-1)%7])
            n3 = Note(pc[x].octave*12 - 12 + Note.INTERVALS[(chord+2*y-1)%7])
            n = pc[x]
            dms[y] = get_best(n1, n2, n3, n)
        #I should theoretically now have the best do, mi, so notes (or 1000000 if impossible
        gb = get_best(dms[0], dms[1], dms[2], pc[x]) #Apparently, this line sometimes passes in None
        for y in range(0, 3):
            if(gb == dms[y]):
                dmsdone[y] = 1
                nc[x] = gb
    return nc
    #And... this should theoretically work.
                
        
#This is the code that actually runs
prev_chord = [Note(72), Note(67), Note(64), Note(60)] #60, 64, 67, 72 is a 1 chord
chord = 7

print(prev_chord)
print(voice_next_chord(prev_chord,chord))
