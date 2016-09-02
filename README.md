RobOrchestra
=============

Welcome to RobOrchestra! We are a project in Carnegie Mellon University's Robotics Club that aims to explore the creative possibilities for robotic instruments. We design, build and program robots that read music from MIDI data in order to put on musical performances. Our goal is to create a full robotic orchestra that is able to play from arrangements from standard MIDI files, and is also able to "improvise" unique polyphonic music in real time based off of music generation algorithms developed by our team.

Meeting agendas and notes can be found on the Wiki.

###How it works.
	
The robots, all powered by Arduinos with MIDI shields, operate via a distributed network.
A laptop acts as the "conductor", transmitting MIDI signals through the network of robots. 
Each robot reads the data and picks out its own part, and then plays it accordingly. We currently use Processing to control the orchestra.


###Robots.

The orchestra is currently comprised of Xylobot, BassBot and SnareBot. We are currently in the process of adding more percussion robots as well as a larger Xylobot and a Ukulelebot.


#####The Arduino directory was moved to instruments/archives
