AutonomousGrainCart
===================
*Software for interacting with an autonomous tractor that has been setup with [Pixhawk](https://pixhawk.org) hardware.*

Run this code as a module in mavproxy, see the following links for more info.

[Dronecode Modules](http://dronecode.github.io/MAVProxy/html/modules/index.html)

Below is the link for the DroneKit-Python version 2 migration guide. This script currently uses version 1.

[Drone API Migration Guide](http://python.dronekit.io/guide/migrating.html)

# Installation instruction for OSX

Install GPSd

`brew install gpsd`

Install the necessary dependencies for Pygame

`brew install mercurial python sdl sdl_image sdl_mixer sdl_ttf smpeg portmidi`

`pip install hg+http://bitbucket.org/pygame/pygame`

Install MAVProxy

`brew tap homebrew/science`

`brew install wxmac wxpython opencv`

`pip install numpy pyparsing MAVProxy`

Install DroneKit 1.5.0

`pip install -I https://github.com/dronekit/dronekit-python/archive/v1.5.0.tar.gz`


Matthew Reimer, 2015
