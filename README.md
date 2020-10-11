RobOrchestra
=============

Welcome to RobOrchestra! RobOrchestra is an ongoing project in the Carnegie Mellon Robotics Club that aims to explore the creative possibilities for robotic instruments. We design, build and program robots that read music from MIDI data in order to put on musical performances. Our goal is to create a full robotic orchestra that is able to play from arrangements from standard MIDI files, and is also able to "improvise" unique polyphonic music in real time based off of music generation algorithms developed by our team.

Check out this demo video: https://drive.google.com/open?id=1UAF38HtQlL7tU6Xmdl4eHLXhHpyFQM5X

#### Team Meetings: Sundays, 1:20-2:20pm EST for Hardware and Sundays, 2:30-3:30pm EST for Software, both on Zoom. Contact Sam (RobOrchestra Leader) at sir@andrew.cmu.edu for more information, or Steven Wu (RobOrchestra Software Lead) at stevenwu@andrew.cmu.edu, or Sharon Liu (RobOrchestra Harware Lead) at sharonli@andrew.cmu.edu.
#### Check out our Wiki for meeting agendas and tutorials

### How it works.
	
The robots, all powered by Arduinos with MIDI shields, operate via a distributed network. A laptop acts as the "conductor", transmitting MIDI siginals through the network of robots. Each robot reads the data and picks out its own part, and then plays it accordingly. We use Processing, a powerful music programming language, to control the orchestra, however it should work with nearly any MIDI software.


### Robots.

The orchestra is currently comprised of TomBot SnareBot and XyloBot. Currently in progress are UkuleleBot, RoboOboe, and RoboBagpipes.


##### The Arduino directory was moved to instruments/archives
