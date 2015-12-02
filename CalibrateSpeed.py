#Run this file to obtain a dictionary for calibrating the speed in Gcart.py
#After you follow the instructions on the screen and stop the tractor 
#you will need to copy paste the dictionary into setSpeed function
#setSpeed can be found at approx line 100 in Gcart.py

from Tkinter import *
import ttk
from ttk import *
import sys
import Tkinter
from dronekit import connect, VehicleMode, LocationGlobal
import time
import threading
import gps
import socket
import math


root = Tk()
root.title("GcartLayout")
root.attributes('-zoomed', True)

# Create the frames for layout
frameTuple=("terminal", "topInfo", "tracHealth", "buttons", "lowerInfo", "speedSel")
for x in frameTuple:
	globals()[x] = ttk.Frame(root, relief="groove", padding="3")
	globals()[x].grid_propagate(False)
	globals()[x].grid(sticky=(N,E,S,W))
	
# Place the frames in root
terminal.grid(column=6, columnspan= 4, row=2, rowspan=4)
topInfo.grid(column=0, columnspan= 6, row=0)
tracHealth.grid(column=6, columnspan= 4, row=0, rowspan=2)
buttons.grid(column=0, columnspan= 6, row=1, rowspan=4)
lowerInfo.grid(column=0, columnspan= 6, row=5)
speedSel.grid(column=0, columnspan= 10, row=7)

# Configure relative size of frames by changing column weights of root
for x in range(10):
	root.columnconfigure(x, weight=10)
for x in (1,2,3,4,7):
	root.rowconfigure(x, weight=10)
root.rowconfigure(0, weight=5)
root.rowconfigure(5, weight=6)
#~ root.rowconfigure(6, weight=2)

###Terminal Frame###	
text = Tkinter.Text(terminal)
text.grid(column=0, row=0, sticky=(N,E,S,W))
terminal.columnconfigure(0, weight=1)
terminal.rowconfigure(0, weight=1)

class Std_redirector(object):
	def __init__(self,widget):
		self.widget = widget
		
	def write(self,string):
		self.widget.insert(Tkinter.END,string)
		self.widget.see(Tkinter.END)
			
sys.stdout = Std_redirector(text)
###End of Terminal Frame###

#Use this line for connecting with 3dr radio
v = connect("/dev/ttyUSB0", baud=57600 , wait_ready=True)
#use this line for connecting to simulation
#~ v = connect("127.0.0.1:14550", wait_ready=True)
print "Connected to Tractor \nReady to Go!!!"

###Tractor Health frame###
#Still need to set up labels with callbacks for temp, oil, fuel, and rpm
ttk.Label(tracHealth, text="Tractor Health", anchor="center", font=("",24,"")).grid(column=0, row=0, columnspan=4)
for x in range(4):
	tracHealth.columnconfigure(x, weight=1)
for x in range(2):
	tracHealth.rowconfigure(x, weight=1)
###End of Tractor Health frame###

###SpeedSelFrame####
def setTargetSpeed(scaleVal):
	#Updates target speed as slider is moved
	targetSpeed.set((str(round(float(scaleVal), 1)), "MPH"))

def setSpeed(requestSpeed):
	#Function for changing speed. requestSpeed is a number (0-whatever
	#the top speed is set for) default is 8mph
	speedScaleVal.set(requestSpeed)
	setTargetSpeed(requestSpeed)
	global rc8Val
	if requestSpeed==0:
		rc8Val=1000
	else:
		rc8Val=int(requestSpeed/8.0*1000+1000)
		if rc8Val>2000:
			rc8Val=2000
		elif rc8Val<1000:
			rc8Val=1000
	
	v.channels.overrides = {8:rc8Val}

def setSpeedonRelease(instanceVar):
	setSpeed(speedScaleVal.get())
		
speedStyle = ttk.Style()
speedStyle.configure("Speed.Horizontal.TScale", 
	sliderthickness="full", 
	sliderlength=150, 
	background="orange")	
speedStyle.map("Speed.Horizontal.TScale",
	background=[("pressed", "orange"),
				("active", "orange")])
					
speedScaleVal = DoubleVar()
speedScale = ttk.Scale(speedSel, 
	orient=HORIZONTAL, 
	from_=0.0, 
	to=8.0, 
	variable= speedScaleVal, 
	style="Speed.Horizontal.TScale", 
	command=setTargetSpeed)
speedScale.bind("<ButtonRelease-1>", setSpeedonRelease)
speedScale.grid(column=0, row=0, sticky=(N,E,S,W))
speedSel.columnconfigure(0, weight=1)
speedSel.rowconfigure(0, weight=1)

ttk.Label(root, 
	text="Speed Control", 
	anchor="center",
	font=("",18,"")
	).grid(column=0, 
		columnspan=10, 
		row=6, 
		sticky=(S,E,W))

ttk.Label(root, 
	text="Slow", 
	anchor="center",
	font=("",18,"")
	).grid(column=0, 
		row=6, 
		sticky=(S,E,W))
		
ttk.Label(root, 
	text="Fast", 
	anchor="center",
	font=("",18,"")
	).grid(column=9, 
		row=6, 
		sticky=(S,E,W))
###End of SpeedSelFrame####


