#########################
# Autonomous Grain Cart #
#########################

import pygame
import gps
import socket
import time
import math
from droneapi.lib import VehicleMode, Location
import threading

pygame.init()
window = pygame.display.set_mode((1030, 1400))
pygame.display.set_caption("Grain Cart Control")
clock = pygame.time.Clock()

# Colours
white = (255, 255, 255)
red = (200, 0, 0)
yellow = (255, 255, 0)
green = (0, 255, 0)
lightblue = (0, 255, 255)
grey = (160, 160, 160)
black = (0, 0, 0)
purple = (204, 0, 204)
blue = (0, 0, 255)
greyblue = (153, 204, 255)


##Button Functions
def text_objects(text, font):
    textSurface = font.render(text, True, black)
    return textSurface, textSurface.get_rect()


def button(msg, x, y, w, h, ic, ac, action=None):
    mouse = pygame.mouse.get_pos()
    click = pygame.mouse.get_pressed()
    if x + w > mouse[0] > x and y + h > mouse[1] > y:
        pygame.draw.rect(window, ac, (x, y, w, h))
        if click[0] == 1 and action != None:
            action()
    else:
        pygame.draw.rect(window, ic, (x, y, w, h))

    smallText = pygame.font.Font("freesansbold.ttf", 30)
    textSurf, textRect = text_objects(msg, smallText)
    textRect.center = ((x + (w / 2)), (y + (h / 2)))
    window.blit(textSurf, textRect)


api = local_connect()
v = api.get_vehicles()[0]
cmds = v.commands

# offsets for cart relative to combine in meters
sendcart_event = pygame.USEREVENT + 1
# sendcartTimer still in use for guide right and for calculating distances but not for active guidance
# when unloading see use of threading in startUnloading
sendcartTimer = 750  # time in milliseconds before sending new coordinate
offsetAhead = 18.0
offsetLeft = 9.5
altitude = 30  # in meters


def setSpeed(a):
    # function for controlling rc8 hooked to speed control lever
    v.channel_override = {8: a}
    v.flush()


# ~ print "sent servo 8 to ", a
def speedReturn():
    setSpeed(0)
    print "Control Returned to Remote"


def speedSlow():
    setSpeed(1000)
    print "set speed to slow \n"


def speed2():
    setSpeed(1202)
    print "set speed to 2km/hr \n"


def speed3():
    setSpeed(1283)
    print "set speed to 3km/hr \n"


def speed4():
    setSpeed(1358)
    print "set speed to 4km/hr \n"


def speed5():
    setSpeed(1489)
    print "set speed to 5km/hr \n"


def speed6():
    setSpeed(1570)
    print "set speed to 6km/hr \n"


def speed7():
    setSpeed(1704)
    print "set speed to 7km/hr \n"


def speedMax():
    setSpeed(2000)
    print "set speed max \n"


nudge = 0.0


def moveLeft():
    global nudge
    nudge = nudge + 0.5
    print "nudge = ", nudge, "\n"


def moveRight():
    global nudge
    nudge = nudge - .5
    print "nudge = ", nudge, "\n"


nudgeFront = 0.0


def setPointForward():
    global nudgeFront
    nudgeFront = 15.0
    print "Set point ahead ", nudgeFront, "(m) \n"


def setPointForwardZero():
    global nudgeFront
    nudgeFront = 0.0
    print "Set ahead distance back to normal ", nudgeFront, "(m) \n"


def bringItClose():
    global nudge
    nudge = 0.0
    setPointForwardZero()
    print "CART IS COMING CLOSE!"
    print "CART IS COMING CLOSE!"
    print "CART IS COMING CLOSE!"
    print "nudge = ", nudge, "\n"


def turnAround():
    global nudge
    print "CART IS TURNING AROUND!"
    print "CART IS MOVING CLOSER! \n"
    speed4()
    nudge = 0.0  # this should ensure cart always turns to the right
    setPointForward()


