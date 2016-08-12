RobOrchestra
=============

Welcome to RobOrchestra! We are a project in Carnegie Mellon University's Robotics Club 
dedicated to making robots that can play a wide range of instruments usually reserved
for human performance.

Info for team members can be found on the wiki.

###How it works.
	
The robots, all powered by Arduinos with MIDI shields, operate via a distributed network.
A laptop acts as the "conductor", transmitting MIDI signals through the network of robots. 
Each robot reads the data and picks out its own part, and then plays it accordingly. We use 
Max 7, a powerful music programming language, to control the orchestra, however it should
work with nearly any MIDI software.


###Robots.

The orchestra is currently comprised of BassBot and SnareBot, our percussion section,
and xylobot, our, well, more of our percussion section. We are in the process of building 
glockenspielbot, xylobot's bigger brother, and ukulele bot.


#####The Arduino directory was moved to instruments/archives
