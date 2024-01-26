import pygame
from pygame import midi
import time

def main():
    pygame.midi.init()
    assert(pygame.midi.get_init())
    print('test')

    nDevices = midi.get_count()
    print(nDevices)
    for devnum in range(nDevices):
        print(midi.get_device_info(devnum))

    myBus = midi.Output(0)
    compBus = myBus#midi.Output(0)

    for p in range(60, 73):
        myBus.note_on(p, velocity=100, channel=0)
        myBus.note_on(p+7, velocity=100, channel=0)

        time.sleep(0.5)
        myBus.note_off(p, velocity=100, channel=0)
        myBus.note_off(p+7, velocity=100, channel=0)
    #pygame.midi.quit() #Is a thing, but supposedly calls when the code stops anyway; don't bother

# this is the main entry point of this script
if __name__ == "__main__":
    main()