def distBwPoints(lat1, lon1, lat2, lon2):
    # returns distance in meters between two points of lat and lon
    # lat and lon need to be in decimal degrees
    # going to use a,b,c triangle c is hyponteus
    # theta is the distance in km of one degree of latitude
    theta = 111111.0
    a = math.fabs(((lat1 - lat2) * theta))
    # ~ print "a=", a
    b = math.fabs((lon1 - lon2)) * math.cos(math.radians(math.fabs(lat1))) * theta
    # ~ print "b=",b
    c = math.sqrt(a * a + b * b)
    # ~ print "c=",c
    return c


def getGpsLoc():
    # returns list of lat,lon,track,speed
    # Use the python gps package to access the laptop GPS
    try:
        gpsd = gps.gps(mode=gps.WATCH_ENABLE)
        # Once we have a valid location (see gpsd documentation) we can start moving our vehicle around
        # This is necessary to read the GPS state from the laptop
        gpsd.next()
        gotgps = True
        while gotgps:
            gpsd.next()
            if (gpsd.valid & gps.LATLON_SET) != 0:
                loc = [gpsd.fix.latitude, gpsd.fix.longitude, gpsd.fix.track, gpsd.fix.speed]
                return loc
    except(socket.error):
        print "Error the GPS does not seem to be Connected \n"
        homeScreen()
        # uncomment below return statement to test program and comment out while loop above
        # ~ return [49.0,-99.0,270,0]


# this function was used to turn guided mode on so map could be used. It is no longer
# necassary because I have given up on the idea of using the map as it is hard and
# imprecise in a moving vehicle.
def setGuided():
    # ~ combineLoc=getGpsLoc()
    # ~ cartLoc=v.location
    # ~ print "combine location is", combineLoc
    # ~ print "cart location is",v.location
    while v.mode.name != "GUIDED":
        v.mode = VehicleMode("GUIDED")
        v.flush()
        time.sleep(1)


approach = [0, 0, 0, 0]


def setApproachLoc():
    global approach
    approach = getGpsLoc()
    print "Approach set to here"
    print "GPS coordinates are ", approach[0], " ", approach[1]
    print "ARE YOU SURE THIS IS A SAFE SPOT?????!!!!! \n"
    homeScreen()


def goToApproach():
    global approach
    setGuided()
    cartLoc = Location(approach[0], approach[1], altitude, is_relative=True)
    cmds.goto(cartLoc)
    v.flush()
    print "Sending Cart to Approach \n", cartLoc


def cartUnldLoc(distLeft, distAhead, combineLoc):
    # returns lat lon that is dist left and dist ahead of combine location.
    # if dist left or dist ahead is negative the offset will be behind
    # combineLoc is a list with 4 elements in the same form that getGpsLoc returns
    # angle between headingLeft and hyptoneus line formed by the triangle
    # created with distLeft + distAhead
    theta = math.degrees(math.atan(float(distAhead) / float(distLeft)))
    # alpha is the angle between 0(north) and the hyptoneus line
    # (if you drew a line between combineloc and projected point)
    alpha = -1
    if (combineLoc[2] - 90 + theta) < 0:
        alpha = math.radians(combineLoc[2] + 270 + theta)
        # ~ print "if statement"
    else:
        alpha = math.radians(combineLoc[2] - 90 + theta)
        # ~ print "else statement"
        # delta lat and delta lon equals the sine and cosine of alpha multiplied
        # by hypotenues length (h)
    h = math.sqrt(distLeft * distLeft + distAhead * distAhead)
    deltaLat = math.cos(alpha) * h
    deltaLon = math.sin(alpha) * h
    # convert delta lat and delta lon to decimal degrees add to combine
    # lat lon and return the result
    deltaLat = deltaLat / 111111.0
    deltaLon = deltaLon / (math.cos(math.radians(combineLoc[0])) * 111111.0)
    lat = combineLoc[0] + deltaLat
    lon = combineLoc[1] + deltaLon
    loc = [lat, lon]
    return loc


def emergencyStop():
    print "EMERGENCY STOP ACTIVATED \n"
    sendcartTimer = 0
    pygame.time.set_timer(sendcart_event, sendcartTimer)
    while v.mode.name != "HOLD":
        v.mode = VehicleMode("HOLD")
        v.flush()
        time.sleep(1)
        if v.mode.name != "HOLD":
            print "Vehicle was not stopped!"
            print "Trying Again! \n"
    print "Vehicle Stopped \n"
    speedSlow()
    homeScreen()


