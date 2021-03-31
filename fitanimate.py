#!/usr/bin/env python3
import argparse
import os
import sys
import glob
import fitparse
from datetime import datetime

import matplotlib.pyplot as plt; plt.rcdefaults()
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation


class TextLine:
    def __init__(self, axes, field_name, txt_format, x, y ):
        self.axes = axes
        self.field_name = field_name
        self.txt_format = txt_format
        self.x = x
        self.y = y
        self.value = 0

        self.axes_text = None

    def setAxesText(self):
        if not self.axes_text:
            self.axes_text = self.axes.text( self.x, self.y, self.txt_format.format( self.value ) )
            return

        self.axes_text.set_text( self.txt_format.format( self.value ) )

    def setValue(self, data ):
        if 'interpolated' in data and data['interpolated']:
            return False

        if not (self.field_name in data):
            return False

        self.value = data[self.field_name]
        return True

class CounterTextLine(TextLine):
    def __init__(self,axes, field_name, txt_format, x, y ):
        TextLine.__init__(self, axes, field_name, txt_format, x, y )

    def setValue(self, data):
        if self.value == 0 or self.field_name in data:
            self.value += 1
            return True

        return False

class TextPlot:
    def __init__(self, axes):
        self.axes = axes

        self.txt_lines = []
        self.txt_lines.append( CounterTextLine( self.axes, 'lap', 'Lap {}',   -0.5, 1.0 ) )
        self.txt_lines.append( TextLine( self.axes,'temperature', '{:.0f} ℃',    -0.5, 0.7 ) )
        self.txt_lines.append( TextLine( self.axes,'altitude',    '{:.0f} m', -0.5, 0.4 ) )

    def ffNames(self):
        """
        Return list of fit file record variable names requred for this plot
        """
        return [ 'temperature', 'altitude']

    def update(self, data):
        for txt_line in self.txt_lines:

            if not txt_line.setValue( data ):
                continue

            txt_line.setAxesText()

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

        self.data.append( data )
        return True

    def interpolateData(self):
        for i in range(len(self.data)-1):
            d0 = self.data[i]
            d1 = self.data[i+1]
            self.intData.append(d0)
            for j in range(1,self.fps):
                self._step = j
                dnew = {}
                for f in d0.keys():
                    if f != 'lap':
                        dnew[f] = self._interpolate(d0[f],d1[f],j)
                        dnew['interpolated'] = True

                self.intData.append( dnew )

    def nFrames(self):
        return self.fps * len(self.data)

    def _interpolate(self, v0, v1, step ):
        return ( (self.fps-step)*v0 + step*v1)/float(self.fps)

    def dump(self):
        for d in self.data:
            print(d)


def prePocessData( infile, timeoffset=None, record_names = ['power','speed','cadence','heart_rate'] ):
    dataset = DataSet()
    ff = fitparse.FitFile( infile )

    for message in ff.get_messages(['record','lap']):
        data = {}
        message_name = message.as_dict()['name']
        if message_name == 'record':
            data['timestamp'] = int(message.get_value('timestamp').timestamp())
            if timeoffset:
                data['timestamp'] += timeoffset



            for f in record_names:
                data[f] = safeData( message.get_value(f) )

            ok = dataset.addData(data)
            if not ok:
                print( 'Problem adding data point. Not adding any more data.')
                dataset.interpolateData()
                return dataset

        elif message_name == 'lap' and len(dataset.data)>0:
            # Just append to the previous data
            dataset.data[-1]['lap'] = True

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
    '--offset', type=float, default=9.0, help='Time offset (hours)'
)
parser.add_argument(
    '--show',    '-s', action='store_true', default=False, help='Show animation'
)
parser.add_argument(
    '--num',    '-n', type=int, default=0, help='Only animate th first N frames'
)
parser.add_argument(
    '--outfile', '-o', type=str, default=None, help='Output filename'
)
parser.add_argument(
    '--format', '-f', type=str, default='4k', help='Output file format. Valid values are 4k or 1080p'
)

args = parser.parse_args()

# 1920×1080  => 16:9
# Size here is in inches
# matplotlib seems to use 100 DPI
# => 19.20,10.80 for 1080p

# 4k  3840 x 2160

# rows,columns grid
if args.format == '1080p':
    x=19.20
    y=10.80
    fontSize=32
elif args.format == '4k':
    x=38.40
    y=21.60
    fontSize=64
else:
    print( 'Unkown output format {}'.format(args.format) )
    sys.exit(1)

plt.rcParams.update({'font.size': fontSize})

fig, axes = plt.subplots(3,4,figsize=(x,y))
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
plotText = TextPlot( a_t )
plots = (plotPower, plotSpeed, plotCadence, plotHR, plotText)


record_names = []
for plot in plots:
    record_names += plot.ffNames()

dataGen = DataGen( prePocessData(args.infile, int(args.offset*3600.0), record_names ) )

nData = dataGen.dataSet.nFrames()
if args.num:
    nData = args.num

# Time interval between frames in msec.
inter = 1000.0/float(dataGen.dataSet.fps)
anim=animation.FuncAnimation(fig, run, dataGen, fargs=(fig,plots,), repeat=False,blit=False,interval=inter,save_count=nData)

outf = os.path.splitext(os.path.basename(args.infile.name))[0] + '_overlay.mp4'
if args.outfile:
    outf = args.outfile

if not args.show:    
    anim.save(outf, codec="png", fps=dataGen.dataSet.fps,
              savefig_kwargs={'transparent': True, 'facecolor': 'none'})

if args.show:
    plt.show()
