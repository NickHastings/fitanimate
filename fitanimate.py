#!/usr/bin/env python3
import argparse
import os
import glob
import fitparse
from datetime import datetime

import matplotlib.pyplot as plt; plt.rcdefaults()
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

plt.rcParams.update({'font.size': 36})

# Only one bar
class BarPlot:
    def __init__(self, name, units, axes, limit = 100, value = 0.0 ):
        self.name = name
        self.units = units
        self.axes = axes
        self.axes.autoscale_view('tight')
        self.axes.set_ylim( 0, limit )
        self.axes.set_title( self.lable(value),  y=-0.3 )
        self.bar = self.axes.bar( name, value, alpha=0.5 )


    def lable(self, value =0.0):
        return '{:3.0f} {:s}'.format(value,self.units)
    def update(self, value ):
        self.bar[0].set_height(value)
        self.axes.set_title( self.lable(value) )

def safeData(d):
    if d is None:
        return 0.0
    else:
        return float(d)

class DataPoint:
    def __init__(self, t, p, s, c, h):
        self.t = t
        self.p = safeData(p)
        self.s = safeData(s)
        self.c = safeData(c)
        self.h = safeData(h)

    def __str__(self):
        return ' time = {:d}, power = {:5.1f} w, speed = {:4.1f} km/hr, cadance = {:3.0f} RPM, hr = {:3.0f}'.format(self.t, self.p, self.s, self.c, self.h)

class DataSet:
    def __init__(self):
        self.data = []
        self.intData = []
        self.fps = 10
        self._step  = 0
    
    def addData(self,t,p,s,c,h):
        if len(self.data) < 1:
            self.data.append( DataPoint(t,p,s,c,h) )
            return True

        t_prev = self.data[-1].t
        dt = t-t_prev
        if dt == 0:
            return True
        
        if dt<0:
            print('Negative time delta! Not adding data')
            return False

        # If there are missing seconds since the last entry
        # Fill in the missing data with data from the last entry
        dp = self.data[-1]
        for tt in range(t_prev+1, t):
            self.data.append(DataPoint(tt, dp.p, dp.s, dp.c, dp.h ))

        self.data.append( DataPoint(t,p,s,c,h) )            

        return True

    def interpolateData(self):
        self.intData.append( self.data[0] )
        d0 = self.data[0]
        for i in range(1,len(self.data)):
            d1 = self.data[i]

            for j in range(self.fps):
                self._step = j
                t = d0.t
                p = self._interpolate(d0.p,d1.p)
                s = self._interpolate(d0.s,d1.s)
                c = self._interpolate(d0.c,d1.c)
                h = self._interpolate(d0.h,d1.h)
                self.intData.append( DataPoint(t,p,s,c,h) )

            d0 = d1

            

    def nFrames(self):
        return self.fps * len(self.data)

    def _interpolate(self, v0, v1 ):
        return ( (self.fps-self._step)*v0 + self._step*v1)/float(self.fps)
        
    def dump(self):
        for d in self.data:
            print(d)
            
        
def prePocessData( infile, timeoffset=None ):
    dataset = DataSet()
    ff = fitparse.FitFile(infile )
    for record in ff.get_messages('record'):

        t = int(record.get_value('timestamp').timestamp())
        if timeoffset:
            t += timeoffset
        p = record.get_value('power')
        s = record.get_value('speed')*3.6
        c = record.get_value('cadence')
        h = record.get_value('heart_rate')
        
        ok = dataset.addData(t,p,s,c,h)
        if not ok:
            print( 'Problem adding data point. Not adding any more data.')
            dataset.interpolateData()
            return dataset

    dataset.interpolateData()        
    return dataset
        

def run(data,fig,plots):
    t, p, s, c, h = data

    tstr = (datetime.fromtimestamp(t))
    
    fig.suptitle('{}'.format(tstr))
    power, speed, cad = plots
    power.update(p)
    speed.update(s)
    cad.update(c)

# Yeilds to first argument of run()
class DataGen():
    def __init__(self, dataSet ):
        self.dataSet = dataSet

    def __call__(self):

        for data in self.dataSet.intData:
            yield data.t, data.p, data.s, data.c, data.h            
            
#def data_gen():
#    dataset = prePocessData()
#    for data in dataset.data:
#        yield data.t, data.p, data.s, data.c, data.h



# 1920×1080  => 16:9
# Size here is in inches
# matplotlib seems to use 100 DPI
# => 19.20,10.80 for 1080p

# 3x3 grid -> 9 sets of axes. Just use the bottom three
fig, axes = plt.subplots(3,3,figsize=(19.20,10.80))
[ax.set_axis_off() for ax in axes.ravel()]
(a_p, a_s, a_c) = axes[2]

# set figure background opacity (alpha) to 0
fig.patch.set_alpha(0.) # Transparant background

# See https://adrian.pw/blog/matplotlib-transparent-animation/

parser = argparse.ArgumentParser()
parser.add_argument(
    'infile', metavar='FITFILE', type=argparse.FileType(mode='rb'),
    help='Input .FIT file (Use - for stdin)',
)
parser.add_argument(
    '--offset', '-o', type=float, default=9.0, help='Time offset (hours)'
)

args = parser.parse_args()
dataGen = DataGen( prePocessData(args.infile, int(args.offset*3600.0) ) )

nData = dataGen.dataSet.nFrames()

plotPower = BarPlot( 'Power',' W',  a_p, limit=1000.0)
plotSpeed = BarPlot( 'Speed', 'km/h', a_s, limit= 60.0 )
plotCadence = BarPlot( 'Cadence', 'RPM', a_c, limit = 110.0 )
plots = (plotPower, plotSpeed, plotCadence)


inter = 1000.0/float(dataGen.dataSet.fps)
anim=animation.FuncAnimation(fig, run, dataGen, fargs=(fig,plots,), repeat=False,blit=False,interval=inter,save_count=nData)

outf = os.path.splitext(os.path.basename(args.infile.name))[0] + '.mov'
anim.save(outf, codec="png", fps=dataGen.dataSet.fps,
         savefig_kwargs={'transparent': True, 'facecolor': 'none'})

#plt.show()
