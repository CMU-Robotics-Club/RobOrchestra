import pygame 
from pygame import midi #pip3 install python-rtmidi
import time
import mido


def main():
    mido.set_backend('mido.backends.rtmidi')
    midi.init()
    assert(midi.get_init())
    
    #Playback - either comment out block or open SimpleSynth
    otpts = mido.get_output_names()
    #assert(len(otpts) > 0)
    #outport = mido.open_output(otpts[0])
    

if __name__ == "__main__":
    main()