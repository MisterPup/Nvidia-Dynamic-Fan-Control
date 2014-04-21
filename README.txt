Nvidia-Dynamic-Fan-Control
==========================

Python script for dynamic control of the fan speed of a Nvidia Card.
Based on the work of Luke Frisken:
https://code.google.com/p/nvidia-fanspeed/

It adds a frontend to the original (modified) script and fixes some bugs
The fan speed is controlled with a 2D curve of [temp, speed] points.

Works only with proprietary drivers.
No SLI support (only single GPU configuration)

Curve points validation has been added, but it must be tested, so please be careful before applying any changes to the curve!

Tested on 331.20 and 337.12 Beta

DEPENDENCIES
  matplotlib

HOW TO INSTALL
Install matplotlib
  On Debian based distros:
    sudo apt-get install python-matplotlib
Modify xorg.conf
  add line
    Option         "Coolbits" "4"
  to section "Device" in file /etc/X11/xorg.conf
  
