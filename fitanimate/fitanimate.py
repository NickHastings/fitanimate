#!/usr/bin/env python3
import configargparse
from pathlib import Path
import os
import sys

import fitanimate.plot as fap
import fitanimate.data as fad

import matplotlib.pyplot as plt
plt.rcdefaults()
import matplotlib.animation as animation
import matplotlib.gridspec as gridspec

import cartopy.crs as crs

def getFontSize( x, dpi ):
    # For 64 point font for 4k (x=3840,y=2160) @ 100 dpi
    return int(64* x/3840 * 100.0/dpi)

def main():
    videoFormats = {
        '240p': (426,240),
        '360p': (640,360),
        '480p': (720,480),
        '720p': (1280,720),
        '1080p': (1920,1080),
        '1440p': (2560,1440),
        '4k' : (3840,2160)
    }

    defaultFields = ['timestamp', 'temperature', 'heart_rate', 'lap', 'gears', 'altitude', 'grad', 'distance']

    parser = configargparse.ArgumentParser(default_config_files=
                                           [ os.path.join( str(Path.home()), '.config', 'fitanimate', '*.conf'),
                                             os.path.join( str(Path.home()), '.fitanimate.conf') ]
    )

    parser.add_argument(
        'infile', metavar='FITFILE', type=configargparse.FileType(mode='rb'),
        help='Input .FIT file (Use - for stdin)',
    )
    parser.add_argument(
        '--offset', type=float, default=0.0, help='Time offset (hours)'
    )
    parser.add_argument(
        '--show',    '-s', action='store_true', default=False, help='Show the animation on screen'
    )
    parser.add_argument(
        '--num',    '-n', type=int, default=0, help='Only animate the first NUM frames'
    )
    parser.add_argument(
        '--fields', type=str, action='append', default=[], help='Fit file variables to display.', choices=fap.RideText.supportedFields
    )
    parser.add_argument(
        '--outfile', '-o', type=str, default=None, help='Output filename'
    )
    parser.add_argument(
        '--format', '-f', type=str, default='1080p', choices=videoFormats.keys(),
        help='Output video file resolution.'
    )
    parser.add_argument(
        '--dpi', '-d', type=int, default=100,
        help='Dots Per Inch. Probably shouldn\'t change'
    )
    parser.add_argument(
        '--text-color', '-c', type=str, default='black',
        help='Text Color'
    )
    parser.add_argument(
        '--vertical', '-v', action='store_true', default=False, help='Plot bars Verticaly'
    )
    parser.add_argument(
        '--elevation-factor', '-e', type=float, default=5.0, help='Scale the elevation by this factor in the plot.'
    )
    parser.add_argument(
        '--test', '-t', action='store_true', help='Options for quick tests. Equivalent to "-s -f 360p".'
    )
    args = parser.parse_args()

    if args.test:
        args.format = '360p'
        args.show = True

    x, y = videoFormats[args.format]

    plt.rcParams.update({
        'font.size': getFontSize(x,args.dpi),
        'figure.dpi': args.dpi,
        'text.color': args.text_color,
        'axes.labelcolor': args.text_color,
        'xtick.color': args.text_color,
        'ytick.color': args.text_color
    })

    projection = crs.PlateCarree()
    fig = plt.figure(figsize=(x/args.dpi,y/args.dpi))

    gs_e  = gridspec.GridSpec(1,1)
    gs_e.update( left=0.6, right=1.0, top=1.0, bottom=0.8)
    a_e   = plt.subplot( gs_e[0,0] )

    gs_m  = gridspec.GridSpec(1,1)
    gs_m.update( left=0.6, right=1.0, top=0.8, bottom=0.4)
    a_m   = plt.subplot( gs_m[0,0], projection=projection  )

    gs_b  = gridspec.GridSpec(1,1)
    gs_b.update( left=0.11, right=1.0, top=0.15, bottom=0.0)
    a_bar = plt.subplot( gs_b[0,0] )

    fig.patch.set_alpha(0.) # Transparant background

    # See https://adrian.pw/blog/matplotlib-transparent-animation/

    plotVars = []
    plotVars.append( fap.PlotVar('cadence', 'Cadence', 'RPM', 120.0 ) )
    plotVars.append( fap.PlotVar('speed', 'Speed', 'km/h', 80.0, scaleFactor=3.6 ) )
    plotVars.append( fap.PlotVar('power', 'Power',' W', 1000.0))

    if args.vertical:
        gs_b.update( left=0.0, bottom=0.05, top=0.25)
        plotBar = fap.BarPlot( plotVars, a_bar )
    else:
        plotBar = fap.HBarPlot( plotVars, a_bar )

    plots = [plotBar]

    if len(args.fields) == 0:
        args.fields = defaultFields

    plots.append( fap.RideText( fig, args.fields ) )

    mp = fap.MapPlot(a_m, projection )
    plots.append(mp)
    ep = fap.ElevationPlot( a_e, args.elevation_factor )
    plots.append(ep)

    record_names = []
    for plot in plots:
        record_names += plot.ffNames

    # Remove duplicates
    record_names = list(dict.fromkeys(record_names))
    dataGen = fad.DataGen( fad.prePocessData(args.infile, record_names , int(args.offset*3600.0) ) )

    mp.DrawBasePlot( dataGen.lonArr, dataGen.latArr )
    ep.DrawBasePlot( dataGen.dArr, dataGen.aArr )

    # Check the dimensions of the map plot and move it to the edge/top
    dyOverDx = mp.getHeightOverWidth()
    gs_points = gs_m[0].get_position(fig).get_points()
    xmin = gs_points[0][0]
    ymin = gs_points[0][1]
    xmax = gs_points[1][0]
    ymax = gs_points[1][1]
    dx=xmax-xmin
    dy=ymax-ymin
    if dyOverDx>1.0: # Tall plot. Maintain gridspec height, change width
        dx_new = dx/dyOverDx
        xmin_new = xmax - dx_new
        gs_m.update(left=xmin_new)
    else: # Wide plot. Move up
        dy_new = dy * max(dyOverDx,0.6) # Don't scale to less that 60%... messes up for some reason
        ymin_new = ymax - dy_new
        gs_m.update(bottom=ymin_new)

    nData = dataGen.dataSet.nFrames()
    if args.num:
        nData = args.num

    # Time interval between frames in msec.
    inter = 1000.0/float(dataGen.dataSet.fps)
    anim=animation.FuncAnimation(fig, fad.run, dataGen, fargs=(fig,tuple(plots),), repeat=False,blit=False,interval=inter,save_count=nData)

    outf = os.path.splitext(os.path.basename(args.infile.name))[0] + '_overlay.mp4'
    if args.outfile:
        outf = args.outfile

    if not args.show:
        anim.save(outf, codec="png", fps=dataGen.dataSet.fps,
                  savefig_kwargs={'transparent': True, 'facecolor': 'none'})

    if args.show:
        plt.show()

if __name__ == '__main__':
    main()
