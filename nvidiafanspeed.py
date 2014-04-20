#!/usr/bin/env python
# -*- coding: utf-8 -*-

from subprocess import *
import time
import os
import sys
import signal
import threading

"""
recommended_curve_point_array = [[10, 30],
								 [20, 35],
								 [40, 45],
								 [50, 55],
								 [60, 60],
								 [66, 70],
								 [70, 90],
								 [100, 100]]

--------------------

custom fan speed curve example:
[[temp, speed],
 [temp, speed],
 [temp, speed]]
always start at low temp/speed and head towards high temp/speed
ensure that first point is always lower temp than possible
ensure that gradient is always positive and less than infinity

--------------------

current temperature = 12

curve point = [temp, speed]
curve point 1 = [10, 5] 
curve point 2 = [20, 10]

curve point 1 temperature (10) <= current temperature (12) < curve point 2 temperature (20)

gradient = (10 - 5)/(20 - 10) = 0.5 #from point 1 to point 2, fan speed must be increased by 0.5 for every unitary increase of the temperature

difference current temperature-previously point temperature = 12 - 10 = 2

new speed = 5 + 2*0.5 = 6
"""	

class Curve():

	def __init__(self, *args, **kwargs):
		if len(args) == 1: #[[temp0, speed0], [temp1, speed1], [temp2, speed2]]
			self.cpa = list(args[0])
		if len(args) == 2: #[[temp0, temp1, temp2], [speed0, speed1, speed2]]			
			self.convertIntoMatrix(args[0], args[1])

	def convertIntoMatrix(self, x_values, y_values):
		self.cpa = list()
		x_temp = list(x_values)
		y_speed = list(y_values)
		for index in range(0, len(x_temp)):
			self.cpa.append([x_temp[index], y_speed[index]])

	def evaluate(self, x):
		point_i = 0
		while(point_i < len(self.cpa) - 1):

			if(self.cpa[point_i][0] <= x and self.cpa[point_i + 1][0] > x):
				point_1 = self.cpa[point_i]
				point_2 = self.cpa[point_i + 1]
				delta_x = point_2[0] - point_1[0]
				delta_y = point_2[1] - point_1[1]

				gradient = float(delta_y)/float(delta_x)

				x_bit = x - point_1[0]
				y_bit = int(float(x_bit) * gradient)
				y = point_1[1] + y_bit
				return y

			point_i += 1
 	 	        
	def setCurve(self, *args, **kwargs):
		if len(args) == 1:
			self.cpa = list(args[0])
		if len(args) == 2:
			self.convertIntoMatrix(args[0], args[1])
		

class StoppableThread(threading.Thread):
    """Thread class with a stop() method. The thread itself has to check
    regularly for the stopped() condition."""

    def __init__(self):
        super(StoppableThread, self).__init__()
        self._stop = threading.Event()

    def stop(self):
        self._stop.set()

    def stopped(self):
        return self._stop.isSet()

class NvidiaFanController(StoppableThread):
	"""Room here for arguments to implement multigpu fan control"""
	def __init__(self, *args, **kwargs):
		super(NvidiaFanController, self).__init__()
		signal.signal(signal.SIGINT, self.exit_signal_handler) #CTRL-C 
		signal.signal(signal.SIGQUIT, self.exit_signal_handler) #CTRL-\
		signal.signal(signal.SIGHUP, self.exit_signal_handler) #terminal closed		
		signal.signal(signal.SIGTERM, self.exit_signal_handler)
		self.curve_lock = threading.Lock()

		if len(args) == 1: #[[temp0, speed0], [temp1, speed1], [temp2, speed2]]
			self.curve = Curve(args[0])
		if len(args) == 2: #[[temp0, temp1, temp2], [speed0, speed1, speed2]]
			self.curve = Curve(args[0], args[1])

	def exit_signal_handler(self, signal, frame):
		self.stop()
	
	def stop(self):
		super(NvidiaFanController, self).stop() #StoppableThread.stop()

	def run(self):

		while(not self.stopped()):
			self.curve_lock.acquire()

			#print "Custom Fan Speed pid ", os.getpid()
			for index in range(0, len(self.curve.cpa)):
				print self.curve.cpa[index]
			
			current_temp = self.getTemp()
			new_fan_speed = self.curve.evaluate(current_temp)
			#clearScreen()
			print("CurrTemp: {0} FanSpeed: {1}".format(current_temp,new_fan_speed))
			self.setFanSpeed(new_fan_speed)

			time.sleep(1.0)

			self.curve_lock.release()
			
		self.resetFan()
		
		print "Exit"
		#finished and ready to exit
		return
	
	def resetFan(self):
		print "Reset to Auto Fan"
		process = Popen("nvidia-settings -a [gpu:0]/GPUFanControlState=0", shell=True, stdin=PIPE, stdout=PIPE)
	
	def getTemp(self):
		process = Popen("nvidia-settings -q gpucoretemp", shell=True, stdin=PIPE, stdout=PIPE)
		line_array = process.stdout.readlines()
		tmp_line = line_array[1]
		#grab number from end of line
		return int(tmp_line[-4:-2])
	
	def setFanSpeed(self, speed):
        #watch -n0 aticonfig --adapter=0 --od-gettemperature
        #that's the line to get ati fan speed
		process = Popen("nvidia-settings -a [gpu:0]/GPUFanControlState=1 -a [fan:0]/GPUCurrentFanSpeed={0}".format(speed), shell=True, stdin=PIPE, stdout=PIPE)
		return

	def setCurve(self, *args, **kwargs):
		self.curve_lock.acquire()
		print "Change Fan Speed"

		if len(args) == 1:
			self.curve.setCurve(args[0])

		if len(args) == 2:
			self.curve.setCurve(args[0], args[1])
		
		self.curve_lock.release()


if __name__ == "__main__":

	curve_point_array = [[10, 30],[20, 35],[40, 45],[50, 55],[60, 60],[66, 70],[70, 99],[100, 100]]

	x_temp = list()
	for index in range(0, len(curve_point_array)):
		x_temp.append(curve_point_array[index][0])

	y_speed = list()
	for index in range(0, len(curve_point_array)):
		y_speed.append(curve_point_array[index][1])	

	#nvidiaController = NvidiaFanController(curve_point_array)
	nvidiaController = NvidiaFanController(x_temp, y_speed)
	nvidiaController.start()

	signal.pause() #don't let the main thread terminate before the nvidia thread (otherwise the latter won't receive any signal)

	#---------------------------
	"""
	new_curve_point_array = [[10, 40],[20, 45],[40, 50],[50, 60],[60, 70],[66, 80],[70, 90],[100, 100]]

	new_x_temp = list()
	for index in range(0, len(new_curve_point_array)):
		new_x_temp.append(new_curve_point_array[index][0])

	new_y_speed = list()
	for index in range(0, len(new_curve_point_array)):
		new_y_speed.append(new_curve_point_array[index][1])	


	time.sleep(2.0)
	#nvidiaController.setCurve(new_curve_point_array)
	nvidiaController.setCurve(new_x_temp, new_y_speed)
	"""
	#---------------------------
	
