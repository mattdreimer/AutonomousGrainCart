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


def getGpsLoc():
    #returns list of lat,lon,track,speed
    # Use the python gps package to access the laptop GPS
    gpsd = gps.gps(mode=gps.WATCH_ENABLE)
    gotgps=True
    while gotgps:
        gpsd.next()
        if (gpsd.valid & gps.LATLON_SET) != 0:
            print "got new gps position"
            nextGpsLoc = [gpsd.fix.latitude, gpsd.fix.longitude, gpsd.fix.track, gpsd.fix.speed]
            print nextGpsLoc
            return nextGpsLoc
        else:
            print "fail"
    # except socket.error:
    #     print "Error the GPS does not seem to be Connected \n"

getGpsLoc()