Nvidia-Dynamic-Fan-Control
==========================

Python script for dynamic control of the fan speed of a Nvidia Card
Based on the work of Luke Frisken:
https://code.google.com/p/nvidia-fanspeed/

Fan speed changes depending on the temperature of the card
A modifiable 2D curve of [temp, speed] points is used to control the fan

Works only with proprietary drivers
No SLI support (only single GPU configuration)
It must be used with an open terminal

Tested on version 331.20 and 337.12 Beta of the driver

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
  
HOW TO START
Open a terminal in the folder containing both nvidia-gui.py and nvidiafanspeed.py then:
  python nvidia-gui.py
  
