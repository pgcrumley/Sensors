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

Capture data from HTU21D attached to Raspberry Pi GPIO pins.
By default CLOCK is pin 5 and DATA is pin 3

Datasheet available from :
https://www.silabs.com/documents/public/data-sheets/Si7021-A20.pdf

Capture data from a HTU21D device attached to a Raspberry Pi and 
periodically send the results to a file.

send data in format of:
  YYYYMMDD_HHMMSS <RPI_ID> <degrees C> <Rel Humidity>
"""

from datetime import datetime
import time

import HTU21D

DEBUG = 0
if DEBUG:
    import sys

SAMPLE_INTERVAL_IN_SECONDS = 60
DATETIME_FORMAT = '%Y%m%d_%H%M%S'
RESULT_FILENAME_BASE = '/opt/Sensors/logs/HTU21D_'

#
# main
#
if __name__ == '__main__':
    
    # get RPi ID
    RPI_ID = 'ID_TBD'
    with open('/proc/cpuinfo') as f:
        for line in f:
            info = line.split()
            if len(info) > 0 and 'Serial' == info[0]:
                RPI_ID = info[2]
                break
    
    if DEBUG:
        print('RPI_ID = "{}"'.format(RPI_ID), file=sys.stderr)
    
    data_name = RESULT_FILENAME_BASE + RPI_ID

    sensor = HTU21D.HTU21D()
    chip_type = sensor.get_chip_type()
    
    with open(data_name, 'a') as output:
        next_sample_time = time.time()
        while True:

            when = datetime.now().strftime(DATETIME_FORMAT)
            temp,rh = sensor.retrieve_temp_humidity()    
            result = '{} {} {:.3f} {:.3f}\n'.format(when, RPI_ID, 
                                                    temp, rh)
            output.write(result)
            output.flush()
            
            next_sample_time = next_sample_time + SAMPLE_INTERVAL_IN_SECONDS
            delay_time = next_sample_time - time.time()
            if DEBUG:
                print('delay_time = {}'.format(delay_time), file=sys.stderr, flush=True)
        
            if 0 < delay_time:  # don't sleep if already next sample time
                time.sleep(delay_time)

