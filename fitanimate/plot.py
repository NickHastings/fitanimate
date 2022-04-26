''' Classes to display and animate fit file data
'''
from datetime import datetime
import matplotlib.pyplot as plt

class TextLine:
    '''Base class for placeing a line of text
    '''
    def __init__(self, fig, field_name, txt_format, x=None, y=None, scale=None):
        self.fig = fig
        self.field_name = field_name
        self.txt_format = txt_format
        self.x = x
        self.y = y
        self.value = 0
        self.scale = scale

        self.fig_txt = None

    def set_axes_text(self):
        '''Sets the text
        '''
        if not self.fig_txt:
            self.fig_txt = self.fig.text(self.x, self.y, self.txt_format.format(self.value))
            return

        self.fig_txt.set_text(self.txt_format.format(self.value))

    def set_value(self, data):
        '''Sets the data value
        '''
        # Don't update the text data if it is just a subsecond interpolation
        if 'interpolated' in data and data['interpolated']:
            return False

        if not self.field_name in data:
            return False

        self.value = data[self.field_name]
        if self.scale:
            self.value *= self.scale

        return True

class CounterTextLine(TextLine):
    '''Text line consisting of an incrementing counter
    '''
    def __init__(self, fig, field_name, txt_format, x=None, y=None):
        TextLine.__init__(self, fig, field_name, txt_format, x, y)

    def set_value(self, data):
        if self.value == 0 or self.field_name in data:
            self.value += 1
            return True

        return False

class TSTextLine(TextLine):
    '''A showing a time of arbitrary format
    '''
    def __init__(self, fig, field_name, txt_format, x=None, y=None,
                 timeformat='%H:%M:%S'):
        TextLine.__init__(self, fig, field_name, txt_format, x, y)
        self.timeformat = timeformat

    def set_value(self,data):
        if not TextLine.set_value(self, data):
            return False

        self.value = datetime.fromtimestamp(int(self.value)).strftime(self.timeformat)
        return True


class TextPlot:
    '''Generic text data to display
    '''
    def __init__(self, fig):
        self.fig = fig
        self.text_lines = []

        # List of fit file record variable names requred for this plot
        self._fit_file_names = []

        # Postion of first text object if not specified
        self.x = 0.02
        self.y = 0.95

        # If position for new text is not given offset from previous text by this much
        self.dx = 0.0
        self.dy = -0.06

    def add_text_line(self, text_line):
        '''Adds new text line
        '''
        nlines = len(self.text_lines)

        if nlines < 1:
            xprev = self.x-self.dx
            yprev = self.y-self.dy
        else:
            xprev = self.text_lines[-1].x
            yprev = self.text_lines[-1].y

        if text_line.x is None:
            text_line.x = xprev + self.dx

        if text_line.y is None:
            text_line.y = yprev + self.dy

        self.text_lines.append(text_line)

        self._fit_file_names.append(text_line.field_name)

    @property
    def fit_file_names(self):
        '''Returns list of fit file record variable names requred for this plot
        '''
        return self._fit_file_names

    def update(self, data):
        '''Updates the text
        '''
        for text_line in self.text_lines:

            if not text_line.set_value(data):
                continue

            text_line.set_axes_text()

class RideText(TextPlot):
    '''Container for text to be displayed
    '''
    supported_fields = ['timestamp', 'temperature', 'core_temperature', 'heart_rate',
                       'lap', 'gears', 'altitude', 'grad', 'distance']
    def __init__(self, fig, fields):
        TextPlot.__init__(self, fig)
        self.fields = fields

        if 'timestamp' in self.fields:
            self.add_text_line(TSTextLine(self.fig,'timestamp', '{}')) #, x=.1, y=.9))

        if 'temperature' in self.fields:
            self.add_text_line(TextLine(self.fig,'temperature', '{:.0f} ℃'))

        if 'core_temperature' in self.fields:
            self.add_text_line(TextLine(self.fig,'core_temperature', '{:.1f} ℃'))

        if 'heart_rate' in self.fields:
            self.add_text_line(TextLine(self.fig,'heart_rate',  '{:.0f} BPM'))

        if 'lap' in self.fields:
            self.add_text_line(CounterTextLine(self.fig, 'lap', 'Lap {}'))

        if 'gears' in self.fields:
            self.add_text_line(TextLine(self.fig, 'gears', '{}'))

        # Position near the elevation profile
        if 'altitude' in self.fields or 'grad' in self.fields:
            self.add_text_line(TextLine(self.fig, 'altitude','{:.0f} m', x=0.9, y=0.95))
            self.add_text_line(TextLine(self.fig, 'grad', '{:5.1f}%'))

        # Near the map
        if 'distance' in self.fields:
            self.add_text_line(TextLine(self.fig, 'distance', '{:.1f} km', y=0.75, scale=0.001))

    # @property
    # def fit_file_names(self):
    #     """
    #     Return list of fit file record variable names requred for this plot
    #     """
    #     return [ 'temperature', 'altitude', 'heart_rate', 'gradient', 'distance']


