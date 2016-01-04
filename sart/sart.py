"""
Timing works as follows:

1) Determine effective framerate by collecting frame times and averaging
2) Calculate number of frames for each desired duration
3) loop for number of frames and call win.flip() in every loop ->
   ensures that each frame has been shown
"""

from psychopy import core, visual, gui, data, event, logging, sound
from psychopy.tools.filetools import fromFile, toFile
import time, random, os, sys
import numpy as np
#import pylab as pl

##-----------------------------------------------------------------------
## global vars
##-----------------------------------------------------------------------

datadir='./data'
instruction_file="./instructions_no.py"
debug=False
stimcolor='white'
detect_dropped_frames=True
sepchar=","
fullscreen=False #True

key_left='lctrl'  #'left'
key_right='right'
quit_key='escape'
valid_keys=[key_left, key_right]

# durations in s
dfixcross=.250
dnumber  =.250
dblank   =.900
dprobe   = 6.0

ntrials=720
nprobes=20
ntotal=ntrials+nprobes
ntraining=20
ntrials_probe_min=28
ntrials_probe_max=44
nstop_block=4
numbers=[i for i in range(1,10)]

## randomization
probe_trials=[]
for i in range(nprobes-1):
    offset=probe_trials[i-1] if i!=0 else 0
    probe_trials.append(np.random.randint(low=offset+ntrials_probe_min, high=offset+ntrials_probe_max+1))
probe_trials.append(ntrials-1)
probe_trials+=np.arange(1,nprobes+1)


trials=np.zeros(ntotal, dtype=np.int)
trials[probe_trials]=-1

# stop-trials
for i,last in enumerate(probe_trials):
    first=probe_trials[i-1]+1 if i!=0 else 0
    stop=np.random.choice(np.arange(first,last), nstop_block, replace=False)
    trials[stop]=3

## rest is random
# random 
#trials[trials==0]=np.random.choice([1,2,4,5,6,7,8,9], ntrials-nprobes*nstop_block, replace=True)
# random permutation
trials[trials==0]=np.random.permutation(np.concatenate( [ [i]*((ntrials-nprobes*nstop_block)/8) for i in [1,2,4,5,6,7,8,9]]))

print "nstop  =", np.sum(trials==3)
print "nprobes=", np.sum(trials==-1)
for i in [1,2,4,5,6,7,8,9]:
    print "n(%i)=%i"%(i, np.sum(trials==i))
#pl.plot( trials, '-o')
#pl.ylim(-1.1, 9.1)
#pl.show()
#core.exit()

    
##-----------------------------------------------------------------------
## setup config
##-----------------------------------------------------------------------
if not os.path.exists(datadir):
    print "> creating ", datadir
    os.makedirs(datadir)
    
try:#try to get a previous parameters file
    expinfo = fromFile(os.path.join(datadir, 'last_params.pickle'))
except:#if not there then use a default set
    expinfo = {'subject_id':'', 'session':'', 'condition':''}
    
expinfo['date']= data.getDateStr() #add the current time

instr={}
execfile(instruction_file, instr)
instructions=instr['instructions']

#present a dialogue to change params
if not debug:
    dlg = gui.DlgFromDict(expinfo, title='Body SART', fixed=['dateStr'])
    if dlg.OK:
        toFile(os.path.join(datadir, 'last_params.pickle'), expinfo)#save params to file for next time
    else:
        core.quit()#the user hit cancel so exit
    
#make a text file to save data
fname = os.path.join('./data/%03i_%s_%s.csv'%(int(expinfo['subject_id']),
                                              expinfo['session'], expinfo['date']))
datafile = open(fname, 'w')
# write header
datafile.write('# subject_id={subject_id}\n# date={date}\n# session={session}\n# condition={condition}\n'.format(**expinfo))
datafile.flush()

## window
win = visual.Window([1024,768],allowGUI=True, monitor='testMonitor', units='deg', fullscr=fullscreen)

##-----------------------------------------------------------------------
# record frame-rate
##-----------------------------------------------------------------------
fint=1./win.getActualFrameRate()
print "Logging to ", fname
print "Interval for a frame=%f s"%fint
print "That's %f frames per second"%(1./fint)

