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

Last driver version tested: 352.21  
On 349.12 and 349.16 versions there is a regression that makes impossibile to control fan speed

DEPENDENCIES  
* python  
* matplotlib  

HOW TO INSTALL  
* Install python  
  &nbsp;&nbsp;sudo apt-get install python #on debian based distros
* Install matplotlib  
  &nbsp;&nbsp;sudo apt-get install python-matplotlib #on debian based distros
* Add the following line in section "Device" of /etc/X11/xorg.conf  
  &nbsp;&nbsp;Option         "Coolbits" "4"
  
HOW TO START  
Open a terminal in the folder containing both nvidia-gui.py and nvidiafanspeed.py then execute:  
  python nvidia-gui.py
  
