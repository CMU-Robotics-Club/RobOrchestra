import pygame 
from pygame import midi #pip3 install python-rtmidi
import time
import mido

def main():
    mido.set_backend('mido.backends.rtmidi')
    midi.init()
    assert(midi.get_init())
    mdata = mido.MidiFile("Cscale3.mid")
    #mdata = mido.MidiFile("auldlangsyne.mid")

    #Playback - either comment out block or open SimpleSynth
    otpts = mido.get_output_names()
    #assert(len(otpts) > 0)
    #outport = mido.open_output(otpts[0])

    lis = []
    for msg in mdata.tracks[0]: #0 for Cscale, 1 for AuldLangSyne (not sure what 0 is there)
        print(msg)
        if msg.type == 'note_on' and msg.velocity > 0:
            lis.append(msg.note)

    print(lis)
    return lis

if __name__ == "__main__":
    main()