# durations in frames
ffixcross=int(np.ceil(dfixcross/fint))
fnumber  =int(np.ceil(dnumber/fint))
fblank   =int(np.ceil(dblank/fint))
fprobe   =int(np.ceil(dprobe/fint))
datafile.write("##Expected errors:\n"
               "# fixcross: %f vs. %f\n"
               "# number  : %f vs. %f\n"
               "# blank   : %f vs. %f\n"
               "# probe   : %f vs. %f\n"%(dfixcross, ffixcross*fint, dnumber,
                                          fnumber*fint, dblank, fblank*fint,
                                          dprobe, fprobe*fint))
datafile.flush()

datafields=['time','condition','trial','type', 'number', 'response', 'nresponses', 'RT', 'time_fixcross','time_number','time_blank','time_probe']
datafile.write(sepchar.join(datafields)+"\n")
datafile.flush()

eclock = core.Clock() # experiment-clock
fclock = core.Clock() # frame-clock

def logdata(**kwargs):
    data={'time':eclock.getTime(), 'condition':-1, 'trial':-1, 'type':-1, 'response':-1,
          'RT':-1.0, 'number':-1, 'nresponses':0, 
          'time_fixcross':-1, 'time_number':-1, 'time_blank':-1, 'time_probe':-1}
    data.update(kwargs)
    datafile.write(sepchar.join([str(data[field]) for field in datafields])+"\n")
    datafile.flush()



class ProbeStim:
    def __init__(self, win, nposs=4):
        start,end=-.5, .5
        ypad=.05
        self.nposs=nposs
        line=visual.Line(win, start=(start, 0), end=(end,0), units='norm', lineColor=stimcolor, lineWidth=5)
        ticks=start+np.arange(0,nposs)*(end-start)/float(nposs-1)
        poss=[visual.Line(win, start=(tick, -ypad), end=(tick,ypad), units='norm', lineColor=stimcolor,
                          lineWidth=3) for tick in ticks]
        lab=[visual.TextStim(win, pos=(ticks[0], -.1), units='norm', text='on-task', height=.05, color=stimcolor),
             visual.TextStim(win, pos=(ticks[-1], -.1), units='norm', text='off-task', height=.05, color=stimcolor)]

        self.arrow_v=0.4*np.array([ [0,0], [.2, .2], [.1, .2], [.1, .5], [-.1, .5], [-.1, .2], [-.2, .2], [0, 0]])
        self.arrow_v[:,1]+=ypad+.01
        self.ticks=ticks
        self.arrow=visual.ShapeStim(win, vertices=self.arrow_v, fillColor=stimcolor, units='norm')
                
        self.init_random()

        self.elements=[line]+poss+lab

    def init_random(self):
        ## initialize to either 0 or nposs-1
        initial_pos=np.random.choice([0,self.nposs-1])
        self.set_arrow(initial_pos)        
        
    def set_arrow(self, pos):
        self.current_pos=pos
        v=self.arrow_v.copy()
        v[:,0]+=self.ticks[pos]
        self.arrow.setVertices(v)

    def arrow_left(self):
        if self.current_pos==0:
            return
        else:
            self.set_arrow(self.current_pos-1)
            
    def arrow_right(self):
        if self.current_pos==self.nposs-1:
            return
        else:
            self.set_arrow(self.current_pos+1)
    
    def draw(self):
        for el in self.elements:
            el.draw()
        self.arrow.draw()

fixcross=visual.TextStim(win, pos=[0,0],text="+", units='norm', height=0.2, 
                        alignHoriz='center', alignVert='center', color=stimcolor)
number=visual.TextStim(win, pos=[0,0],text="", units='norm', height=0.3, 
                        alignHoriz='center', alignVert='center', color=stimcolor)
probe=ProbeStim(win)

if detect_dropped_frames:
    win.setRecordFrameIntervals(True)
    win._refreshThreshold=fint+0.004 
    #set the log module to report warnings to the std output window (default is errors only)
    logging.console.setLevel(logging.WARNING)


