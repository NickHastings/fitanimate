import fitparse

def safeData(d,name=None):
    if d is None:
        return None

    if name and name in ['position_lat','position_long']:
        # Divide by 2^32/360.
        return d/11930464.7

    try:
        fd = float(d)
    except TypeError:
        return None

    return fd


class DataSet:
    # Only iterpolated these fast changing variables
    do_interpolate =  ['power','speed','cadence']
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
                    if f in d1 and f in self.do_interpolate:
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


def prePocessData( infile, record_names, timeoffset=None ):
    dataset = DataSet()
    ff = fitparse.FitFile( infile )

    for message in ff.get_messages(['record','lap','event']):
        data = {}
        message_name = message.as_dict()['name']
        if message_name == 'record':
            data['timestamp'] = int(message.get_value('timestamp').timestamp())
            if timeoffset:
                data['timestamp'] += timeoffset

            for f in record_names:
                d = safeData( message.get_value(f), f )
                if not (d is None):
                    data[f] = d

            ok = dataset.addData(data)
            if not ok:
                print( 'Problem adding data point. Not adding any more data.')
                dataset.interpolateData()
                return dataset

        elif message_name == 'lap' and len(dataset.data)>0:
            # Just append to the previous data
            dataset.data[-1]['lap'] = True

        elif ( message_name == 'event' and
               message.get_raw_value('gear_change_data') and
               len(dataset.data)>0 ):
            gears = '{}-{}'.format(message.get_value('front_gear'),
                                   message.get_value('rear_gear') )
            dataset.data[-1]['gears'] = gears

    dataset.interpolateData()
    return dataset

def run(data,fig,plots):
    for plot in plots:
        plot.update(data)

# Yeilds to first argument of run()
class DataGen():
    def __init__(self, dataSet ):
        self.dataSet = dataSet

        self.aArr = []
        self.dArr = []

        self.latArr = []
        self.lonArr = []

        for data in dataSet.data:
            if 'altitude' in data and 'distance' in data:
                self.aArr.append(data['altitude'])
                self.dArr.append(data['distance'])

            if 'position_lat' in data and 'position_long' in data:
                self.latArr.append(data['position_lat'])
                self.lonArr.append(data['position_long'])

        if len(self.aArr)>0:
            self.mkGradData()

    def mkGradData(self):
        # Smooth second-by-seceond altitude and distance data to get
        # better gradient estimates
        #
        # Easier to do this here instead of in preProcessData()
        # since we now have the altitude and distance arrrays

        a = []
        d = []
        window_size = 5
        i = 0
        if len(self.aArr) != len(self.dArr):
            print( 'Warning missmatch in distance and altitude data.')
            return

        while i < len(self.aArr) - window_size + 1:
            a.append(sum(self.aArr[i : i + window_size]) / window_size)
            d.append(sum(self.dArr[i : i + window_size]) / window_size)
            i+=1

        alast=None
        dlast=None
        glast=0.0
        grad=0.0
        g = []
        for i in range(len(a)):
            if not (dlast is None) and not(alast is None):
                dd = d[i]-dlast
                da = a[i]-alast
                if dd != 0.0:
                    grad = 100.0*da/dd
                else:
                    grad = glast
                g.append(grad)
            dlast = d[i]
            alast = a[i]
            glast = grad

        # Will be window_size-1 fewer entries. Pad the start.
        for i in range(window_size):
            g.insert(0,g[0])

        # Now insert the gradient data
        i = 0
        for data in self.dataSet.data:
            if 'altitude' in data and 'distance' in data:
                if i >= len(g):
                    print('Warning grad array size data missmatch.')
                    break

                data['grad'] = g[i]
                i+=1

    def __call__(self):
        for data in self.dataSet.intData:
            yield data
