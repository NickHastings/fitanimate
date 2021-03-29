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

class TextData:
    def __init__(self, axes):
        self.axes = axes
        self.txt = []

    def ffNames(self):
        """
        Return list of fit file variable names requred for this plot
        """
        return [ 'temperature', 'altitude']

    def update(self, data):
        ffnames = self.ffNames()
        for n in ffnames:
            if not (n in data):
                return

        x = [-0.5, -0.5]
        y = [1.0, 0.7]

        s = [
            '{} C'.format(data[ffnames[0]]),
            '{:.0f} m'.format(data[ffnames[1]])
        ]

        if len(self.txt)<1:
            for i in range(len(ffnames)):
                self.txt.append( self.axes.text(x[i],y[i],s[i]) )
            return

        for i in range(len(ffnames)):
            self.txt[i].set_text(s[i])


# Only one bar
class BarPlot:
    def __init__(self, ffname, name, units, axes, limit = 100, value = 0.0, scaleFactor=1.0, offSet=0.0 ):
        self.ffname = ffname # name in fit file
        self.name = name
        self.units = units
        self.scaleFactor = scaleFactor # Multiply ff data by this
        self.offSet = offSet # Add this to ff data
        self.axes = axes
        self.axes.autoscale_view('tight')
        self.axes.set_ylim( 0, limit )
        self.axes.set_title( self.lable(value),  y=-0.3 )
        self.bar = self.axes.bar( name, value, alpha=0.5 )

    def ffNames(self):
        """
        Return list of fit file variable names requred for this plot
        """
        return [ self.ffname ]

    def lable(self, value =0.0):
        return '{:3.0f} {:s}'.format(value,self.units)
    def update(self, data ):
        value = data[self.ffname]*self.scaleFactor + self.offSet
        self.bar[0].set_height(value)
        self.axes.set_title( self.lable(value) )

def safeData(d):
    if d is None:
        return 0.0
    else:
        return float(d)

class DataSet:
    def __init__(self):
        self.data = []
        self.intData = []
        self.fps = 10
        self._step  = 0

    def addData(self, data ):
        if len(self.data) < 1:
            self.data.append( data )
            return True

        t_prev = int(self.data[-1]['timestamp'])
        dt = int(data['timestamp'])-t_prev
        if dt == 0:
            return True

        if dt<0:
            print('Negative time delta! Not adding data')
            return False

        # If there are missing seconds since the last entry
        # Fill in the missing data with data from the last entry
        dp = self.data[-1]
        for tt in range(t_prev+1, data['timestamp']-1):
            dnew = {}
            for f in dp.keys():
                dnew[f] = safeData(data[f])

            dnew['timestamp'] = tt

            self.data.append( dnew )

        self.data.append( data )
        return True

    def interpolateData(self):
        self.intData.append( self.data[0] )
        d0 = self.data[0]
        for i in range(1,len(self.data)):
            d1 = self.data[i]
            for j in range(self.fps):
                self._step = j
                dnew = {}
                for f in d0.keys():
                    dnew[f] = self._interpolate(d0[f],d1[f])

                self.intData.append( dnew )
                d0 = d1

    def nFrames(self):
        return self.fps * len(self.data)

    def _interpolate(self, v0, v1 ):
        return ( (self.fps-self._step)*v0 + self._step*v1)/float(self.fps)

    def dump(self):
        for d in self.data:
            print(d)


def prePocessData( infile, timeoffset=None, fields = ['power','speed','cadence','heart_rate'] ):
    dataset = DataSet()
    ff = fitparse.FitFile( infile )

    for record in ff.get_messages('record'):
        data = {}
        data['timestamp'] = int(record.get_value('timestamp').timestamp())
        if timeoffset:
            data['timestamp'] += timeoffset

        for f in fields:
            data[f] = safeData( record.get_value(f) )

        ok = dataset.addData(data)
        if not ok:
            print( 'Problem adding data point. Not adding any more data.')
            dataset.interpolateData()
            return dataset

    dataset.interpolateData()
    return dataset


def run(data,fig,plots):

    tstr = datetime.fromtimestamp(int(data['timestamp']))

    fig.suptitle('{}'.format(tstr))

    for plot in plots:
        plot.update(data)


# Yeilds to first argument of run()
class DataGen():
    def __init__(self, dataSet ):
        self.dataSet = dataSet

    def __call__(self):

        for data in self.dataSet.intData:
            yield data


parser = argparse.ArgumentParser()
parser.add_argument(
    'infile', metavar='FITFILE', type=argparse.FileType(mode='rb'),
    help='Input .FIT file (Use - for stdin)',
)
parser.add_argument(
    '--offset', '-o', type=float, default=9.0, help='Time offset (hours)'
)
parser.add_argument(
    '--show',    '-s', action='store_true', default=False, help='Show animation'
)
parser.add_argument(
    '--num',    '-n', type=int, default=0, help='Only animate th first N frames'
)
parser.add_argument(
    '--outfile',type=str, default=None, help='Output filename'
)

# 1920×1080  => 16:9
# Size here is in inches
# matplotlib seems to use 100 DPI
# => 19.20,10.80 for 1080p

# rows,columns grid
fig, axes = plt.subplots(3,4,figsize=(19.20,10.80))
[ax.set_axis_off() for ax in axes.ravel()]
(a_p, a_s, a_c, a_h) = axes[2]
a_t = axes[0][0]

# set figure background opacity (alpha) to 0
fig.patch.set_alpha(0.) # Transparant background

# See https://adrian.pw/blog/matplotlib-transparent-animation/

plotPower = BarPlot( 'power', 'Power',' W',  a_p, limit=1000.0)
plotSpeed = BarPlot( 'speed', 'Speed', 'km/h', a_s, limit= 60.0, scaleFactor=3.6 )
plotCadence = BarPlot( 'cadence', 'Cadence', 'RPM', a_c, limit = 110.0 )
plotHR  = BarPlot( 'heart_rate', 'Heart Rate', 'BPM', a_h, limit = 190.0 )
plotText = TextData( a_t )
plots = (plotPower, plotSpeed, plotCadence, plotHR, plotText)

args = parser.parse_args()
fields = []
for plot in plots:
    fields += plot.ffNames()

dataGen = DataGen( prePocessData(args.infile, int(args.offset*3600.0), fields ) )

nData = dataGen.dataSet.nFrames()
if args.num:
    nData = args.num

# Time interval between frames in msec.
inter = 1000.0/float(dataGen.dataSet.fps)
anim=animation.FuncAnimation(fig, run, dataGen, fargs=(fig,plots,), repeat=False,blit=False,interval=inter,save_count=nData)

outf = os.path.splitext(os.path.basename(args.infile.name))[0] + '.mp4'
if args.outfile:
    outf = args.outfile

anim.save(outf, codec="png", fps=dataGen.dataSet.fps,
          savefig_kwargs={'transparent': True, 'facecolor': 'none'})

if args.show:
    plt.show()
