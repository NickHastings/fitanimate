''' Manange and process fit file data to be displayed
'''

import fitparse

def safe_data(data, name=None):
    '''Protect against invalid input data
    '''
    if data is None:
        return None

    if name and name in ['position_lat','position_long']:
        # Divide by 2^32/360.
        return data/11930464.7

    try:
        float_data = float(data)

    except TypeError:
        return None

    return float_data


class DataSet:
    ''' Container Class for fitfile data
    '''
    # Only iterpolated these fast changing variables
    do_interpolate =  ['power','speed','cadence']
    def __init__(self):
        self.data = []
        self.int_data = []
        self.fps = 10

    def add_data(self, data):
        '''Add a data record
        '''
        if len(self.data) < 1:
            self.data.append(data)
            return True

        t_prev = int(self.data[-1]['timestamp'])
        delta_time = int(data['timestamp'])-t_prev
        if delta_time == 0:
            return True

        if delta_time<0:
            print('Negative time delta! Not adding data')
            return False

        self.data.append(data)
        return True

    def interpolate_data(self):
        '''Interpolate fast changing data to allow smooth animation
        '''
        for i in range(len(self.data)-1):
            data0 = self.data[i]
            data1 = self.data[i+1]
            self.int_data.append(data0)
            for j in range(1,self.fps):
                dnew = {}
                for feild in data0.keys():
                    if feild in data1 and feild in self.do_interpolate:
                        dnew[feild] = self._interpolate(data0[feild],data1[feild],j)
                        dnew['interpolated'] = True

                self.int_data.append(dnew)

    def number_of_frames(self):
        '''Return the total number of image frames
        '''
        return self.fps * len(self.data)

    def _interpolate(self, value0, value1, step):
        '''Calculate and return an inerpolated data point
        '''
        return ((self.fps-step)*value0 + step*value1)/float(self.fps)

    def dump(self):
        '''Write all the data to stdout
        '''
        for data in self.data:
            print(data)


def pre_pocess_data(infile, record_names, timeoffset=None) -> DataSet:
    '''Read a fitfile and return a DataSet of data with the request records
    '''
    dataset = DataSet()
    fit_file = fitparse.FitFile(infile)

    for message in fit_file.get_messages(['record','lap','event']):
        data = {}
        message_name = message.as_dict()['name']
        if message_name == 'record':
            data['timestamp'] = int(message.get_value('timestamp').timestamp())
            if timeoffset:
                data['timestamp'] += timeoffset

            for feild in record_names:
                datum = safe_data(message.get_value(feild), feild)
                if not datum is None:
                    data[feild] = datum

            success = dataset.add_data(data)
            if not success:
                print('Problem adding data point. Not adding any more data.')
                dataset.interpolate_data()
                return dataset

        elif message_name == 'lap' and len(dataset.data)>0:
            # Just append to the previous data
            dataset.data[-1]['lap'] = True

        elif (message_name == 'event' and
              message.get_raw_value('gear_change_data') and
              len(dataset.data)>0):
            gears = f"{message.get_value('front_gear')}-{message.get_value('rear_gear')}"
            dataset.data[-1]['gears'] = gears

    dataset.interpolate_data()
    return dataset

def run(data, _, plots):
    '''Update the plots with the data
    '''
    for plot in plots:
        plot.update(data)

class DataGen():
    '''Yeilds to first argument of run()
    '''
    def __init__(self, data_set):
        self.data_set = data_set

        self.altitude_list = []
        self.distance_list = []

        self.lati_list = []
        self.long_list = []

        for data in data_set.data:
            if 'altitude' in data and 'distance' in data:
                self.altitude_list.append(data['altitude'])
                self.distance_list.append(data['distance'])

            if 'position_lat' in data and 'position_long' in data:
                self.lati_list.append(data['position_lat'])
                self.long_list.append(data['position_long'])

        if len(self.altitude_list)>0:
            self.make_gradient_data()

    def make_gradient_data(self):
        '''
        Smooth second-by-seceond altitude and distance data to get
        better gradient estimates

        Easier to do this here instead of in preProcessData()
        since we now have the altitude and distance arrrays
        '''

        altitude = []
        distance = []
        window_size = 5
        i = 0
        if len(self.altitude_list) != len(self.distance_list):
            print('Warning missmatch in distance and altitude data.')
            return

        while i < len(self.altitude_list) - window_size + 1:
            altitude.append(sum(self.altitude_list[i : i + window_size]) / window_size)
            distance.append(sum(self.distance_list[i : i + window_size]) / window_size)
            i+=1

        altitude_last=None
        distance_last=None
        gradient_last=0.0
        gradient=0.0
        gradient_list = []
        for i, _ in enumerate(altitude):
            if (not distance_last is None) and (not altitude_last is None):
                delta_distance = distance[i]-distance_last
                delta_altitude = altitude[i]-altitude_last
                if delta_distance != 0.0:
                    gradient = 100.0*delta_altitude/delta_distance

                else:
                    gradient = gradient_last

                gradient_list.append(gradient)

            distance_last = distance[i]
            altitude_last = altitude[i]
            gradient_last = gradient

        # Will be window_size-1 fewer entries. Pad the start.
        for i in range(window_size):
            gradient_list.insert(0,gradient_list[0])

        # Now insert the gradient data
        i = 0
        for data in self.data_set.data:
            if 'altitude' in data and 'distance' in data:
                if i >= len(gradient_list):
                    print('Warning grad array size data missmatch.')
                    break

                data['grad'] = gradient_list[i]
                i+=1

    def __call__(self):
        for data in self.data_set.int_data:
            yield data
