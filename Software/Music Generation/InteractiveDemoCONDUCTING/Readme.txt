Early version of an interactive demo

Playable notes, and percussion frequency set via sliders

Each beat, pick a random note, check if it should be played, and if so, play it.

This version estimates beat length via computer vision. It's designed to run alongside the Arduino code in the Conducting folder, which uses a Pixy camera to look for motion, interprets those as beats, then does a running average to estimate tempo.