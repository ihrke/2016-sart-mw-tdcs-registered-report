
from psychopy import core, visual, gui, data, event, logging, monitors
from psychopy.tools.filetools import fromFile, toFile
import time, random, os, sys
import numpy as np

# in cm
monitor=monitors.Monitor("Tromso", distance=100, width=52)
monitor.setSizePix([1920,1200])

## window
fullscreen=True
stimcolor='black'


win = visual.Window([1920,1200],allowGUI=True, monitor=monitor, fullscr=fullscreen)

fint=1./win.getActualFrameRate()
print "Interval for a frame=%f s"%fint
print "That's %f frames per second"%(1./fint)


for num in range(1,10):
    number=visual.TextStim(win, pos=[0,0],text="%i"%num, units='deg', height=3,
                            alignHoriz='center', alignVert='center', color=stimcolor)
    number.draw()
win.flip()
print event.waitKeys()
