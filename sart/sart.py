"""
Sustained Attention to Respond Task (SART)
used in
"Increasing and decreasing propensity of mind wandering by transcranial direct current stimulation: A registered report"


Notes:

Timing works as follows:

1) Determine effective framerate by collecting frame times and averaging
2) Calculate number of frames for each desired duration
3) loop for number of frames and call win.flip() in every loop ->
   ensures that each frame has been shown

Author: Matthias Mittner <matthias.mittner@uit.no>
"""

from psychopy import core, visual, gui, data, event, logging, monitors
from psychopy.tools.filetools import fromFile, toFile
import time, random, os, sys
import numpy as np
import scipy.stats
import pandas as pd

def rtruncnorm(n, a, b, mean, sd):
    """wrap scipy.stats weird parametrization"""
    na, nb = (a - mean) / sd, (b - mean) / sd
    return scipy.stats.truncnorm.rvs(na,nb,loc=mean,scale=sd, size=n)

def get_stimuli(nnontargets, ntargets, nprobes):
    """randomization function (to be called for each half of the exp)"""
    ntargets_temp=ntargets/4
    nprobes_temp=nprobes/4
    nnontargets_temp=nnontargets/4
    stimulus_final=[]
    for index in range(0,4):
        ## first find number of nontargets per block subject to constraints
        blocks=0 
        while(np.sum(blocks)!=nnontargets_temp):
            blocks=np.array(np.round(rtruncnorm(ntargets_temp+nprobes_temp, 12, 29, 20, 5.69)), dtype=np.int)
        ## build stimulus array containing which stimulus is being shown (-1 = thought-probe)
        stimulus=np.zeros(nnontargets_temp+ntargets_temp+nprobes_temp, dtype=np.int)
        block_end=np.cumsum(blocks)+np.arange(len(blocks)) # indices where blocks end

        stimulus[block_end]=11 # thought-probe and target-stimulus locations
        stimulus[stimulus==0]=np.random.choice([0,1,2,4,5,6,7,8,9], nnontargets_temp, replace=True)
        npr=0 #counts number of probes
        ns=0 # counts number of target trails
        while((npr!=nprobes_temp)& (ns!=ntargets_temp)):
            stimulus[block_end]=11 # thought-probes and target-stimuli locations
            stimulus[stimulus==11]=np.random.choice([3,-1], ntargets_temp+nprobes_temp, replace=True)
            inds = np.where(stimulus ==3)
            ns=len(inds[0])
            
            inds =np.where(stimulus ==-1)
            npr=len(inds[0])
        stimulus_final=np.concatenate((stimulus_final, stimulus))
    return stimulus_final

def get_stimuli_training(nnontargets, ntargets, nprobes):
    """randomization function (to be called for training trail)"""

    ## first find number of nontargets per block subject to constraints
    blocks=0 
    while(np.sum(blocks)!=nnontargets):
        blocks=np.array(np.round(rtruncnorm(ntargets+nprobes, 12, 29, 20, 5.69)), dtype=np.int)

    ## build stimulus array containing which stimulus is being shown (-1 = thought-probe)
    stimulus=np.zeros(nnontargets+ntargets+nprobes, dtype=np.int)
    block_end=np.cumsum(blocks)+np.arange(len(blocks)) # indices where blocks end
    stimulus[block_end[0:len(block_end):2]]=3 # target-stimulus locations
    stimulus[block_end[1:len(block_end):2]]=-1 # thought-probe locations
    stimulus[stimulus==0]=np.random.choice([0,1,2,4,5,6,7,8,9], nnontargets, replace=True)
    return stimulus

##-----------------------------------------------------------------------
## global vars
##-----------------------------------------------------------------------
datadir='./data'
instruction_file="./instructions_en.py" 
debug=False
stimcolor='black'
bgcolor=[104, 104, 104]
detect_dropped_frames=True
sepchar=","
fullscreen=True

key_response='space'  #'left'
key_numbers=["1","2","3","4"]
quit_key= 'escape'
valid_keys=[key_response]+key_numbers
key_left="lctrl"
key1="1"
key2="2"
key3="3"
key4="4" 

# durations in s
dnumber  = 1.0    
dblank   = 1.2
dprobe   = 6.0

# per half of experiment
nnontargets=500
ntargets=12
nprobes=12
ntrials=nnontargets+ntargets+nprobes

# create randomized stimuli
#stimuli_half1 = get_stimuli(nnontargets, ntargets, nprobes)
#stimuli_half2 = get_stimuli(nnontargets, ntargets, nprobes)
#stimuli=np.concatenate((stimuli_half1, stimuli_half2))

#Save stimuli to text file
#np.savetxt("Experiment_stimuli.csv", stimuli, delimiter=",")

#Read stimuli from  text file
stimuli = pd.read_csv('./Experiment_stimuli.csv',header=None)
stimuli=np.asarray(stimuli.values.tolist())
stimuli.shape=(len(stimuli),)
ntotal=len(stimuli) 

# setup training session
#nnontargets_training=80
#ntargets_training=2
#nprobes_training=2
#stimuli_training = get_stimuli_training(nnontargets_training, ntargets_training, nprobes_training)
#
#Save stimuli to text file
#np.savetxt("stimuli_training.csv", stimuli_training, delimiter=",")

