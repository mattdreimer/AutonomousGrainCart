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

#Use this line for connecting with 3dr radio
v = connect("/dev/ttyUSB0", baud=57600 , wait_ready=True)
#use this line for connecting to simulation
#~ v = connect("127.0.0.1:14550", wait_ready=False)
print "Connected to Tractor \nReady to Go!!!"

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
def gps_callback(self, attr_name, value):
	if value.fix_type==3:
		gpsLabel.configure(foreground="green")
	else:
		gpsLabel.configure(foreground="red")
	gpsStatus.set("%dDGPS Sats: %d" %(value.fix_type, value.satellites_visible))
v.add_attribute_listener("gps_0", gps_callback)
	
gpsStatus = StringVar()
gpsLabel = ttk.Label(topInfo, textvariable=gpsStatus, anchor="center", font=("",12,""))
gpsLabel.grid(column=0, row=0, sticky=(N,E,S,W))

@v.on_message("RADIO")
def listener(self, name, message):
	if message.rssi < message.noise+10 or message.remrssi < message.remnoise+10:
		radioLabel.configure(foreground="red")
	else:
		radioLabel.configure(foreground="black")
	radioStatus.set('Radio %u/%u %u/%u' % (message.rssi, message.noise, message.remrssi, message.remnoise))

radioStatus = StringVar()
radioLabel = ttk.Label(topInfo, textvariable=radioStatus, anchor="center", font=("",12,""))
radioLabel.grid(column=0, row=1, sticky=(N,E,S,W))

@v.on_message("NAV_CONTROLLER_OUTPUT")
def listener(self, name, message):
    wpDist.set("Distance to waypoint: %s(m)" %(message.wp_dist))
    
wpDist = StringVar()
wpDistLabel = ttk.Label(topInfo, textvariable=wpDist, anchor="center", font=("",12,""))
wpDistLabel.grid(column=1, row=0, sticky=(N,E,S,W))

for x in range(4):
	topInfo.columnconfigure(x, weight=1)
for x in range(2):
	topInfo.rowconfigure(x, weight=1)
###End of topInfo Frame####

###tractorHealthFrame###
@v.on_message("TRACTOR_HEALTH")
def listener(self, name, message):
    #print 'Tractor Health %d %d %d %d %d' % (message.rpm_D4, message.rpm_D5, 
    #   message.coolan_temp_D1, message.oil_pres_D4, message.fuel_level_D2)
    rpm = (message.rpm_D4 + (256*message.rpm_D5))/8 ##rpm
    coolant_temp = message.coolan_temp_D1-40 ##celsius
    oil_pressure = message.oil_pres_D4*4/6.89476 ##psi
    fuel_level = message.fuel_level_D2*0.4 ## percent
    
    rpmText.set(str(rpm))
    coolantText.set(str(int(coolant_temp))+" C")
    oilText.set(str(int(oil_pressure))+" PSI")
    fuelPercent.set(int(fuel_level))

    if fuel_level<25:
        fuelLabel.configure(style="FuelR.Vertical.TProgressbar")
    else:
       fuelLabel.configure(style="FuelG.Vertical.TProgressbar")    
    
    if coolant_temp<=70:
        coolantLabel.configure(foreground="blue")
    elif coolant_temp>=95:
        coolantLabel.configure(foreground="red")
    elif 70<coolant_temp<95:
        coolantLabel.configure(foreground="green")
    else:
        coolantLabel.configure(foreground="black")

    if 25<oil_pressure<50:
        oilLabel.configure(foreground="green")
    else:
        oilLabel.configure(foreground="red")
    	
rpmText = StringVar()
rpmLabel = ttk.Label(tracHealth, textvariable=rpmText, anchor="center", 
	font=("",18,""))
rpmLabel.grid(column=0, row=1, rowspan=3, sticky=(N,E,S,W))

coolantText = StringVar()
coolantLabel = ttk.Label(tracHealth, textvariable=coolantText, anchor="center", 
	font=("",18,""))
coolantLabel.grid(column=1, row=1, rowspan=3, sticky=(N,E,S,W))

oilText = StringVar()
oilLabel = ttk.Label(tracHealth, textvariable=oilText, anchor="center", 
	font=("",18,""))
oilLabel.grid(column=2, row=1, rowspan=3, sticky=(N,E,S,W))

fuelStyle = ttk.Style()
fuelStyle.configure("FuelG.Vertical.TProgressbar", 
	background="green")
fuelStyle.configure("FuelR.Vertical.TProgressbar", 
	background="red")

fuelPercent = IntVar()
fuelLabel = ttk.Progressbar(tracHealth, orient=VERTICAL, variable=fuelPercent)
fuelLabel.grid(column=3, row=1, rowspan=4, sticky=(N,E,S,W))

ttk.Label(tracHealth, text="Fuel", anchor="center", 
	font=("",20,"")).grid(column=3, row=0)

ttk.Label(tracHealth, text="Coolant\nCelsius", anchor="center", 
    justify="center", font=("",20,"")).grid(column=1, row=0)

ttk.Label(tracHealth, text="Engine\nRPM", anchor="center", justify="center",
    font=("",20,"")).grid(column=0, row=0)

