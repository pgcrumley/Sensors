#!/usr/bin/python3
"""
MIT License

Copyright (c) 2018 Paul G Crumley

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

@author: pgcrumley@gmail.com

Capture data from a device attached to a Raspberry Pi and 
periodically send the results to a file.

send data in format of:
  <UTC-Timestamp> <Device-Type> <ID> <Data>+

"""

import datetime
import time
from sensor import Sensor

DEBUG = 1
if DEBUG:
    import sys

DEFAULT_SAMPLE_INTERVAL_IN_SECONDS = 60 * 10
OUTPUT_FORMAT = '{} {} {} {}\n' # when what id data+
DEFAULT_FILENAME_FORMAT = '/opt/Sensors/logs/{}_{}.log'


class SamplingDriver:
    """
    Framework to periodically sample a Sensor and append results to a file.
    
    This does not close() the sensor when stop() is called so the same
    sensor can be used after samples are paused.
    """ 
    def __init__(self, 
                 sensor,
                 interval=DEFAULT_SAMPLE_INTERVAL_IN_SECONDS,
                 filename=None
                 ):
        self.__sensor = sensor
        self.__interval = interval
        if filename:
            self.__filename = filename
        else:
            fn = DEFAULT_FILENAME_FORMAT.format(platform.node,
                                                sensor.get_chip_type)
            self.__filename = fn
            
        if DEBUG:
            print('interval: "{}"'.format(self.__interval),
                  file = sys.stderr, flush=True)
            print('filename: "{}"'.format(self.__filename),
                  file = sys.stderr, flush=True)
            print('type: "{}"'.format(self.__sensor.get_sensor_type_name()),
                  file = sys.stderr, flush=True)
            print('id: "{}"'.format(self.__sensor.get_sensor_id()),
                  file = sys.stderr, flush=True)
        self.__running = False


    def collect_samples(self):
        """
        Collect samples and send data to the file till stop() is called.
        """
        self.__running = True
        with open(self.__filename, 'a') as output:
            next_sample_time = time.time()
            while self.__running:
                sensor_name = self.__sensor.get_sensor_type_name()
                sensor_id = self.__sensor.get_sensor_id()
                data = self.__sensor.retrieve_data_string()    
                if DEBUG:
                    print('data: "{}"'.format(data),
                          file = sys.stderr, flush=True)
                when = datetime.datetime.now(datetime.timezone.utc).isoformat()
                result = OUTPUT_FORMAT.format(when,
                                              sensor_name, 
                                              sensor_id, 
                                              data)
                output.write(result)
                output.flush()
                
                next_sample_time = next_sample_time + self.__interval
                delay_time = next_sample_time - time.time()
                if DEBUG:
                    print('delay_time = {}'.format(delay_time),
                          file=sys.stderr, flush=True)
            
                if 0 < delay_time:  # don't sleep if already next sample time
                    time.sleep(delay_time)

    def stop(self):
        """
        Stop collecting samples
        """
        self.__running = False


class test_sensor(Sensor):
    """
    simple Sensor class for testing
    """
    def __init__(self):
        super().__init__('test_sensor', sensor_id = 0)
        
    def close(self):
        super().close()
    
    def get_data_tuple_names(self):
        """
        Return a tuple with the names of the data in the data tuple.
        """
        return (('test_number',))


    def retrieve_data_tuple(self):
        """
        Retrieve data from the sensor and return as a tuple.
        """
        return ((42,))


#
# main
#
if __name__ == '__main__':
    from threading import Thread
    
    sensor = test_sensor()
    driver = SamplingDriver(sensor, 
                            interval=5, 
                            filename='./sampling_driver_test.log')

    # make and start a thread for so collection runs in background
    func = driver.collect_samples
    t = Thread(target=func)
    t.start()

    # collect some samples
    time.sleep(15)

    # tell driver to stop collecting samples
    driver.stop()

    # wait for driver to finish
    t.join()
    
    # we can pause then restart
    time.sleep(15)

    # take more samples    
    func = driver.collect_samples
    t = Thread(target=func)
    t.start()
    time.sleep(15)
    driver.stop()
    t.join()
    
    # close the sensor when finish
    sensor.close()
    
    
    
