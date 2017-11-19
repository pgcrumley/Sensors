#!/usr/bin/python3
"""
MIT License

Copyright (c) 2017 Paul G Crumley

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

Capture data from DS18B20 probes attached to Raspberry Pi GPIO_4
"""

import glob
import struct

SENSOR_BASE_FILENAME = '/sys/bus/w1/devices/28-'
SENSOR_BASE_FILENAME_GLOB = SENSOR_BASE_FILENAME + '*'

class DS18B20_Controller:
    """
    This class provides access to multiple DS18B20 devices attached to a Raspberry Pi
    on the default pin (GPIO_4).
    """
    def __init__(self):
        pass
    
    def get_ids(self):
        """
        return a list of IDs for connected DS18B20 devices
        """
        result = []
        for e in glob.glob(SENSOR_BASE_FILENAME_GLOB):
            i = e.replace(SENSOR_BASE_FILENAME, '')
            result.append(i)

        return result
        
    def retrieve_temp(self, i):
        """
        Retrieve the raw data from the DS18B20 with passed id
        and return the temperature in degrees C.
        
        The id is a string with the numeric sensor id value.
        """
        
        sensor_filename = SENSOR_BASE_FILENAME + i + '/w1_slave' 
        with open(sensor_filename) as f:
            raw_line_1 = f.readline().split()
            raw_line_2 = f.readline().split()
            if (len(raw_line_1) != 12):
                raise IOError('format problem with line 1 from "{}"'.format(sensor_filename))
            if (raw_line_1[11] != 'YES'):
                raise IOError('CRC problem with data from "{}"'.format(sensor_filename))
            if (len(raw_line_2) != 10):
                raise IOError('format problem with line 2 from "{}"'.format(sensor_filename))
                
        raw_bytes = bytes([int(raw_line_1[0], 16),int(raw_line_1[1], 16)])
        raw_temp = struct.unpack('<h',raw_bytes)[0]
        temp = raw_temp / 16.0
        
        return temp


#
# main
#
if __name__ == '__main__':
    #
    # do something for a quick test
    #
    controller = DS18B20_Controller()  # take defaults
    ids = controller.get_ids()
    print("DS18B20s found: {}".format(ids))
    for i in ids:
        temp = controller.retrieve_temp(i)
        print ("{} : Temperature :  {} C".format(i, temp))
