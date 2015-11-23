
##################### Note Object #####################
# Note.note returns the alphabetical name of the note
# Note.octave returns the octave of the note
# Note.deg returns the degree of the note
# Note.solfege returns the solfege name of the note
#######################################################

class Note(object):
    NOTES = ['C','C#','D','D#','E','F','F#','G','G#','A','A#','B']
    SOLFEGE = ['Do','Re','Mi','Fa','So','La','Ti']
    INTERVALS = [0,2,4,5,7,9,11]

    def __init__(self, midi_val):
        self.midi_val = midi_val

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
    next_chord = [None]*4

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

prev_chord = [None, None, None, Note(60)]
chord = 7

print(voice_next_chord(prev_chord,chord))
