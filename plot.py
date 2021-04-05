from datetime import datetime

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
    def setValue(self,data):
        if not TextLine.setValue(self, data):
            return False

        self.value = datetime.fromtimestamp(int(self.value))
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
        self._addTextLine( TSTextLine( self.axes,'timestamp', '{}' ))
        self._addTextLine( TextLine( self.axes,'temperature', '{:.0f} ℃'))
        self._addTextLine( TextLine( self.axes,'altitude',    '{:.0f} m'))
        self._addTextLine( TextLine( self.axes,'heart_rate',  '{:.0f} BPM'))
        self._addTextLine( TextLine( self.axes,'distance',  '{:.1f} km', scale=0.001))
        #self._addTextLine( TextLine( self.axes,'gradient',  '{:.1f}%'))
        self._addTextLine( CounterTextLine( self.axes, 'lap', 'Lap {}'))

    def _addTextLine(self, textLine ):
        nlines = len(self.textLines)
        textLine.x = self.x + nlines*self.dx
        textLine.y = self.y + nlines*self.dy
        self.textLines.append( textLine )

    @staticmethod
    def ffNames():
        """
        Return list of fit file record variable names requred for this plot
        """
        return [ 'temperature', 'altitude', 'heart_rate', 'gradient', 'distance']

    def update(self, data):
        for txtLine in self.textLines:

            if not txtLine.setValue( data ):
                continue

            txtLine.setAxesText()

class ElevationPlot:
    dscale = 0.001
    def __init__(self, distArr, elevArr, axes ):
        self.axes = axes
        self.axes.plot([ self.dscale*d for d in distArr],elevArr)
        self.axes.set_xlabel('km')
        self.axes.set_ylabel('m')

    def update(self,data):
        self.axes.plot(self.dscale*data['distance'],data['altitude'],'r.')

    @staticmethod
    def ffNames():
        return [ 'distance', 'altitude' ]

class MapPlot:
    def __init__(self, latArr, lonArr, axes ):
        self.axes = axes
        self.axes.scatter( latArr, lonArr )

    def update(self,data):
        if 'position_lat' in data and 'position_long' in data:
            self.axes.plot(data['position_long'],data['position_lat'],'r.')
            
    @staticmethod
    def ffNames():
        return [ 'position_lat', 'position_long' ]


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

class BarPlotBase:
    alpha = 0.3
    def __init__(self, plotVars, axes, value = 0.0):
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
    txt_dy = -0.15
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

