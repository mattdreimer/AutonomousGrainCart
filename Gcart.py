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

###topInfoFrame###

#Should have GpsStatus, Radio Link status and strength (see mavproxy console),
#and Arm status of pixhawk (see mavproxy console)
#leave some space for more information to be displayed

###End of topInfo Frame####

###tractorHealthFrame###

#should have temp, oil, feul, and rpm of tractor displayed
#should watch with a callback some mavlink message
#mavlink message has not yet been implemented

###End of tracHealthFrame###


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
	if requestSpeed==0:
		rc8Val=1000
	else:
		#needs to calibrated to the tractor ie make a table of rc8values
		#for each speed ex 1mph=1200 2mph=1350 ect.. look up the values from 
		#the table or interpolate if it is between two values 
		#or more interesting is to write a script to automate the process.
		rc8Val=int(requestSpeed/8.0*1000+1000)
		if rc8Val>2000:
			rc8Val=2000
		elif rc8Val<1000:
			rc8Val=1000
	
	v.channels.overrides = {8:rc8Val}
	v.flush()
	print "sent servo 8 to ", rc8Val

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
offsetAhead=18.0
offsetLeft=9.5
def distBwPoints(lat1,lon1,lat2,lon2):
	#returns distance in meters between two points of lat and lon
	#lat and lon need to be in decimal degrees
	#going to use a,b,c triangle c is hyponteus
	#theta is the distance in km of one degree of latitude
	theta=111111.0
	a=math.fabs(((lat1-lat2)*theta))
	#~ print "a=", a
	b=math.fabs((lon1-lon2))*math.cos(math.radians(math.fabs(lat1)))*theta
	#~ print "b=",b
	c=math.sqrt(a*a+b*b)
	#~ print "c=",c
	return c

def getGpsLoc():
	#returns list of lat,lon,track,speed
	# Use the python gps package to access the laptop GPS
	try:
		gpsd = gps.gps(mode=gps.WATCH_ENABLE)
		# Once we have a valid location (see gpsd documentation) we can start moving our vehicle around
		# This is necessary to read the GPS state from the laptop
		gpsd.next()
		gotgps=True
		while gotgps:
			gpsd.next()
			if (gpsd.valid & gps.LATLON_SET) != 0:
				loc = [gpsd.fix.latitude, gpsd.fix.longitude, gpsd.fix.track,gpsd.fix.speed]
				return loc
	except socket.error:
		print "Error the GPS does not seem to be Connected \n"
	#uncomment below return statement to test program and comment out while loop above
	#~ return [49.0,-99.0,270,0]

def cartUnldLoc(distLeft,distAhead,combineLoc):
	#returns lat lon that is dist left and dist ahead of combine location.
	#if dist left or dist ahead is negative the offset will be behind
	#combineLoc is a list with 4 elements in the same form that getGpsLoc returns
	#angle between headingLeft and hyptoneus line formed by the triangle 
	#created with distLeft + distAhead
	theta=math.degrees(math.atan(float(distAhead)/float(distLeft)))
	#alpha is the angle between 0(north) and the hyptoneus line 
	#(if you drew a line between combineloc and projected point)
	alpha=-1
	if (combineLoc[2]-90+theta)<0:
		alpha=math.radians(combineLoc[2]+270+theta)
		#~ print "if statement"
	else:
		alpha=math.radians(combineLoc[2]-90+theta)
		#~ print "else statement"
	#delta lat and delta lon equals the sine and cosine of alpha multiplied 
	#by hypotenues length (h)
	h=math.sqrt(distLeft*distLeft+distAhead*distAhead)
	deltaLat=math.cos(alpha)*h
	deltaLon=math.sin(alpha)*h
	#convert delta lat and delta lon to decimal degrees add to combine
	#lat lon and return the result
	deltaLat=deltaLat/111111.0
	deltaLon=deltaLon/(math.cos(math.radians(combineLoc[0]))*111111.0)
	lat=combineLoc[0]+deltaLat
	lon=combineLoc[1]+deltaLon
	loc=[lat,lon]
	return loc

nudge=0.0
nudgeFront=0.0
def setPointForward():
	global nudgeFront
	nudgeFront=15.0
	print "Set point ahead ",nudgeFront,"(m) \n"

def turnAround():
	global nudge
	print "CART IS TURNING AROUND!"
	print "CART IS MOVING CLOSER! \n"
	setSpeed(3.0)
	nudge=0.0 #this should ensure cart always turns to the right
	setPointForward()
	
sendCartControl = threading.Event()
sendCartStatus = False

turnSet=False
forwardSet=False

def sendCart(sendCartControl):
	#~ print "sendCartThreadisStarted"
	global turnSet
	global forwardSet
	global sendCartStatus
	while True:
		#~ print "sendCartThread is Running"
		sendCartControl.wait()
		print "Started sending tractor process"
		while v.mode.name!="GUIDED":
			print "got here"
			v.mode = VehicleMode("GUIDED")
			time.sleep(1)
			print v.mode.name
		print "Tractor is in Gear \nStarting to get gps location of combine"
		combineLoc=getGpsLoc()
		print "Got Gps Location"
		loc=cartUnldLoc(offsetLeft+nudge,offsetAhead+nudgeFront,combineLoc)
		#check distance b/w cart and combine if distance is below some threshold execute turn cart around only do this once
		if turnSet==False:
			cartLoc=v.location.global_frame
			distance=distBwPoints(loc[0],loc[1],cartLoc.lat,cartLoc.lon)
			if 25.0>distance:
				print "Turning Cart Around \n"
				turnAround()
				turnSet=True
		if turnSet==True and forwardSet==False:
			cartLoc=v.location.global_frame
			distance=distBwPoints(combineLoc[0],combineLoc[1],cartLoc.lat,cartLoc.lon)
			if 21.0>distance:
				bringItClose()
				forwardSet=True
		#~ print "Distance = ", distance
		loc=cartUnldLoc(offsetLeft+nudge,offsetAhead+nudgeFront,combineLoc)
		cartGoalLoc=LocationGlobal(loc[0],loc[1],0)
		v.simple_goto(cartGoalLoc)
		#~ print "Sending Cart to ", cartLoc
		if sendCartStatus==False:
			while v.mode.name!="HOLD":
				v.mode = VehicleMode("HOLD")
				time.sleep(1)		
sendCartThread = threading.Thread(target=sendCart, args=(sendCartControl,))
sendCartThread.start()

def stop():
	setSpeed(0)
	global sendCartControl
	global sendCartStatus
	sendCartControl.clear()
	sendCartStatus=False
	startUnloadingButton.grid()
	v.mode = VehicleMode("HOLD")
	
def print_mode():
	pass
		
def startUnloading():
	global nudge
	nudge=15.0 #change this to set distance away from combine cart initially starts
	global nudgeFront
	nudgeFront=0.0
	global turnSet
	global forwardSet
	global sendCartControl
	global sendCartStatus
	sendCartStatus=True
	turnSet=False
	forwardSet=False
	print v.mode.name
	sendCartControl.set()
	startUnloadingButton.grid_remove()
	print "got there"

	
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
		
armDisarmButton=ttk.Button(buttons, 
	text="Arm", 
	command= print_mode,
	style="Default.TButton")
armDisarmButton.grid(
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
	text="Start\nUnloading", 
	command= startUnloading,
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