def controlledStop():
    # stops the cart gently
    print "Stopping Slowly \n"
    sendcartTimer = 0
    pygame.time.set_timer(sendcart_event, sendcartTimer)
    while v.mode.name != "HOLD":
        speedSlow()
        time.sleep(1)
        v.mode = VehicleMode("HOLD")
        v.flush()
        time.sleep(1)
        if v.mode.name != "HOLD":
            print "Vehicle was not stopped!"
            print "Trying Again! \n"
    print "Vehicle Stopped \n"
    homeScreen()


modeSet = False
turnSet = False
forwardSet = False
sendCartControl = False


def sendCart():
    global modeSet
    global turnSet
    global forwardSet
    global sendCartControl
    while True:
        while sendCartControl:
            combineLoc = getGpsLoc()
            loc = cartUnldLoc(offsetLeft + nudge, offsetAhead + nudgeFront, combineLoc)
            # put vehicle in guided mode and avoid doing it over and over
            if modeSet == False:
                while v.mode.name != "GUIDED":
                    v.mode = VehicleMode("GUIDED")
                    v.flush()
                    if v.mode.name == "GUIDED":
                        print "Tractor is in gear! \n"
                        modeSet = True
            if modeSet == True:
                # check distance b/w cart and combine if distance is below some threshold execute turn cart around only do this once
                if turnSet == False:
                    cartLoc = v.location
                    distance = distBwPoints(loc[0], loc[1], cartLoc.lat, cartLoc.lon)
                    if 25.0 > distance:
                        print "Turning Cart Around \n"
                        turnAround()
                        turnSet = True
                if turnSet == True and forwardSet == False:
                    cartLoc = v.location
                    distance = distBwPoints(combineLoc[0], combineLoc[1], cartLoc.lat, cartLoc.lon)
                    if 21.0 > distance:
                        bringItClose()
                        forwardSet = True
                        # ~ print "Distance = ", distance
                loc = cartUnldLoc(offsetLeft + nudge, offsetAhead + nudgeFront, combineLoc)
                cartGoalLoc = Location(loc[0], loc[1], altitude, is_relative=True)
                cmds.goto(cartGoalLoc)
                v.flush()
                # ~ print "Sending Cart to ", cartLoc


sendCartThread = threading.Thread(target=sendCart)
sendCartThread.start()


def homeScreen():
    global sendCartControl
    sendCartControl = False
    # ~ controlledStop() #cart should not move when homeScreen is displayed
    global approach
    gameloop = True
    while gameloop:
        for event in pygame.event.get():
            # ~ print event
            if (event.type == pygame.QUIT):
                pygame.quit()
                quit()
            if (event.type == pygame.MOUSEBUTTONDOWN):
                button("QUICK STOP", 20, 1150, 800, 200, red, grey, emergencyStop)
                button("Controlled Stop", 20, 20, 800, 200, yellow, grey, controlledStop)
                button("Start Unloading", 440, 720, 380, 380, green, grey, startUnloading)
                button("Guide Right", 20, 720, 380, 380, lightblue, grey, guideRight)
                if approach[0] != 0:
                    button("Go To Approach", 440, 280, 380, 380, purple, grey, goingToApproach)
                button("Approach is HERE", 20, 280, 380, 380, greyblue, grey, ApproachLoc)
                button("Remote", 830, 20, 180, 140, green, grey, speedReturn)
                button("SLOW", 830, 170, 180, 140, green, grey, speedSlow)
                button("2km/hr", 830, 320, 180, 140, green, grey, speed2)
                button("3km/hr", 830, 470, 180, 140, green, grey, speed3)
                button("4km/hr", 830, 620, 180, 140, green, grey, speed4)
                button("5km/hr", 830, 770, 180, 140, green, grey, speed5)
                button("6km/hr", 830, 920, 180, 140, green, grey, speed6)
                button("7km/hr", 830, 1070, 180, 140, green, grey, speed7)
                button("MAX", 830, 1220, 180, 140, green, grey, speedMax)

            window.fill(white)
            ##BUTTONS
            button("QUICK STOP", 20, 1150, 800, 200, red, grey)
            button("Controlled Stop", 20, 20, 800, 200, yellow, grey)
            button("Start Unloading", 440, 720, 380, 380, green, grey)
            button("Guide Right", 20, 720, 380, 380, lightblue, grey)
            if approach[0] != 0:
                button("Go To Approach", 440, 280, 380, 380, purple, grey)
            button("Approach is HERE", 20, 280, 380, 380, greyblue, grey)
            button("Remote", 830, 20, 180, 140, green, grey)
            button("SLOW", 830, 170, 180, 140, green, grey)
            button("2km/hr", 830, 320, 180, 140, green, grey)
            button("3km/hr", 830, 470, 180, 140, green, grey)
            button("4km/hr", 830, 620, 180, 140, green, grey)
            button("5km/hr", 830, 770, 180, 140, green, grey)
            button("6km/hr", 830, 920, 180, 140, green, grey)
            button("7km/hr", 830, 1070, 180, 140, green, grey)
            button("MAX", 830, 1220, 180, 140, green, grey)

        pygame.display.flip()
        clock.tick(15)