#Read stimuli from  text file
stimuli_training = pd.read_csv('./stimuli_training.csv',header=None)
stimuli_training=np.asarray(stimuli_training.values.tolist())
stimuli_training=stimuli_training.astype(int)
stimuli_training.shape=(len(stimuli_training),)

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
monitor=monitors.Monitor("Tromso", distance=100, width=52)
monitor.setSizePix([1920,1200])
win = visual.Window([1920,1200],allowGUI=True, monitor=monitor, units='deg', fullscr=fullscreen,colorSpace = 'rgb255',color = bgcolor )

##-----------------------------------------------------------------------
# record frame-rate
##-----------------------------------------------------------------------
fint=1./win.getActualFrameRate()
print "Logging to ", fname
print "Interval for a frame=%f s"%fint
print "That's %f frames per second"%(1./fint)

# durations in frames
fnumber  =int(np.ceil(dnumber/fint))
fblank   =int(np.ceil(dblank/fint))
fprobe   =int(np.ceil(dprobe/fint))
datafile.write("##Expected errors:\n"
               "# number  : %f vs. %f\n"
               "# blank   : %f vs. %f\n"
               "# probe   : %f vs. %f\n"%(dnumber,fnumber*fint, dblank, fblank*fint,
                                          dprobe, fprobe*fint))
datafile.flush()

datafields=['time','condition','trial','type', 'number', 'response', 'nresponses', 'RT','time_number','time_blank','time_probe']
datafile.write(sepchar.join(datafields)+"\n")
datafile.flush()

eclock = core.Clock() # experiment-clock
fclock = core.Clock() # frame-clock

def logdata(**kwargs):
    data={'time':eclock.getTime(), 'condition':-1, 'trial':-1, 'type':-1, 'response':-1,
          'RT':-1.0, 'number':-1, 'nresponses':0,
          'time_number':-1, 'time_blank':-1, 'time_probe':-1}
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
        lab=[visual.TextStim(win, pos=(ticks[0], -.1), units='norm', text='1', height=.1, color=stimcolor),
             visual.TextStim(win, pos=(ticks[1], -.1), units='norm', text='2', height=.1, color=stimcolor),
             visual.TextStim(win, pos=(ticks[2], -.1), units='norm', text='3', height=.1, color=stimcolor),
             visual.TextStim(win, pos=(ticks[-1], -.1), units='norm', text='4', height=.1, color=stimcolor),
             visual.TextStim(win, pos=(ticks[0]+.1, -.28), units='norm', text='Minimal task-unrelated thought', wrapWidth=0.2, height=.05, color=stimcolor),
             visual.TextStim(win, pos=(ticks[-1]+.1, -.28), units='norm', text='Maximal task-unrelated thought', wrapWidth=0.2, height=.05, color=stimcolor),
             visual.TextStim(win, pos=(0, .5), units='norm',text=' To what extent have you experienced \n task-unrelated thoughts \n prior to the thought probe?',  alignHoriz='center', wrapWidth=1.5, height=.1, color=stimcolor)]

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


    def arrow_move(self,keys):
        if self.current_pos==keys-1:
            return
        else:
            self.set_arrow(keys-1)


    def draw(self):
        for el in self.elements:
            el.draw()
        self.arrow.draw()

number=visual.TextStim(win, pos=[0,0],text="", units='deg',  height=4.2,
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
    num=int(num)
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
        if  key1 in keys:
          probe.arrow_move(int(key1))
        elif key2 in keys:
            probe.arrow_move(int(key2))
        elif key3 in keys:
            probe.arrow_move(int(key3))
        elif key4 in keys:
            probe.arrow_move(int(key4))
    stats['time_probe']=fclock.getTime()
    stats['response']=probe.current_pos+1
    return stats

def show_instruction(screen):
    """screen is a list of strings that is displayed on one screen"""
    event.getKeys() # clear buffer
    r=None
    if not debug:
        for i,inst in enumerate(screen):
            ypos=1-(pad+(i+1)*(2.0-2*pad)/len(screen))
            msg=visual.TextStim(win, pos=[0,ypos],text=unicode(inst,"utf-8"), units='norm', height=0.075, #size=(2.0,1.0),
                                alignHoriz='center', alignVert='center', color=stimcolor ,wrapWidth=1.8)
            msg.draw()
        win.flip()
        r=event.waitKeys()[0]
    return r

##-----------------------------------------------------------------------
## instructions
##-----------------------------------------------------------------------
pad=0.1

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
for screen in instructions['training']:
    show_instruction(screen)


for i,num in enumerate(stimuli_training):
    stats={'condition':'train', 'trial':i+1}
    if num<0:
        # probe
        res=show_probe()

    else:
        res=show_trial(num)
    stats.update(res)
    logdata(**stats)


##-----------------------------------------------------------------------
## full experiment
##-----------------------------------------------------------------------
for screen in instructions['experiment']:
    show_instruction(screen)

iprobes=0 # number of probes already shown
for i,num in enumerate(stimuli):

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
