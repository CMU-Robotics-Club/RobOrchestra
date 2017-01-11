import pygame
import pygame.midi
import time

pygame.midi.init()

print pygame.midi.get_default_output_id()
print pygame.midi.get_device_info(0)

player = pygame.midi.Output(2)
player.set_instrument(0)

print 'Playing...'

while(True):
    player.note_on(64, velocity=64, channel=1)
    print 'note on'
    time.sleep(1)
    print 'note off'
    player.note_off(64, velocity=64, channel=1)
    time.sleep(1)