def startUnloading():
    global nudge
    nudge = 15.0  # change this to set distance away from combine cart initially starts
    global nudgeFront
    nudgeFront = 0.0
    global approach
    # starts the grain cart moving to gps coordinates for unloading
    # ~ pygame.time.set_timer(sendcart_event,sendcartTimer)
    global modeSet
    global turnSet
    global forwardSet
    global sendCartControl
    modeSet = False
    turnSet = False
    forwardSet = False
    sendCartControl = True
    control = True
    while control:
        for event in pygame.event.get():
            if (event.type == pygame.QUIT):
                pygame.quit()
                quit()
            if (event.type == pygame.MOUSEBUTTONDOWN):
                button("QUICK STOP", 20, 1150, 800, 200, red, grey, emergencyStop)
                button("Move Left", 20, 280, 380, 380, greyblue, grey, moveLeft)
                button("Move Right", 440, 280, 380, 380, greyblue, grey, moveRight)
                button("Controlled Stop", 20, 20, 800, 200, yellow, grey, controlledStop)
                button("Remote", 830, 20, 180, 140, green, grey, speedReturn)
                button("SLOW", 830, 170, 180, 140, green, grey, speedSlow)
                button("2km/hr", 830, 320, 180, 140, green, grey, speed2)
                button("3km/hr", 830, 470, 180, 140, green, grey, speed3)
                button("4km/hr", 830, 620, 180, 140, green, grey, speed4)
                button("5km/hr", 830, 770, 180, 140, green, grey, speed5)
                button("6km/hr", 830, 920, 180, 140, green, grey, speed6)
                button("7km/hr", 830, 1070, 180, 140, green, grey, speed7)
                button("MAX", 830, 1220, 180, 140, green, grey, speedMax)
                if turnSet == True:
                    button("Empty", 20, 720, 380, 380, lightblue, grey, empty)
                    if approach[0] != 0:
                        button("Go To Approach", 440, 720, 380, 380, green, grey, goToApproachFromUnload)
            window.fill(white)
            # buttons
            button("QUICK STOP", 20, 1150, 800, 200, red, grey)
            button("Controlled Stop", 20, 20, 800, 200, yellow, grey)
            button("Remote", 830, 20, 180, 140, green, grey)
            button("SLOW", 830, 170, 180, 140, green, grey)
            button("2km/hr", 830, 320, 180, 140, green, grey)
            button("3km/hr", 830, 470, 180, 140, green, grey)
            button("4km/hr", 830, 620, 180, 140, green, grey)
            button("5km/hr", 830, 770, 180, 140, green, grey)
            button("6km/hr", 830, 920, 180, 140, green, grey)
            button("7km/hr", 830, 1070, 180, 140, green, grey)
            button("MAX", 830, 1220, 180, 140, green, grey)
            button("Move Left", 20, 280, 380, 380, greyblue, grey)
            button("Move Right", 440, 280, 380, 380, greyblue, grey)
            if turnSet == True:
                button("Empty", 20, 720, 380, 380, lightblue, grey)
                if approach[0] != 0:
                    button("Go To Approach", 440, 720, 380, 380, green, grey)
        pygame.display.flip()
        clock.tick(15)