ttk.Label(tracHealth, text="Oil PSI\nPressure", anchor="center", 
    justify="center", font=("",20,"")).grid(column=2, row=0)

for x in range(3):
	tracHealth.columnconfigure(x, weight=10)
tracHealth.columnconfigure(3, weight=1)
tracHealth.columnconfigure(4, weight=1)
for x in range(5):
	tracHealth.rowconfigure(x, weight=1)
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

###SpeedSelFrame####
def setTargetSpeed(scaleVal):
	#Updates target speed as slider is moved
	targetSpeed.set((str(round(float(scaleVal), 1)), "MPH"))

def setSpeed(requestSpeed):
	#Function for changing speed. requestSpeed is a number (0-whatever
	#the top speed is set for) default is 8mph
	#speedDict is a dictionary that can be obtained by running CalibrateSpeed.py
	speedDict={0:1000, 1: 1100, 2: 1200, 3: 1500, 4: 1600, 5: 1700, 6: 1800, 7: 1900, 8: 2000}
	speedScaleVal.set(requestSpeed)
	setTargetSpeed(requestSpeed)
	
	if requestSpeed in speedDict:
		rc8Val=speedDict[requestSpeed]
	else:
		#map rc8 value if request speed is between two whole numbers
		lowerVal= math.floor(requestSpeed)
		upperVal= math.ceil(requestSpeed)
		spread=speedDict[upperVal]-speedDict[lowerVal]
		rc8Val=int((requestSpeed-lowerVal)*spread+speedDict[lowerVal])
	
	v.channels.overrides["8"] = rc8Val

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
	
nextGpsLoc = []
def getGpsLoc():
	#returns list of lat,lon,track,speed
	# Use the python gps package to access the laptop GPS
	global nextGpsLoc
	try:
		gpsd = gps.gps(mode=gps.WATCH_ENABLE)
		# Once we have a valid location (see gpsd documentation) we can start moving our vehicle around
		# This is necessary to read the GPS state from the laptop
		gotgps=True
		while gotgps:
			gpsd.next()
			if (gpsd.valid & gps.LATLON_SET) != 0:
				nextGpsLoc = [gpsd.fix.latitude, gpsd.fix.longitude, gpsd.fix.track,gpsd.fix.speed]
				print "got new gps position"
	except socket.error:
		print "Error the GPS does not seem to be Connected \n"
	#uncomment below return statement to test program and comment out while loop above
	#~ return [49.0,-99.0,270,0]
gpsThread = threading.Thread(target=getGpsLoc)
gpsThread.start()	


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
	global nextGpsLoc
	combineLoc=[]
	while True:
		#~ print "sendCartThread is Running"
		sendCartControl.wait()
		#~ print "Started sending tractor process"
		while v.mode.name!="GUIDED":
			v.mode = VehicleMode("GUIDED")
			time.sleep(1)
			print v.mode.name
		#~ print "Tractor is in Gear \nStarting to get gps location of combine"
		if combineLoc!=nextGpsLoc:
			combineLoc=nextGpsLoc
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
			print "Sending Cart to ", cartLoc
		if sendCartStatus==False:
			while v.mode.name!="HOLD":
				v.mode = VehicleMode("HOLD")
				time.sleep(1)		
sendCartThread = threading.Thread(target=sendCart, 
	args=(sendCartControl,))
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
	
approach=[0,0,0,0]

def setApproach():
	global approach
	global nextGpsLoc
	if nextGpsLoc!=[]:
		approach = nextGpsLoc
		print "Approach set to here"
		print "GPS coordinates are ", approach[0], " ", approach[1]
		print "ARE YOU SURE THIS IS A SAFE SPOT?????!!!!! \n"
	else:
		print "GPS is not Working"
	
def arm():
	v.channels.overrides["4"] = 2000
	armButton.grid_remove()
	DisarmButton.grid()
	
def disarm():
	v.channels.overrides["4"] = 1000
	DisarmButton.grid_remove()
	armButton.grid()	
		
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
buttonStyle.map("Arm.Default.TButton",
	background=[("active", "green")])
buttonStyle.configure("Arm.Default.TButton",
	background="green")
buttonStyle.map("Disarm.Default.TButton",
	background=[("active", "red")])
buttonStyle.configure("Disarm.Default.TButton",
	background="red")
buttonStyle.map("Approach.Default.TButton",
	background=[("active", "purple")])
buttonStyle.configure("Approach.Default.TButton",
	background="purple")	
		
armButton=ttk.Button(buttons, 
	text="Arm\nTractor", 
	command= arm,
	style="Arm.Default.TButton")
armButton.grid(
	column=1, 
	row=0, 
	sticky=(N,E,S,W))	

DisarmButton=ttk.Button(buttons, 
	text="Disarm\nTractor", 
	command= disarm,
	style="Disarm.Default.TButton")
DisarmButton.grid(
	column=1, 
	row=0, 
	sticky=(N,E,S,W))
DisarmButton.grid_remove()


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

approachHereButton=ttk.Button(buttons, 
	text="Approach\nIs Here", 
	command= setApproach,
	style="Approach.Default.TButton")
approachHereButton.grid(
	column=0, 
	row=0, 
	sticky=(N,E,S,W))

###End of Buttons
root.mainloop()