def show_trial(num):
    stats={'type':'go' if num!=3 else 'stop', 'number':num, 'nresponses':0}
    fclock.reset()
    for i in range(ffixcross):
        fixcross.draw()
        win.flip()
    stats['time_fixcross']=fclock.getTime()

    number.setText("%i"%num)
    fclock.reset()
    for i in range(fnumber):
        number.draw()
        win.flip()
        keys=event.getKeys()
        if set(valid_keys) & set(keys): #intersection on sets
            if stats['nresponses']==0:
                stats['response']=1
                stats['RT']=fclock.getTime()
            stats['nresponses']+=1
    stats['time_number']=fclock.getTime()

    fclock.reset()
    for i in range(fblank):
        win.flip()
        keys=event.getKeys()           
        if set(valid_keys) & set(keys):
            if stats['nresponses']==0:
                stats['response']=1
                stats['RT']=fclock.getTime()+stats['time_number']
            stats['nresponses']+=1
            
    stats['time_blank']=fclock.getTime()
    return stats

def show_probe():
    stats={'type':'probe'}

    # clear keybuffer
    event.getKeys()

    # set probe to either on- or off-task
    probe.init_random()
    
    fclock.reset()
    for i in range(fprobe):
        probe.draw()
        win.flip()
        keys=event.getKeys()
        if key_left in keys:
            probe.arrow_left()
        elif key_right in keys:
            probe.arrow_right()
    stats['time_probe']=fclock.getTime()
    stats['response']=probe.current_pos
    return stats

def show_instruction(screen):
    """screen is a list of strings that is displayed on one screen"""
    event.getKeys() # clear buffer
    r=None
    if not debug:
        for i,inst in enumerate(screen):
            ypos=1-(pad+(i+1)*(2.0-2*pad)/len(screen))
            msg=visual.TextStim(win, pos=[0,ypos],text=unicode(inst,"utf-8"), units='norm', height=0.08, #size=(2.0,1.0),
                                alignHoriz='center', alignVert='center', color=stimcolor, wrapWidth=1.8)
            msg.draw()
        win.flip()
        r=event.waitKeys()[0]
    return r
    

##-----------------------------------------------------------------------
## instructions
##-----------------------------------------------------------------------
pad=0.1

sync_sound=sound.Sound(800, secs=0.2)
stats={'condition':'sync', 'trial':0}
sync_sound.play()
logdata(**stats)

for screen in instructions['welcome']:
    show_instruction(screen)

if not debug:
    show_probe()
    show_instruction(instructions['probetraining'][0])
    while True:
        show_probe()    
        k=show_instruction(instructions['probetraining'][1])
        if k==key_left:
            continue
        else:
            break
    
##-----------------------------------------------------------------------
## training
##-----------------------------------------------------------------------

sync_sound=sound.Sound(800, secs=0.2)
stats={'condition':'sync', 'trial':0}
sync_sound.play()
logdata(**stats)


for screen in instructions['training']:
    show_instruction(screen)


probetrial=int(ntraining-(ntraining/4.))
for trial in range(1,ntraining+2):
    stats={'condition':'train', 'trial':trial}
    if trial==probetrial:
        res=show_probe()
    else:
        num=np.random.choice(numbers, size=1)[0]
        res=show_trial(num)
    stats.update(res)
    logdata(**stats)
    

##-----------------------------------------------------------------------
## full experiment
##-----------------------------------------------------------------------
for screen in instructions['experiment']:
    show_instruction(screen)

iprobes=0 # number of probes already shown
for i,num in enumerate(trials):
    stats={'condition':'exp', 'trial':i+1}
    if i==ntotal/2:
        for screen in instructions['halfway']:
            show_instruction(screen)
    if num<0:
        # probe
        res=show_probe()
    else:
        res=show_trial(num)
    stats.update(res)
    logdata(**stats)

datafile.close()
for screen in instructions['finish']:
    show_instruction(screen)

while True:
    win.flip()
    keys=event.getKeys()
    if quit_key in keys:
        break

##-----------------------------------------------------------------------
## cleaning up
##-----------------------------------------------------------------------

win.close()
if True:
    print "Content of datafile %s"%fname
    print "---------------------------------"
    print open(fname).read()
    print "---------------------------------"    


