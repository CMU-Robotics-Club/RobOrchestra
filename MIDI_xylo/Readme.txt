Readme.txt
@author: Audrey Yeoh (ayeoh)

This readme is for RobOrchestra Xylobot. 

The program is the alpha version of the working MIDI file for xylobot. It will talk about the details
of the program and its support files. 

Sending MIDI
I have only found 1 way of sending MIDI files to the arduino so far. I was unable to find any
software that was able to send MIDI out to arduino using windows, so I used Garageband on mac and
installed the plugin MidiO. 
To make MIDI sent do the following steps in order:
- Set MIDI shield to PGM state (switch on board)
- Upload MIDI_xylo.ino file to arduino (choose the right board and com port)
- Plug in MIDI->USB cable as follows:
    - MIDI out cable goes into MIDI in on shield
    - MIDI out USB into computer
- Go to garage band and choose the track that should be played. (obviously choose a song first) 
- Select the appropriate channel. Xylobot is default to channel 1. (Can change in MIDI.begin(channel))
    - Note when argument left empty defaults to channel 1
    - Choose channel by:
        - Double click on left sidebar until right sidebar comes up. 
        - Click the edit tab under the instrument image
        - In the sound generator option, choose MidiO
        - Click on the MidiO image
        - Choose the right channel
        - Choose the right port destination (port 1 tends to be good)
- Now the arduino should be able to receive mesages from MIDI

Testing/ Playing MIDI files on xylobot
We can test in multiple ways. Note that the MIDI shield uses the TX and RX pins to send the MIDI
files to the arduino so there is no more serial port available. This program was debugged with 
the onboard LED on the arduino.
Play music on xylobot as follows:
- Set the MIDI shield to RUN mode. (switch on board)
- Power the solenoids with 12V (power leads should be sticking out of xylobot)
- Make sure the arduino is connected to the computer (mac)
- Play song by playing song on garageband. It will automatically send the MIDI file as it is being
played

Cautions and Reminders
- Remember to plug in the MIDI cables the right way, otherwise it won't play
- Remember to switch the MIDI shield to RUN mode when running the program and PGM mode when 
programming the arduino. This is because they take the same line and intefere with each other 
otherwise and won't work right. 
- Solenoids NEED to be initialized as OUTPUTs and starting as LOW in the setup loop, otherwise
they will all be raised and draw a ton of current

KNOWN BUGS & TO DOS
- 2 keys on the robot are currently dead. Currently it's C# and D. This is because their solenoid 
circuit is burnt. Transistors probably burnt out.
- Currently the notes are lagging by 1. It's sad, will try to fix.
- Talked to Dannenberg and he says we need to find out when the note goes off because if a note on,
note on then note off, note off is seen, that means 2 notes are playing at the same time
- Find out what the velocity component is suppose to do cause it is not part of the code 
- make an initializer instead of initializing everything in the program. 
