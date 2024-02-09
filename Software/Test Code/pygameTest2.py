import pygame 
from pygame import midi #pip3 install python-rtmidi
import time
import mido

def main():
    mido.set_backend('mido.backends.rtmidi')
    midi.init()
    assert(midi.get_init())
    mdata = mido.MidiFile("auldlangsyne.mid")

    #Playback - either comment out block or open SimpleSynth
    otpts = mido.get_output_names()
    assert(len(otpts) > 0)
    outport = mido.open_output(otpts[0])

    lis = []
    for msg in mdata.tracks[1]:
        if msg.type == 'note_on':
            lis.append(msg.note)

    print(lis)
    return lis

if __name__ == "__main__":
    main()