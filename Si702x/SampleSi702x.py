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

Capture data from a Si702x device attached to a Raspberry Pi and 
periodically send the results to a file.

send data in format of:
  YYYYMMDD_HHMMSS <RPI_ID> <degrees C> <Rel Humidity>

"""

from datetime import datetime
import time

import Si702x

DEBUG = 0
if DEBUG:
    import sys

SAMPLE_INTERVAL_IN_SECONDS = 60
DATETIME_FORMAT = '%Y%m%d_%H%M%S'
RESULT_FILENAME_BASE = '/opt/Sensors/logs/'

#
# main
#
if __name__ == '__main__':
    
    sensor = Si702x.Si702x()
    if DEBUG:
        print('sensor.get_chip_eid() = "{}"'.format(sensor.get_chip_eid()), file=sys.stderr)

    chip_type = sensor.get_chip_type()
    chip_eid = sensor.get_chip_eid()

    data_name = RESULT_FILENAME_BASE + chip_type + '_' + chip_eid
    
    next_sample_time = time.time()
    while True:
        with open(data_name, 'a') as output:
            when = datetime.now().strftime(DATETIME_FORMAT)
            temp,rh = sensor.retrieve_temp_humidity_with_retries()    
            result = '{} {} {:.3f} {:.3f}\n'.format(when, chip_eid, 
                                                    temp, rh)
            output.write(result)
            output.flush()
            
            next_sample_time = next_sample_time + SAMPLE_INTERVAL_IN_SECONDS
            delay_time = next_sample_time - time.time()
            if DEBUG:
                print('delay_time = {}'.format(delay_time), file=sys.stderr, flush=True)
        
            if 0 < delay_time:  # don't sleep if already next sample time
                time.sleep(delay_time)

