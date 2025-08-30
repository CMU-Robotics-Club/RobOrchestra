RobOrchestra
=============

Welcome to RobOrchestra! RobOrchestra is an ongoing project in the Carnegie Mellon Robotics Club that aims to explore the creative possibilities for robotic instruments. We design, build and program robots that read music from MIDI data in order to put on musical performances. Our goal is to create a full robotic orchestra that is able to play from arrangements from standard MIDI files, and is also able to "improvise" unique polyphonic music in real time based off of music generation algorithms developed by our team.

Check out this demo video: https://drive.google.com/open?id=1UAF38HtQlL7tU6Xmdl4eHLXhHpyFQM5X

### How it works.
	
The robots, all powered by Arduinos with MIDI shields, operate via a distributed network. A laptop acts as the "conductor", transmitting MIDI siginals through the network of robots. Each robot reads the data and picks out its own part, and then plays it accordingly. We use Processing, a powerful music programming language, to control the orchestra, however it should work with nearly any MIDI software.

