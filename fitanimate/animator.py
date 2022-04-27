'''Implements animation of FIT file data using
matplotlib animation
'''
import os

from cycler import cycler
from cartopy import crs

import matplotlib.gridspec as gspec
from matplotlib import animation
import matplotlib.pyplot as plt

import fitanimate.plot as fap
import fitanimate.data as fad

plt.rcdefaults()

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

def get_font_size(x_size, dpi):
    '''Set font size for a given DPI.
    For 64 point font for 4k (x=3840,y=2160) @ 100 dpi
    '''
    return int(64* x_size/3840 * 100.0/dpi)

class Element:
    '''An plot element to drawn
    '''
    def __init__(self, gridspec=None, axis=None, plot=None):
        self.gridspec = gridspec
        self.axis = axis
        self.plot = plot

class Animator:
    '''Worker class to perform anaimatons from FIT data
    '''
    def __init__(self, args):
        self.args = args

        self.data_generator = None
        self.plots = None
        self.fig = None

        self.elevation = None
        self.map = None
        self.bar = None

    def setup(self):
        '''Sets up plots based on the passed arguments
        '''

        if self.args.test:
            self.args.format = '360p'
            self.args.show = True

        if len(self.args.plots) != len(default_plots):
            # The user specified plots, remove the defaults
            self.args.plots = self.args.plots[len(default_plots):]

        if len(self.args.fields) != len(default_fields): # As above
            self.args.fields = self.args.fields[len(default_fields):]

        fap.PlotBase.alpha = self.args.alpha
        fap.PlotBase.highlight_color = self.args.highlight_color

        x_size, y_size = video_formats[self.args.format]

        plt.rcParams.update({
            'font.size': get_font_size(x_size,self.args.dpi),
            'figure.dpi': self.args.dpi,
            'text.color': self.args.text_color,
            'axes.labelcolor': self.args.text_color,
            'xtick.color': self.args.text_color,
            'ytick.color': self.args.text_color,
            'axes.prop_cycle': cycler('color', [self.args.plot_color])
        })

        self.fig = plt.figure(figsize=(x_size/self.args.dpi,y_size/self.args.dpi))

        self.setup_elevation()
        projection = self.setup_map()
        self.setup_bar()

        # Text data
        self.plots.append(fap.RideText(self.fig, self.args.fields))

        if self.map:
            self.map.plot = fap.MapPlot(self.map.axis, projection)
            self.plots.append(self.map.plot)

        if self.elevation:
            self.elevation.plot = fap.ElevationPlot(self.elevation.axis,
                                                    self.args.elevation_factor)
            self.plots.append(self.elevation.plot)

        record_names = []
        for plot in self.plots:
            record_names += plot.fit_file_names

        # Remove duplicates
        record_names = list(dict.fromkeys(record_names))
        self.data_generator = fad.DataGen(fad.pre_pocess_data(self.args.infile, record_names,
                                                    int(self.args.offset*3600.0)))

    def setup_elevation(self):
        ''' Setup Elevation plot
        '''
        if self.args.no_elevation: # Don't make the elevation plot and remove related text
            for field in ['altitude','grad']:
                if field in self.args.fields:
                    self.args.fields.remove(field)

        else:
            self.elevation = Element(gspec.GridSpec(1,1))
            self.elevation.gridspec.update(left=0.6, right=1.0, top=1.0, bottom=0.8)
            self.elevation.axis = plt.subplot(self.elevation.gridspec[0,0])

    def setup_map(self):
        '''Setup map plot
        '''
        if self.args.no_map:
            field = 'distance'
            if field in self.args.fields:
                self.args.fields.remove(field)
            return None

        projection = crs.PlateCarree()
        self.map = Element(gspec.GridSpec(1,1))
        self.map.gridspec.update(left=0.6, right=1.0, top=0.8, bottom=0.4)
        self.map.axis = plt.subplot(self.map.gridspec[0,0], projection=projection)

        return projection

    def setup_bar(self):
        ''' Setup bar plot
        '''
        self.bar = Element(gspec.GridSpec(1,1))
        # If horizontal, size depends on the number of bars
        if self.args.vertical:
            height = 0.15
        else:
            height = 0.05*len(self.args.plots)

        self.bar.gridspec.update(left=0.11, right=1.0, top=height, bottom=0.0)
        self.bar.axis = plt.subplot(self.bar.gridspec[0,0])

        self.fig.patch.set_alpha(0.) # Transparant background
        # See https://adrian.pw/blog/matplotlib-transparent-animation/

        plot_vars = []
        for plot_variable in self.args.plots:
            plot_vars.append(fap.new_plot_var(plot_variable))

        if self.args.vertical:
            self.bar.gridspec.update(left=0.0, bottom=0.05, top=0.25)
            plot_bar = fap.BarPlot(plot_vars, self.bar.axis)
        else:
            plot_bar = fap.HBarPlot(plot_vars, self.bar.axis)

        self.plots = [plot_bar]

    def draw(self):
        '''Draw the empty plots
        '''
        if self.map.plot:
            self.map.plot.draw_base_plot(self.data_generator.long_list,
                                         self.data_generator.lati_list)

        if self.elevation.plot:
            self.elevation.plot.draw_base_plot(self.data_generator.distance_list,
                                               self.data_generator.altitude_list)

        # Check the dimensions of the map plot and move it to the edge/top
        if self.map.plot:
            dy_over_dx = self.map.plot.get_height_over_width()
            gs_points = self.map.gridspec[0].get_position(self.fig).get_points()
            xmin = gs_points[0][0]
            ymin = gs_points[0][1]
            xmax = gs_points[1][0]
            ymax = gs_points[1][1]
            dx=xmax-xmin
            dy=ymax-ymin
            if dy_over_dx>1.0: # Tall plot. Maintain gridspec height, change width
                dx_new = dx/dy_over_dx
                xmin_new = xmax - dx_new
                self.map.gridspec.update(left=xmin_new)
            else: # Wide plot. Move up
                # Don't scale to less that 60%... messes up for some reason
                dy_new = dy * max(dy_over_dx,0.6)
                ymin_new = ymax - dy_new
                self.map.gridspec.update(bottom=ymin_new)


    def animate(self):
        '''Animate the data on the plots
        '''
        number_of_frames = self.data_generator.data_set.number_of_frames()
        if self.args.num:
            number_of_frames = self.args.num

        # Time interval between frames in msec.
        inter = 1000.0/float(self.data_generator.data_set.fps)
        anim=animation.FuncAnimation(self.fig, fad.run, self.data_generator,
                                     fargs=(self.fig,tuple(self.plots),),
                                     repeat=False, blit=False, interval=inter,
                                     save_count=number_of_frames)

        outf = os.path.splitext(os.path.basename(self.args.infile.name))[0] + '_overlay.mp4'
        if self.args.outfile:
            outf = self.args.outfile

        if not self.args.show:
            anim.save(outf, codec="png", fps=self.data_generator.data_set.fps,
                  savefig_kwargs={'transparent': True, 'facecolor': 'none'})

        if self.args.show:
            plt.show()