def ApproachLoc():
    global sendCartControl
    sendCartControl = False
    control = True
    while control:
        for event in pygame.event.get():
            if (event.type == pygame.QUIT):
                pygame.quit()
                quit()
            if (event.type == pygame.MOUSEBUTTONDOWN):
                button("QUICK STOP", 20, 1150, 800, 200, red, grey, emergencyStop)
                button("Set Here", 20, 280, 380, 380, greyblue, greyblue, setApproachLoc)
                button("Cancel", 440, 280, 380, 380, greyblue, red, homeScreen)
                button("Controlled Stop", 20, 20, 800, 200, yellow, grey, controlledStop)
                button("Remote", 830, 20, 180, 140, green, grey, speedReturn)
                button("SLOW", 830, 170, 180, 140, green, grey, speedSlow)
                # button("Auto",830,320,180,140,green,grey,auto)
                button("3km/hr", 830, 470, 180, 140, green, grey, speed3)
                button("4km/hr", 830, 620, 180, 140, green, grey, speed4)
                button("5km/hr", 830, 770, 180, 140, green, grey, speed5)
                button("6km/hr", 830, 920, 180, 140, green, grey, speed6)
                button("7km/hr", 830, 1070, 180, 140, green, grey, speed7)
                button("MAX", 830, 1220, 180, 140, green, grey, speedMax)
            window.fill(white)
            # buttons
            button("QUICK STOP", 20, 1150, 800, 200, red, grey)
            button("Controlled Stop", 20, 20, 800, 200, yellow, grey)
            button("Remote", 830, 20, 180, 140, green, grey)
            button("SLOW", 830, 170, 180, 140, green, grey)
            # button("Auto",830,320,180,140,red,grey)
            button("3km/hr", 830, 470, 180, 140, green, grey)
            button("4km/hr", 830, 620, 180, 140, green, grey)
            button("5km/hr", 830, 770, 180, 140, green, grey)
            button("6km/hr", 830, 920, 180, 140, green, grey)
            button("7km/hr", 830, 1070, 180, 140, green, grey)
            button("MAX", 830, 1220, 180, 140, green, grey)
            button("Set Here", 20, 280, 380, 380, greyblue, grey)
            button("Cancel", 440, 280, 380, 380, red, grey)
        pygame.display.flip()
        clock.tick(30)


def goingToApproach():
    global sendCartControl
    sendCartControl = False
    global approach
    pygame.time.set_timer(sendcart_event, sendcartTimer)
    control = True
    while control:
        for event in pygame.event.get():
            if (event.type == pygame.QUIT):
                pygame.quit()
                quit()
            if (event.type == sendcart_event):
                cartLoc = v.location
                distToApproach = distBwPoints(approach[0], approach[1], cartLoc.lat, cartLoc.lon)
                print "Distance to approach is ", distToApproach, "m \n"
                if 30 > distToApproach:
                    speed4()
                if 10 > distToApproach:
                    print "Approach is being reached, stopping now! \n"
                    controlledStop()
            if (event.type == pygame.MOUSEBUTTONDOWN):
                button("QUICK STOP", 20, 1150, 800, 200, red, grey, emergencyStop)
                button("Go", 20, 280, 380, 380, greyblue, greyblue, goToApproach)
                button("Cancel", 440, 280, 380, 380, greyblue, red, homeScreen)
                button("Controlled Stop", 20, 20, 800, 200, yellow, grey, controlledStop)
                button("Remote", 830, 20, 180, 140, green, grey, speedReturn)
                button("SLOW", 830, 170, 180, 140, green, grey, speedSlow)
                # button("Auto",830,320,180,140,green,grey,auto)
                button("3km/hr", 830, 470, 180, 140, green, grey, speed3)
                button("4km/hr", 830, 620, 180, 140, green, grey, speed4)
                button("5km/hr", 830, 770, 180, 140, green, grey, speed5)
                button("6km/hr", 830, 920, 180, 140, green, grey, speed6)
                button("7km/hr", 830, 1070, 180, 140, green, grey, speed7)
                button("MAX", 830, 1220, 180, 140, green, grey, speedMax)
            window.fill(white)
            # buttons
            button("QUICK STOP", 20, 1150, 800, 200, red, grey)
            button("Controlled Stop", 20, 20, 800, 200, yellow, grey)
            button("Remote", 830, 20, 180, 140, green, grey)
            button("SLOW", 830, 170, 180, 140, green, grey)
            # button("Auto",830,320,180,140,red,grey)
            button("3km/hr", 830, 470, 180, 140, green, grey)
            button("4km/hr", 830, 620, 180, 140, green, grey)
            button("5km/hr", 830, 770, 180, 140, green, grey)
            button("6km/hr", 830, 920, 180, 140, green, grey)
            button("7km/hr", 830, 1070, 180, 140, green, grey)
            button("MAX", 830, 1220, 180, 140, green, grey)
            button("Go", 20, 280, 380, 380, green, grey)
            button("Cancel", 440, 280, 380, 380, red, grey)
        pygame.display.flip()
        clock.tick(30)


