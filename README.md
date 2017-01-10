RobOrchestra
=============

Welcome to RobOrchestra! RobOrchestra is an ongoing project in the Carnegie Mellon Robotics Club that aims to explore the creative possibilities for robotic instruments. We design, build and program robots that read music from MIDI data in order to put on musical performances. Our goal is to create a full robotic orchestra that is able to play from arrangements from standard MIDI files, and is also able to "improvise" unique polyphonic music in real time based off of music generation algorithms developed by our team.

####Team Meetings Mondays, 4:30pm in RoboClub. Contact sadkins@andrew.cmu.edu for more information

###How it works.
	
The robots, all powered by Arduinos with MIDI shields, operate via a distributed network. A laptop acts as the "conductor", transmitting MIDI siginals through the network of robots. Each robot reads the data and picks out its own part, and then plays it accordingly. We use Processing, a powerful music programming language, to control the orchestra, however it should work with nearly any MIDI software.


###Robots.

The orchestra is currently comprised of BassBot, tomBot SnareBot and xyloBot. Currently in progress are ukuleleBot and xyloBot's larger cousin, glockenspielBot


#####The Arduino directory was moved to instruments/archives
