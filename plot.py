from datetime import datetime
import matplotlib.pyplot as plt

class TextLine:
    def __init__(self, axes, field_name, txt_format, x=0.0, y=0.0, scale=None ):
        self.axes = axes
        self.field_name = field_name
        self.txt_format = txt_format
        self.x = x
        self.y = y
        self.value = 0
        self.scale = scale

        self.axes_text = None

    def setAxesText(self):
        if not self.axes_text:
            self.axes_text = self.axes.text( self.x, self.y, self.txt_format.format( self.value ) )
            return

        self.axes_text.set_text( self.txt_format.format( self.value ) )

    def setValue(self, data ):
        # Don't update the text data if it is just a subsecond interpolation
        if 'interpolated' in data and data['interpolated']:
            return False

        if not (self.field_name in data):
            return False

        self.value = data[self.field_name]
        if self.scale:
            self.value *= self.scale

        return True

class CounterTextLine(TextLine):
    def __init__(self,axes, field_name, txt_format, x=0.0, y=0.0 ):
        TextLine.__init__(self, axes, field_name, txt_format, x, y )

    def setValue(self, data):
        if self.value == 0 or self.field_name in data:
            self.value += 1
            return True

        return False

class TSTextLine(TextLine):
    def __init__(self,axes, field_name, txt_format, x=0.0, y=0.0,
                 timeformat='%H:%M:%S' ):
        TextLine.__init__(self, axes, field_name, txt_format, x, y )
        self.timeformat = timeformat

    def setValue(self,data):
        if not TextLine.setValue(self, data):
            return False

        self.value = datetime.fromtimestamp(int(self.value)).strftime(
            self.timeformat)
        return True


class TextPlot:
    def __init__(self, axes, x=-0.11, y=0.92, dx=0.0, dy=-0.08):
        self.x = x
        self.y = y
        self.dx = dx
        self.dy = dy
        self.axes = axes
        self.axes.set_axis_off()

        self.textLines = []
    def addTextLine(self, textLine ):

        xmin,xmax = self.axes.get_xlim()
        dx=xmax-xmin
        ymin,ymax = self.axes.get_ylim()
        dy=ymax-ymin

        nlines = len(self.textLines)
        textLine.x = xmin + dx*(self.x + nlines*self.dx)
        textLine.y = ymin + dy*(self.y + nlines*self.dy)
        self.textLines.append( textLine )

    @property
    def ffNames(self):
        """
        Return list of fit file record variable names requred for this plot
        """
        return []

    def update(self, data):
        for txtLine in self.textLines:

            if not txtLine.setValue( data ):
                continue

            txtLine.setAxesText()

class RideText(TextPlot):
    def __init__(self, axes, x=-0.11, y=0.92, dx=0.0, dy=-0.08):
        TextPlot.__init__(self, axes, x, y, dx, dy )
        self.addTextLine( TSTextLine( self.axes,'timestamp', '{}' ))
        self.addTextLine( TextLine( self.axes,'temperature', '{:.0f} ℃'))
        self.addTextLine( TextLine( self.axes,'heart_rate',  '{:.0f} BPM'))
        self.addTextLine( CounterTextLine( self.axes, 'lap', 'Lap {}'))
        self.addTextLine( TextLine( self.axes, 'gears', '{}'))

    @property
    def ffNames(self):
        """
        Return list of fit file record variable names requred for this plot
        """
        return [ 'temperature', 'altitude', 'heart_rate', 'gradient', 'distance']


# Information about a fitfile record to plot
class PlotVar:
    def __init__(self, ffname, name, units, maxValue, minValue=0.0, scaleFactor=1.0, offSet=0.0):
        self.ffname = ffname # name in fit file
        self.name = name
        self.units = units
        self.maxValue = maxValue
        self.minValue = minValue
        self.scaleFactor = scaleFactor # Multiply ff data by this
        self.offSet = offSet # Add this to ff data


    def getNameLabel( self ):
        return '{} ({})'.format(self.name,self.units)

    def getNormValue( self, data ):
        """ Between 0 and 1"""
        return (self.getValue(data) - self.offSet)/(self.maxValue-self.minValue)

    def getValue(self, data ):
        val = data[self.ffname]
        return val*self.scaleFactor + self.offSet

    def getValueUnits(self, value ):
        return '{:.0f} {:}'.format(value,self.units)

class PlotBase:
    alpha = 0.3

    # Nominal marker sizes are for 3800x2160 (4K) at 100 DPI
    nom_dpi = 100.0
    nom_size = [3840/nom_dpi, 2160/nom_dpi]

    # Normal plot marker size. Diameter in pixels.
    nom_pms = 12

    def __init__(self):
        f = plt.gcf()
        dpi = f.dpi
        size = f.get_size_inches()

        # Scale by size and DPI
        self.pms = self.nom_pms * size[0]/self.nom_size[0] * dpi/self.nom_dpi

        # area is pi*r^2
        self.sms = 3.14159*(0.5*self.pms)**2