###Start of lowerInfoFrame###
###In Gear watcher###
def mode_callback(self, attr_name, value):
	if str(value) == "VehicleMode:HOLD":
		inGearLabel.configure(background="green")
		inGearStatus.set("Tractor is Parked")
	else:
		inGearLabel.configure(background="red")
		inGearStatus.set("Tractor is in Gear")
			
v.add_attribute_listener("mode", mode_callback)

inGearStatus = StringVar()
inGearLabel = ttk.Label(lowerInfo, textvariable=inGearStatus, anchor="center",font=("",24,""))
inGearLabel.grid(column=0, row=0, sticky=(N,E,S,W))

mode_callback(v,"mode",v.mode)

for x in range(3):
	lowerInfo.columnconfigure(x, weight=1)
lowerInfo.rowconfigure(0, weight=1)
###End of in Gear watcher###

###Speed watcher###
def speed_callback(self, attr_name, value):
	speedStatus.set((round(value*2.23694, 1), 'MPH'))
			
v.add_attribute_listener("groundspeed", speed_callback)

speedStatus = StringVar()
speedLabel = ttk.Label(lowerInfo, textvariable=speedStatus, anchor="center",font=("",24,""))
ttk.Label(lowerInfo, text="GPS Speed", anchor="center",font=("",24,"")).grid(column=1, row=0, sticky=(N,E,W))
speedLabel.grid(column=1, row=0, sticky=(S,E,W))
###End of Speed watcher###

###Target Speed Display###
targetSpeed = StringVar()
targetSpeedLabel = ttk.Label(lowerInfo, 
	textvariable=targetSpeed, 
	anchor="center",
	font=("",24,""))
ttk.Label(lowerInfo, 
	text="Target Speed", 
	anchor="center",
	font=("",24,"")).grid(
	column=2, 
	row=0, 
	sticky=(N,E,W))
targetSpeedLabel.grid(column=2, row=0, sticky=(S,E,W))
###End of Target Speed Display###
###End of lowerInfoFrame####=


###Start of Buttons###

speedCalibrationControl = threading.Event()
startLogging = threading.Event()
sendCartStatus = False

def speedCalibration(speedCalibrationControl):
	#~ print "sendCartThreadisStarted"
	global sendCartStatus
	global rc8Val
	count=0
	while True:
		#~ print "sendCartThread is Running"
		speedCalibrationControl.wait()
		count=count+1
		if count==1:
			print "Started Calibration process"
		else:
			print "Calibration done push stop button"
		while v.mode.name!="GUIDED":
			print "got here"
			v.mode = VehicleMode("GUIDED")
			time.sleep(1)
			print v.mode.name
		print "Tractor is in Gear"
		if count==1:
			speedDict={0:1000}
			for x in range(1,9):
				print "Please adjust speed until tractor is going ", x," mph"
				print "Please push log button and wait for more instructions"
				startLogging.wait()
				speedDict[x] = rc8Val
				print speedDict
				startLogging.clear()

		time.sleep(1)
			 
		if sendCartStatus==False:
			print "copy paste the following into blank file"
			print speedDict
			while v.mode.name!="HOLD":
				v.mode = VehicleMode("HOLD")
				time.sleep(1)
						
speedCalibrationThread = threading.Thread(target=speedCalibration, args=(speedCalibrationControl,))
speedCalibrationThread.start()

def stop():
	setSpeed(0)
	global speedCalibrationControl
	global sendCartStatus
	speedCalibrationControl.clear()
	sendCartStatus=False
	v.mode = VehicleMode("HOLD")
	
def log():
	global startLogging
	startLogging.set()

def print_mode():
	pass
			
def startCalibration():
	global speedCalibrationControl
	global sendCartStatus
	sendCartStatus=True
	print v.mode.name
	speedCalibrationControl.set()

	
for x in range(3):
	buttons.columnconfigure(x, weight=1)
for x in range(2):
	buttons.rowconfigure(x, weight=1)
	
buttonStyle = ttk.Style()
buttonStyle.configure("Default.TButton",
	font=("",24,""),
	anchor="center",
	justify="center")
buttonStyle.map("Stop.Default.TButton",
	background=[("active", "orange")])
buttonStyle.configure("Stop.Default.TButton",
	background="orange")
buttonStyle.map("StartUnloading.Default.TButton",
	background=[("active", "green")])
buttonStyle.configure("StartUnloading.Default.TButton",
	background="green")	
		
logButton=ttk.Button(buttons, 
	text="Log", 
	command= log,
	style="Default.TButton")
logButton.grid(
	column=1, 
	row=0, 
	sticky=(N,E,S,W))	

stopButton=ttk.Button(buttons, 
	text="Stop", 
	command= stop,
	style="Stop.Default.TButton")
stopButton.grid(
	column=1, 
	row=1, 
	sticky=(N,E,S,W))

startUnloadingButton=ttk.Button(buttons, 
	text="Start\nCalibration", 
	command= startCalibration,
	style="StartUnloading.Default.TButton")
startUnloadingButton.grid(
	column=0, 
	row=1, 
	sticky=(N,E,S,W))
	
guideRightButton=ttk.Button(buttons, 
	text="Guide Right", 
	command= print_mode,
	style="Default.TButton")
guideRightButton.grid(
	column=2, 
	row=1, 
	sticky=(N,E,S,W))

###End of Buttons
root.mainloop()