class PlotVar:
    '''Information about a fitfile record to plot
    '''
    def __init__(self, fit_file_name, name, units, max_value,
                 min_value=0.0, scale_factor=1.0, offset=0.0):
        self.fit_file_name = fit_file_name # name in fit file
        self.name = name
        self.units = units
        self.max_value = max_value
        self.min_value = min_value
        self.scale_factor = scale_factor # Multiply ff data by this
        self.offset = offset # Add this to ff data


    def get_name_label(self):
        '''Return the variables name and units
        '''
        return f'{self.name} ({self.units})'

    def get_norm_value(self, data):
        '''Calculate and return the value normalised between 0 and 1
        '''
        return (self.get_value(data) - self.offset)/(self.max_value - self.min_value)

    def get_value(self, data):
        '''Calculate and return the scaled value
        '''
        val = data[self.fit_file_name]
        return val*self.scale_factor + self.offset

    def get_value_units(self, value):
        '''Return the value with units
        '''
        return f'{value:.0f} {self.units:}'

supported_plots = ['cadence', 'speed', 'power', 'heart_rate', 'None']
def new_plot_var(variable):
    '''Return a new PlotVar instance
    '''
    if variable == 'cadence':
        return PlotVar(variable,'Cadence', 'RPM', 120.0)

    if variable == 'speed':
        return PlotVar('speed', 'Speed', 'km/h', 80.0, scale_factor=3.6)

    if variable == 'power':
        return PlotVar('power', 'Power',' W', 1000.0)

    if variable == 'heart_rate':
        return PlotVar('heart_rate', 'HeartRate',' BPM', 200.0)

    if variable == 'None':
        return None

    raise ValueError(f'Illegal variable {variable}. Must be one of: ' +
                      ', '.join([str(v) for v in supported_plots]))

class PlotBase:
    '''Base class for a plot
    '''
    alpha = 0.3
    highlight_color = 'tab:green'

    # Nominal marker sizes are for 3840x2160 (4K) at 100 DPI
    nom_dpi = 100.0
    nom_size = [3840/nom_dpi, 2160/nom_dpi]

    # Normal plot marker size. Diameter in pixels.
    nom_pms = 12

    def __init__(self):
        figure = plt.gcf()
        dpi = figure.dpi
        size = figure.get_size_inches()

        # Scale by size and DPI
        self.pms = self.nom_pms * size[0]/self.nom_size[0] * dpi/self.nom_dpi

        # area is pi*r^2
        self.sms = 3.14159*(0.5*self.pms)**2

class BarPlotBase(PlotBase):
    '''Bar Plot Base Class
    '''
    def __init__(self, plot_vars, axes):
        PlotBase.__init__(self)
        self.bar = None # To be set in derived classes
        self.plot_vars = plot_vars
        self.axes = axes
        self.axes.autoscale_view('tight')
        self.axes.set_axis_on()
        self.axes.tick_params(axis='both', which='both',length=0)
        for side in ['top','bottom','left','right']:
            self.axes.spines[side].set_visible(False)

        self.make_bars([plot_var.name for plot_var in self.plot_vars])

        self.text = []

        for i, _ in enumerate(self.plot_vars):
            self.append_text(i)

    @property
    def fit_file_names(self):
        '''Returns list of fit file record variable names requred for this plot
        '''
        return [plot_var.fit_file_name for plot_var in self.plot_vars]

    def update(self, data):
        '''Updates the stored variables from data
        '''
        for i, plot_var in enumerate(self.plot_vars) :
            if not plot_var.fit_file_name in data:
                continue

            value = plot_var.get_value(data)
            self.text[i].set_text(plot_var.get_value_units(value))

            # scale the value for the bar chart
            value = plot_var.get_norm_value(data)
            self.set_bar_value(self.bar[i], value)

    def set_bar_value(self, bar, value):
        '''Sets the value of the bar.
        This virtual function that should be implemented in the derived class
        '''

    def append_text(self, i):
        '''Appends text to the ith bar
        This virtual function that should be implemented in the derived class
        '''

    def make_bars(self, names):
        '''Make bar from a list of names
        This virtual function that should be implemented in the derived class
        '''