class BarPlotBase(PlotBase):
    def __init__(self, plotVars, axes, value = 0.0):
        PlotBase.__init__(self)
        self.plotVars = plotVars
        self.axes = axes
        self.axes.autoscale_view('tight')
        self.axes.set_axis_on()
        self.axes.tick_params(axis=u'both', which=u'both',length=0)
        for s in ['top','bottom','left','right']:
            self.axes.spines[s].set_visible(False)

        self.makeBar( [ pv.name for pv in self.plotVars ] )

        self.text = []
        for i in range(len(self.plotVars)):
            pv = self.plotVars[i]
            self.appendText(i)


    @property
    def ffNames(self):
        """
        Return list of fit file variable names requred for this plot
        """
        return [ pv.ffname for pv in self.plotVars ]
    def update(self, data ):
        for i in range(len(self.plotVars)) :
            pv = self.plotVars[i]
            if not (pv.ffname in data):
                continue

            value = pv.getValue(data)
            self.text[i].set_text( pv.getValueUnits(value) )

            # scale the value for the bar chart
            value = pv.getNormValue(data)
            self.setBarValue( self.bar[i], value )

    def setBarValue(self, bar, value ):
        pass

    def appendText(self, i ):
        pass

    def makeBars(self, names):
        pass

class BarPlot(BarPlotBase):
    txt_dx = -0.12
    txt_dy = 0.05
    def __init__(self, plotVars, axes, value = 0.0):
        BarPlotBase.__init__(self, plotVars, axes, value )
        self.axes.set_ylim( 0.0, 1.0 )
        self.axes.get_yaxis().set_visible(False)

    def makeBar(self, names ):
        self.bar = self.axes.bar( x = names, height = [0.0]*len(names), alpha=self.alpha )

    def setBarValue(self, bar, value ):
        bar.set_height( value )

    def appendText(self, i ):
        pv = self.plotVars[i]
        self.text.append( self.axes.text( i+self.txt_dx, self.txt_dy, pv.getValueUnits(0.0) ) )

class HBarPlot(BarPlotBase):
    txt_dx = 0.01
    txt_dy = -0.28
    def __init__(self, plotVars, axes, value = 0.0 ):
        BarPlotBase.__init__(self, plotVars, axes, value )
        self.axes.set_xlim( 0.0, 1.0 )
        self.axes.get_xaxis().set_visible(False)

    def makeBar(self, names ):
        self.bar = self.axes.barh( y = names, width = [0.0]*len(names), alpha=self.alpha )

    def setBarValue(self, bar, value ):
        bar.set_width( value )

    def appendText(self, i ):
        pv = self.plotVars[i]
        self.text.append( self.axes.text( self.txt_dx, i+self.txt_dy, pv.getValueUnits(0.0) ) )

class ElevationPlot(PlotBase):
    vScale = 5.0 # Scale the elevation up by this much relative to the distance
    defaultElevMax = 500.0
    def __init__(self, distArr, elevArr, axes ):
        PlotBase.__init__(self)
        self.axes = axes

        self.axes.set_axis_off()
        for s in ['top','bottom','left','right']:
            self.axes.spines[s].set_visible(False)

        self.axes.set_aspect(self.vScale)
        self.axes.tick_params(axis=u'both', which=u'both',length=0)
        self.axes.plot(distArr,elevArr,'o',markersize=self.pms,alpha=self.alpha)
        #self.axes.set_xlabel('km')
        #self.axes.set_ylabel('m')

        # After drawing he plot so we can get the correct x,y limits
        self.textPlot = TextPlot(self.axes, x=0.8, y=0.8, dy=-0.3)
        self.textPlot.addTextLine( TextLine( self.axes, 'altitude','{:.0f} m'))
        self.textPlot.addTextLine( TextLine( self.axes, 'grad', '{:5.1f}%'))

    def update(self,data):
        self.textPlot.update(data)
        if 'distance' in data and 'altitude' in data:
            self.axes.plot(data['distance'],data['altitude'],'ro',markersize=self.pms)

    @property
    def ffNames(self):
        return [ 'distance', 'altitude' ]

class MapPlot(PlotBase):
    def __init__(self, lonArr, latArr, axes, projection ):
        PlotBase.__init__(self)
        self.axes = axes
        self.axes.outline_patch.set_visible(False)
        self.axes.background_patch.set_visible(False)
        self.projection = projection
        lon_min=min(lonArr)
        lon_max=max(lonArr)
        lat_min=min(latArr)
        lat_max=max(latArr)
        dlon = lon_max-lon_min
        dlat = lat_max-lat_min
        b=[ lon_min-0.02*dlon,
            lon_max+0.05*dlon,
            lat_min-0.02*dlat,
            lat_max+0.02*dlat ]
        self.axes.set_extent( b, crs=self.projection )
        self.axes.scatter( lonArr, latArr,s=self.sms,alpha=self.alpha,transform=self.projection )

        # After drawing he plot so we can get the correct x,y limits
        self.textPlot = TextPlot(self.axes, x=0.95, y=0.95, dy=-0.3)
        self.textPlot.addTextLine( TextLine( self.axes,'distance', '{:.1f} km', scale=0.001))

    def update(self,data):
        self.textPlot.update(data)
        if 'position_lat' in data and 'position_long' in data:
            self.axes.scatter(data['position_long'],data['position_lat'],color='red',marker="o",s=self.sms,alpha=self.alpha,transform=self.projection )

    @property
    def ffNames(self):
        return [ 'position_lat', 'position_long' ]
