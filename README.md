Nvidia-Dynamic-Fan-Control
==========================

Python script for dynamic controlling the fan speed of a Nvidia Card.
Based on the work of Luke Frisken:
https://code.google.com/p/nvidia-fanspeed/

It works only with proprietary drivers.
The fan speed is controlled with a 2D curve of [temp, speed] points.

Curve points validation has been added, but it must be tested, so please be careful before applying any changes to the curve!

Tested on 331.20

DEPENDENCIES:
  matplotlib

HOW TO INSTALL
Install matplotlib
  On Debian based distros:
    sudo apt-get install python-matplotlib
Modify xorg.conf
  Before driver 337.12 Beta
    add line
      Option         "Coolbits" "4"
    to section "Device" in file /etc/X11/xorg.conf
  After driver 337.12 Beta
    add line
      Option         "Coolbits" "12"
    to section "Device" in file /etc/X11/xorg.conf
    