def goToApproachFromUnload():
    goToApproach()
    goingToApproach()


def empty():
    global sendCartControl
    sendCartControl = False
    # this is based off combine position so you push empty button when done
    # unloading and the cart turns around.
    pygame.time.set_timer(sendcart_event, sendcartTimer)
    combineLoc = getGpsLoc()
    loc = cartUnldLoc(20, -25, combineLoc)
    cartGoalLoc = Location(loc[0], loc[1], altitude, is_relative=True)
    cmds.goto(cartGoalLoc)
    v.flush()
    control = True
    while control:
        for event in pygame.event.get():
            if (event.type == pygame.QUIT):
                pygame.quit()
                quit()
            if (event.type == sendcart_event):
                cartLoc = v.location
                distToReady = distBwPoints(loc[0], loc[1], cartLoc.lat, cartLoc.lon)
                print "Distance to Ready location is ", distToReady, "m \n"
                if 30 > distToReady:
                    speed4()
                if 10 > distToReady:
                    print "Ready location is being reached, stopping now! \n"
                    controlledStop()
            if (event.type == pygame.MOUSEBUTTONDOWN):
                button("QUICK STOP", 20, 1150, 800, 200, red, grey, emergencyStop)
                # ~ button("Go",20,280,380,380,greyblue,greyblue,goToApproach)
                # ~ button("Cancel",440,280,380,380,greyblue,red,homeScreen)
                button("Controlled Stop", 20, 20, 800, 200, yellow, grey, controlledStop)
                button("Remote", 830, 20, 180, 140, green, grey, speedReturn)
                button("SLOW", 830, 170, 180, 140, green, grey, speedSlow)
                # button("Auto",830,320,180,140,green,grey,auto)
                button("3km/hr", 830, 470, 180, 140, green, grey, speed3)
                button("4km/hr", 830, 620, 180, 140, green, grey, speed4)
                button("5km/hr", 830, 770, 180, 140, green, grey, speed5)
                button("6km/hr", 830, 920, 180, 140, green, grey, speed6)
                button("7km/hr", 830, 1070, 180, 140, green, grey, speed7)
                button("MAX", 830, 1220, 180, 140, green, grey, speedMax)
            window.fill(white)
            # buttons
            button("QUICK STOP", 20, 1150, 800, 200, red, grey)
            button("Controlled Stop", 20, 20, 800, 200, yellow, grey)
            button("Remote", 830, 20, 180, 140, green, grey)
            button("SLOW", 830, 170, 180, 140, green, grey)
            # button("Auto",830,320,180,140,red,grey)
            button("3km/hr", 830, 470, 180, 140, green, grey)
            button("4km/hr", 830, 620, 180, 140, green, grey)
            button("5km/hr", 830, 770, 180, 140, green, grey)
            button("6km/hr", 830, 920, 180, 140, green, grey)
            button("7km/hr", 830, 1070, 180, 140, green, grey)
            button("MAX", 830, 1220, 180, 140, green, grey)
            # ~ button("Go",20,280,380,380,green,grey)
            # ~ button("Cancel",440,280,380,380,red,grey)
        pygame.display.flip()
        clock.tick(30)