class BarPlot(BarPlotBase):
    '''Vertical Bar Plot
    '''
    txt_dx = -0.12
    txt_dy = 0.05
    def __init__(self, plot_vars, axes):
        BarPlotBase.__init__(self, plot_vars, axes)
        self.axes.set_ylim(0.0, 1.0)
        self.axes.get_yaxis().set_visible(False)

    def make_bars(self, names):
        '''Make vertical bars from list of names
        '''
        self.bar = self.axes.bar(x = names, height = [0.0]*len(names), alpha=self.alpha)

    def set_bar_value(self, bar, value):
        '''Set the bar height
        '''
        bar.set_height(value)

    def append_text(self, i):
        '''Add text to the bar
        '''
        plot_var = self.plot_vars[i]
        self.text.append(self.axes.text(i+self.txt_dx, self.txt_dy,
                                        plot_var.get_value_units(0.0)))

class HBarPlot(BarPlotBase):
    '''Horizontal Bar Plot
    '''
    txt_dx = 0.01
    txt_dy = -0.28
    def __init__(self, plot_vars, axes):
        BarPlotBase.__init__(self, plot_vars, axes)
        self.axes.set_xlim(0.0, 1.0)
        self.axes.get_xaxis().set_visible(False)

    def make_bars(self, names):
        '''Make horizontal bars from list of names
        '''
        self.bar = self.axes.barh(y = names, width = [0.0]*len(names), alpha=self.alpha)

    def set_bar_value(self, bar, value):
        '''Set the bar lenth
        '''
        bar.set_width(value)

    def append_text(self, i):
        '''Add text to the bar
        '''
        plot_var = self.plot_vars[i]
        self.text.append(self.axes.text(self.txt_dx, i+self.txt_dy,
                                         plot_var.get_value_units(0.0)))

class ElevationPlot(PlotBase):
    '''Plot showing the activity elvation trace
    '''
    # vscale: Scale the elevation up by this much relative to the distance
    def __init__(self, axes, vertical_scale = 5.0):
        PlotBase.__init__(self)
        self.axes = axes
        self.vertical_scale = vertical_scale

        self.axes.set_axis_off()
        for side in ['top','bottom','left','right']:
            self.axes.spines[side].set_visible(False)

        self.axes.set_aspect(self.vertical_scale)
        self.axes.tick_params(axis='both', which='both',length=0)

    def draw_base_plot(self, dist_list, elev_list):
        '''Draw full elevation profile on the background
        '''
        self.axes.plot(dist_list, elev_list, marker='.', markersize=self.pms,alpha=self.alpha)

    def update(self,data):
        '''Draw the current elvation profile point
        '''
        if 'distance' in data and 'altitude' in data:
            self.axes.plot(data['distance'], data['altitude'], color=self.highlight_color,
                           marker='.', markersize=self.pms)

    @property
    def fit_file_names(self):
        '''Returns list of fit file record variable names requred for this plot
        '''
        return [ 'distance', 'altitude' ]

class MapPlot(PlotBase):
    '''Plot show the activity position trace
    '''
    def __init__(self, axes, projection):
        PlotBase.__init__(self)
        self.axes = axes
        self.axes.outline_patch.set_visible(False)
        self.axes.background_patch.set_visible(False)
        self.projection = projection

    def draw_base_plot(self, long_list, lati_list):
        '''Draw full activity trace on the background
        '''
        lon_min=min(long_list)
        lon_max=max(long_list)
        lat_min=min(lati_list)
        lat_max=max(lati_list)
        dlon = lon_max-lon_min
        dlat = lat_max-lat_min
        extent=[ lon_min-0.02*dlon,
            lon_max+0.05*dlon,
            lat_min-0.02*dlat,
            lat_max+0.02*dlat ]
        self.axes.set_extent(extent, crs=self.projection)
        self.axes.scatter(long_list, lati_list, s=self.sms,marker='.',
                          alpha=self.alpha, transform=self.projection)

    def get_height_over_width(self):
        '''Calculate and return the map height to width ratio
        '''
        ymin,ymax = self.axes.get_ylim()
        delta_y=ymax-ymin
        xmin,xmax = self.axes.get_xlim()
        delta_x=xmax-xmin
        return delta_y/delta_x

    def update(self,data):
        '''Draw the next data point
        '''
        if 'position_lat' in data and 'position_long' in data:
            self.axes.scatter(data['position_long'], data['position_lat'],
                              color=self.highlight_color,marker='.', s=self.sms,
                              alpha=self.alpha, transform=self.projection)

    @property
    def fit_file_names(self):
        '''Returns list of fit file record variable names requred for this plot
        '''
        return ['position_lat', 'position_long']
