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

import pygtk
pygtk.require('2.0')
import gtk
import matplotlib.pyplot as plt
from matplotlib.widgets import Button
import math
import signal
import nvidiafanspeed as nvfanspeed

"""
SETUP:
In order to get this program to work, my xorg.conf was generated
and saved using the x server display configuration tab in nvidia-settings.
These lines:

	Section "Device"
		Identifier     "Device0"
		Driver         "nvidia"
		VendorName     "NVIDIA Corporation"
		BoardName      "GeForce GTX 570"
	EndSection

in /etc/X11/xorg.conf
were then edited to look like this:

	Section "Device"
		Identifier     "Device0"
		Driver         "nvidia"
		VendorName     "NVIDIA Corporation"
		BoardName      "GeForce GTX 570"
		Option "Coolbits" "4"
	EndSection

then the computer is restarted.

ensure that when finished, the box in nvidia-settings for the manual fan control is unticked!!!!!
"""

#TODO
#dipendenze da librerie

class Data(object):
	def __init__(self, xdata, ydata):
		self.xdata = list(xdata)
		self.ydata = list(ydata)

	def getData(self):
		xdata = list(self.xdata)
		ydata = list(self.ydata)
		return xdata, ydata

	def setData(self, xdata, ydata):
		self.xdata = list(xdata)
		self.ydata = list(ydata)

class DataController(object):
	def __init__(self, xdata, ydata):
		self.data = Data(xdata, ydata)

	def getData(self):
		return list(self.data.getData())

	def setData(self, xdata, ydata):
		if self.validate(xdata, ydata) == True:
			self.data.setData(xdata, ydata)
			return True
		else:
			return False

	#Check temp and speed monotonic and greater than zero, check speed inside [30, 100], temp inside [0,120] ecc ecc
	def validate(self, xdata, ydata):
		first = [0,30]
		last = [110,100]

		if xdata[0] != first[0]:
			print "ERROR: First point temperature must be ", first[0]
			return False
		if ydata[0] < first[1]:
			print "ERROR: First point speed lower than ", first[1]
			return False

		if xdata[len(xdata) - 1] < last[0]:
			print "ERROR: Last point temperature must be ", last[0]
			return False
		if ydata[len(ydata) - 1] != last[1]:
			print "ERROR: Last point speed must be ", last[1]
			return False

		for index in range(1, len(xdata)):
			if xdata[index] <= xdata[index - 1] or ydata[index] <= ydata[index - 1]:
				print "ERROR: Curve not increasing!"
				return False

		return True

