Nvidia-Dynamic-Fan-Control
==========================

Python script for dynamic controlling the fan speed of a Nvidia Card.
Based on the work of Luke Frisken:
https://code.google.com/p/nvidia-fanspeed/

The gui is made with matplotlib.
The fan speed is controlled with a 2D curve of [temp, speed] points.

Currently there is no check for the points inserted, so please be careful before applying any change to the curve!
