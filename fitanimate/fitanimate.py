'''Generate animations of data from fit file data
'''
import os
from pathlib import Path
import configargparse

from matplotlib import animation
from matplotlib import gridspec
from cycler import cycler
from cartopy import crs
import matplotlib.pyplot as plt
plt.rcdefaults()

import fitanimate.plot as fap
import fitanimate.data as fad

def get_font_size( x, dpi ):
    # For 64 point font for 4k (x=3840,y=2160) @ 100 dpi
    return int(64* x/3840 * 100.0/dpi)

def main():
    video_formats = {
        '240p': (426,240),
        '360p': (640,360),
        '480p': (720,480),
        '720p': (1280,720),
        '1080p': (1920,1080),
        '1440p': (2560,1440),
        '4k' : (3840,2160)
    }

    default_fields = ['timestamp', 'temperature', 'heart_rate',
                     'lap', 'gears', 'altitude', 'grad', 'distance']
    default_plots = ['cadence', 'speed', 'power']

    parser = configargparse.ArgumentParser(
        default_config_files=
        [ os.path.join( str(Path.home()), '.config', 'fitanimate', '*.conf'),
          os.path.join( str(Path.home()), '.fitanimate.conf') ],
        formatter_class=configargparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        'infile', metavar='FITFILE', type=configargparse.FileType(mode='rb'),
        help='Input .FIT file (Use - for stdin).',
    )
    parser.add_argument(
        '--offset', type=float, default=0.0, help='Time offset (hours).'
    )
    parser.add_argument(
        '--show',    '-s', action='store_true', default=False, help='Show the animation on screen.'
    )
    parser.add_argument(
        '--num',    '-n', type=int, default=0, help='Only animate the first NUM frames.'
    )
    parser.add_argument(
        '--fields', type=str, action='append', default=default_fields,
        help='Fit file variables to display as text.', choices=fap.RideText.supportedFields
    )
    parser.add_argument(
        '--plots', type=str, action='append', default=default_plots,
        help='Fit file variables to display as bar plot.', choices=fap.supportedPlots
    )
    parser.add_argument(
        '--no-elevation', action='store_true', default=False, help='Disable elevation plot.'
    )
    parser.add_argument(
        '--no-map', action='store_true', default=False, help='Disable map.'
    )
    parser.add_argument(
        '--outfile', '-o', type=str, default=None, help='Output filename.'
    )
    parser.add_argument(
        '--format', '-f', type=str, default='1080p', choices=video_formats.keys(),
        help='Output video file resolution.'
    )
    parser.add_argument(
        '--dpi', '-d', type=int, default=100,
        help='Dots Per Inch. Probably shouldn\'t change.'
    )
    parser.add_argument(
        '--text-color', '-c', type=str, default='black',
        help='Text Color.'
    )
    parser.add_argument(
        '--plot-color', type=str, default='tab:blue',
        help='Plot Color.'
    )
    parser.add_argument(
        '--highlight-color', type=str, default='tab:red',
        help='Plot Highlight Color.'
    )
    parser.add_argument(
        '--alpha', type=float, default=0.3, help='Opacity of plots.'
    )
    parser.add_argument(
        '--vertical', '-v', action='store_true', default=False, help='Plot bars Verticaly.'
    )
    parser.add_argument(
        '--elevation-factor', '-e', type=float, default=5.0,
        help='Scale the elevation by this factor in the plot.'
    )
    parser.add_argument(
        '--test', '-t', action='store_true',
        help='Options for quick tests. Equivalent to "-s -f 360p".'
    )
    args = parser.parse_args()

    if args.test:
        args.format = '360p'
        args.show = True

    if len(args.plots) != len(default_plots): # The user specified plots, remove the defaults
        args.plots = args.plots[len(default_plots):]

    if len(args.fields) != len(default_fields): # As above
        args.fields = args.fields[len(default_fields):]

    fap.PlotBase.alpha = args.alpha
    fap.PlotBase.highlight_color = args.highlight_color

    x, y = video_formats[args.format]

    plt.rcParams.update({
        'font.size': get_font_size(x,args.dpi),
        'figure.dpi': args.dpi,
        'text.color': args.text_color,
        'axes.labelcolor': args.text_color,
        'xtick.color': args.text_color,
        'ytick.color': args.text_color,
        'axes.prop_cycle': cycler('color', [args.plot_color])
    })

    fig = plt.figure(figsize=(x/args.dpi,y/args.dpi))

    # Elevation
    if args.no_elevation: # Don't make the elevation plot and remove related text
        for field in ['altitude','grad']:
            if field in  args.fields:
                args.fields.remove(field)

    else:
        gs_e  = gridspec.GridSpec(1,1)
        gs_e.update( left=0.6, right=1.0, top=1.0, bottom=0.8)
        a_e   = plt.subplot( gs_e[0,0] )

    # Map
    if args.no_map:
        field = 'distance'
        if field in args.fields:
            args.fields.remove(field)

    else:
        projection = crs.PlateCarree()
        gs_m  = gridspec.GridSpec(1,1)
        gs_m.update( left=0.6, right=1.0, top=0.8, bottom=0.4)
        a_m   = plt.subplot( gs_m[0,0], projection=projection  )

    # Bar
    gs_b  = gridspec.GridSpec(1,1)
    # If horizontal, size depends on the number of bars
    if args.vertical:
        height = 0.15
    else:
        height = 0.05*len(args.plots)

    gs_b.update( left=0.11, right=1.0, top=height, bottom=0.0)
    a_bar = plt.subplot( gs_b[0,0] )

    fig.patch.set_alpha(0.) # Transparant background

    # See https://adrian.pw/blog/matplotlib-transparent-animation/

    # Bar plots
    plot_vars = []
    for plot_variable in args.plots:
        plot_vars.append( fap.new_plot_var(plot_variable) )

    if args.vertical:
        gs_b.update( left=0.0, bottom=0.05, top=0.25)
        plot_bar = fap.BarPlot( plot_vars, a_bar )
    else:
        plot_bar = fap.HBarPlot( plot_vars, a_bar )

    plots = [plot_bar]

    # Text data
    plots.append( fap.RideText( fig, args.fields ) )

    map_plot = None
    if not args.no_map:
        map_plot = fap.MapPlot(a_m, projection )
        plots.append(map_plot)

    elevation_plot = None
    if not args.no_elevation:
        elevation_plot = fap.ElevationPlot( a_e, args.elevation_factor )
        plots.append(elevation_plot)

    record_names = []
    for plot in plots:
        record_names += plot.fit_file_names

    # Remove duplicates
    record_names = list(dict.fromkeys(record_names))
    data_generator = fad.DataGen( fad.prePocessData(args.infile, record_names,
                                                    int(args.offset*3600.0) ) )

    if map_plot:
        map_plot.draw_base_plot( data_generator.long_list, data_generator.lati_list )

    if elevation_plot:
        elevation_plot.draw_base_plot( data_generator.distance_list, data_generator.altitude_list )

    # Check the dimensions of the map plot and move it to the edge/top
    if map_plot:
        dy_over_dx = map_plot.get_height_over_width()
        gs_points = gs_m[0].get_position(fig).get_points()
        xmin = gs_points[0][0]
        ymin = gs_points[0][1]
        xmax = gs_points[1][0]
        ymax = gs_points[1][1]
        dx=xmax-xmin
        dy=ymax-ymin
        if dy_over_dx>1.0: # Tall plot. Maintain gridspec height, change width
            dx_new = dx/dy_over_dx
            xmin_new = xmax - dx_new
            gs_m.update(left=xmin_new)
        else: # Wide plot. Move up
            # Don't scale to less that 60%... messes up for some reason
            dy_new = dy * max(dy_over_dx,0.6)
            ymin_new = ymax - dy_new
            gs_m.update(bottom=ymin_new)

    number_of_frames = data_generator.data_set.number_of_frames()
    if args.num:
        number_of_frames = args.num

    # Time interval between frames in msec.
    inter = 1000.0/float(data_generator.data_set.fps)
    anim=animation.FuncAnimation(fig, fad.run, data_generator, fargs=(fig,tuple(plots),),
                                 repeat=False, blit=False, interval=inter,
                                 save_count=number_of_frames)

    outf = os.path.splitext(os.path.basename(args.infile.name))[0] + '_overlay.mp4'
    if args.outfile:
        outf = args.outfile

    if not args.show:
        anim.save(outf, codec="png", fps=data_generator.data_set.fps,
                  savefig_kwargs={'transparent': True, 'facecolor': 'none'})

    if args.show:
        plt.show()

if __name__ == '__main__':
    main()