class Chart(object):
	def __init__(self, plt):
		self.DEBUG = False
		self.plot = plt
		self.fig = plt.figure(num="Nvidia Fan Speed Controller") #create a figure (one figure per window)		
		axes = self.fig.add_subplot(111) #add a subplot to the figure. axes is of type Axes which contains most of the figure elements
		#working on the Axes object
		axes.set_title("Fan Speed Curve")
		axes.set_xlabel("Temperature")
		axes.set_ylabel("Fan Speed")
		axes.grid()

		self.x_min = -5
		self.x_max = 115
		self.y_min = 25
		self.y_max = 105

		axes.set_xlim(self.x_min, self.x_max)
		axes.set_ylim(self.y_min, self.y_max)

		printAxes = self.fig.add_axes([0.7, 0.025, 0.1, 0.04])  #position rect [left, bottom, width, height] where all quantities are in fractions of figure width and height 
		self.printButton = Button(printAxes, "Print")	
		self.printButton.on_clicked(self.printData)

		applyAxes = self.fig.add_axes([0.8, 0.025, 0.1, 0.04])
		self.applyAxes = Button(applyAxes, "Apply")
		self.applyAxes.on_clicked(self.applyData)
		
		#better to move outside the object
		x_values = [0,  10, 20, 40, 50, 60, 65, 70, 80, 100, 110] #temp
		y_values = [30,  35, 40, 45, 55, 60, 70, 75, 85, 95, 100] #speed

		#b=blue, o=circle, picker=max distance for considering point as clicked
		self.line, = axes.plot(x_values, y_values, linestyle='-', marker='o', color='b', picker=5) #tuple unpacking: this function returns a tuple, with the comma we take the first element

		self.dragHandler = DragHandler(self)
		self.dataController = DataController(x_values, y_values)
		#self.fileController load data from file
		#validate points from file!		
		if not self.DEBUG:
			self.nvidiaController = nvfanspeed.NvidiaFanController(x_values, y_values)
			self.nvidiaController.start()

		signal.signal(signal.SIGINT, self.exit_signal_handler) #CTRL-C 
		signal.signal(signal.SIGQUIT, self.exit_signal_handler) #CTRL-\
		signal.signal(signal.SIGHUP, self.exit_signal_handler) #terminal closed		
		signal.signal(signal.SIGTERM, self.exit_signal_handler)

		self.fig.canvas.mpl_connect("close_event", self.on_close)

	def on_close(self, event):
		if not self.DEBUG:
			self.nvidiaController.stop()

	def exit_signal_handler(self, signal, frame):
		self.close()

	def close(self):
		self.plot.close('all')
		if not self.DEBUG:
			self.nvidiaController.stop()

	def show(self):
		self.plot.show() #display ALL non closed figures
		#pyplot is stateful: usually self.plot.function() works on the current plot in the current figure

	def printData(self, event):
		xdata, ydata = self.dataController.getData()
		print "---------------"
		for index in range(0, len(xdata)):
			print xdata[index], ydata[index]
		print "---------------"

	def applyData(self, event):
		xdata = self.line.get_xdata()
		ydata = self.line.get_ydata()
		ret = self.dataController.setData(xdata, ydata)
		
		if ret:
			if not self.DEBUG:
				self.nvidiaController.setCurve(xdata, ydata)			
		else:
			xdata, ydata = self.dataController.getData()
			xydata = [xdata, ydata]
			self.line.set_data(xydata)

class DragHandler(object):
	def __init__(self, chartObj):		
		self.dragged = None
		self.chartObj = chartObj
		self.chartObj.fig.canvas.mpl_connect("pick_event", self.on_pick_event)
		self.chartObj.fig.canvas.mpl_connect("button_release_event", self.on_release_event)

	def on_pick_event(self, event):
		self.dragged = event.artist #Line2D
		self.pick_pos = (event.mouseevent.xdata, event.mouseevent.ydata)
		self.ind = event.ind

		if self.ind[0] == 0:
			print "ERROR: cannot modify first point"
			self.dragged = None
		elif self.ind[0] == len(self.dragged.get_xdata()) - 1:
			print "ERROR: cannot modify last point"
			self.dragged = None

		#print "self.ind: ", self.ind
		#xdata = self.dragged.get_xdata()
		#ydata = self.dragged.get_ydata()
		#print 'onpick points:', xdata[self.ind], ydata[self.ind]

	def on_release_event(self, event):
		if self.dragged is not None:
			xdata = self.dragged.get_xdata() #no need to copy the list, since it is used only by the line2D object
			ydata = self.dragged.get_ydata()
			index = self.ind #if two or more points are too closed, this tuple contains more than one point. we take the first
			chartObj = self.chartObj
			if event.xdata <= chartObj.x_min or event.xdata >= chartObj.x_max or event.ydata <= chartObj.y_min or event.ydata >= chartObj.y_max:
				print "ERROR: cannot move point [",index[0],"] out of chart"
				return

			xdata[index[0]] = int(xdata[index[0]] + event.xdata - self.pick_pos[0]) #truncate towards zero
			ydata[index[0]] = int(ydata[index[0]] + event.ydata - self.pick_pos[1])
			#print 'new point:', xdata[index], ydata[index]

			xydata = [xdata, ydata]
			self.dragged.set_data(xydata)			
			self.dragged = None
			self.chartObj.fig.canvas.draw()

if __name__ == "__main__": 

	chart = Chart(plt)
	chart.show()