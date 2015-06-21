#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Enhanced version of the script made by Luke Frisken. It adds a frontend to the script,
with a drag and drop chart. The drag and drop code is a modified version of the
Drag n Drop Text Example from SciPy
Copyright (C) 2014  Claudio Pupparo

Script to control the fan speed of an NVidia gpu using a custom fan speed/temperature curve.
Copyright (C) 2012  Luke Frisken

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see http://www.gnu.org/licenses.
"""

from subprocess import *
import time
import os
import sys
import signal
import threading

"""
example_curve_point_array = [[10, 30],
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

	DRIVER_VERSION_CHANGE = 352.09 #from this version on, we need to use a different method to change fan speed
	DRIVER_VERSIONS_ERROR = [349.16, 349.12] #cannot control fan speed in these driver versions

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
			#for index in range(0, len(self.curve.cpa)):
			#	print self.curve.cpa[index]

			current_temp = self.getTemp()
			new_fan_speed = self.curve.evaluate(current_temp)
			#os.system("clear")
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
		drv_ver = self.getDriverVersion()

		if drv_ver >= NvidiaFanController.DRIVER_VERSION_CHANGE:
			process = Popen("nvidia-settings -a [gpu:0]/GPUFanControlState=1 -a [fan:0]/GPUTargetFanSpeed={0}".format(speed), shell=True, stdin=PIPE, stdout=PIPE)
		elif drv_ver in NvidiaFanController.DRIVER_VERSIONS_ERROR:
			print "Cannot control fan speed in version {0} of the driver".format(drv_ver)
		else:
			process = Popen("nvidia-settings -a [gpu:0]/GPUFanControlState=1 -a [fan:0]/GPUCurrentFanSpeed={0}".format(speed), shell=True, stdin=PIPE, stdout=PIPE)

	def getDriverVersion(self):
		try:
			out = check_output(["nvidia-settings", "-q", "[gpu:0]/NvidiaDriverVersion"])
			drv_ver = float(out[out.rfind(":")+1:].replace("\n", "").strip())
			return drv_ver
		except Exception:
			print "Exception in parsing Nvidia Driver Version. We'll use old attribute 'GPUCurrentFanSpeed'"
			return -1

	def setCurve(self, *args, **kwargs):
		self.curve_lock.acquire()
		print "Fan Speed Curve updated"

		if len(args) == 1:
			self.curve.setCurve(args[0])

		if len(args) == 2:
			self.curve.setCurve(args[0], args[1])

		self.curve_lock.release()


if __name__ == "__main__":
	print "Please launch nvidia-gui.py"
	"""
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
	"""