def guideRight():
    global nudge
    nudge = 39.0  # change this to set distance away from combine cart initially starts
    global nudgeFront
    # negative number is unsatisfying solution to get cart on left. I reverse combine
    # heading as well below.
    nudgeFront = -40.0
    global approach
    # starts the grain cart moving to gps coordinates for unloading
    pygame.time.set_timer(sendcart_event, sendcartTimer)
    modeSet = False
    turnSet = False
    forwardSet = False
    control = True
    while control:
        for event in pygame.event.get():
            if (event.type == pygame.QUIT):
                pygame.quit()
                quit()
            if (event.type == sendcart_event):
                combineLoc = getGpsLoc()
                # Reversing heading here
                combineLoc[2] = combineLoc[2] + 180.0
                loc = cartUnldLoc(offsetLeft + nudge, offsetAhead + nudgeFront, combineLoc)
                # put vehicle in guided mode and avoid doing it over and over
                if modeSet == False:
                    while v.mode.name != "GUIDED":
                        v.mode = VehicleMode("GUIDED")
                        v.flush()
                        if v.mode.name == "GUIDED":
                            print "Tractor is in gear! \n"
                            modeSet = True
                if modeSet == True:
                    cartLoc = v.location
                    loc = cartUnldLoc(offsetLeft + nudge, offsetAhead + nudgeFront, combineLoc)
                    cartGoalLoc = Location(loc[0], loc[1], altitude, is_relative=True)
                    cmds.goto(cartGoalLoc)
                    v.flush()
                    # ~ print "Sending Cart to ", cartLoc
            if (event.type == pygame.MOUSEBUTTONDOWN):
                button("QUICK STOP", 20, 1150, 800, 200, red, grey, emergencyStop)
                button("Move Left", 20, 280, 380, 380, greyblue, grey, moveLeft)
                button("Move Right", 440, 280, 380, 380, greyblue, grey, moveRight)
                button("Controlled Stop", 20, 20, 800, 200, yellow, grey, controlledStop)
                button("Remote", 830, 20, 180, 140, green, grey, speedReturn)
                button("SLOW", 830, 170, 180, 140, green, grey, speedSlow)
                button("2km/hr", 830, 320, 180, 140, green, grey, speed2)
                button("3km/hr", 830, 470, 180, 140, green, grey, speed3)
                button("4km/hr", 830, 620, 180, 140, green, grey, speed4)
                button("5km/hr", 830, 770, 180, 140, green, grey, speed5)
                button("6km/hr", 830, 920, 180, 140, green, grey, speed6)
                button("7km/hr", 830, 1070, 180, 140, green, grey, speed7)
                button("MAX", 830, 1220, 180, 140, green, grey, speedMax)
                if approach[0] != 0:
                    button("Go To Approach", 440, 720, 380, 380, green, grey, goToApproachFromUnload)
            window.fill(white)
            # buttons
            button("QUICK STOP", 20, 1150, 800, 200, red, grey)
            button("Controlled Stop", 20, 20, 800, 200, yellow, grey)
            button("Remote", 830, 20, 180, 140, green, grey)
            button("SLOW", 830, 170, 180, 140, green, grey)
            button("2km/hr", 830, 320, 180, 140, green, grey)
            button("3km/hr", 830, 470, 180, 140, green, grey)
            button("4km/hr", 830, 620, 180, 140, green, grey)
            button("5km/hr", 830, 770, 180, 140, green, grey)
            button("6km/hr", 830, 920, 180, 140, green, grey)
            button("7km/hr", 830, 1070, 180, 140, green, grey)
            button("MAX", 830, 1220, 180, 140, green, grey)
            button("Move Left", 20, 280, 380, 380, greyblue, grey)
            button("Move Right", 440, 280, 380, 380, greyblue, grey)
            if approach[0] != 0:
                button("Go To Approach", 440, 720, 380, 380, green, grey)
        pygame.display.flip()
        clock.tick(30)


homeScreen()
