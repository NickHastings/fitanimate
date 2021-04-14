import fitparse

def safeData(d,name=None):
    if d is None:
        return 0.0

    if name and name in ['position_lat','position_long']:
        # Divide by 2^32/360.
        return d/11930464.7

    return float(d)

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


def prePocessData( infile, timeoffset=None, record_names = ['power','speed','cadence','heart_rate'] ):
    dataset = DataSet()
    ff = fitparse.FitFile( infile )

    alti0 = None
    dist0 = None
    calc_grad = False

    if 'gradient' in record_names:
        record_names.remove('gradient')
        calc_grad = True
        if not ('altitude' in record_names):
            record_names.append('altitude')
        if not ('distance' in record_names):
            record_names.append('distance')


    for message in ff.get_messages(['record','lap','event']):
        data = {}
        message_name = message.as_dict()['name']
        if message_name == 'record':
            data['timestamp'] = int(message.get_value('timestamp').timestamp())
            if timeoffset:
                data['timestamp'] += timeoffset

            for f in record_names:
                data[f] = safeData( message.get_value(f), f )

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

        if calc_grad:
            if 'altitude' in data:
                alti = data['altitude']
            else:
                alti = None

            if 'distance' in data:
                dist = data['distance']
            else:
                dist = None

            if ( (not alti0 is None) and (not dist0 is None) and
                 (not alti is None) and (not dist is None) ):
                dd=dist-dist0
                if dd>0.1:
                    da=alti-alti0
                    g = 100.0*da/dd
                    data['gradient'] = g

            if (not alti is None) and (not dist is None):
                alti0 = alti
                dist0 = dist

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


    def __call__(self):
        for data in self.dataSet.intData:
            yield data
