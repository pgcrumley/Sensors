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

Capture data from DS18B20 sensors in /sys/bus/w1/devices and 
send data to /opt/sensors/logs/DS18B20.log in format of:
  <Timestamp> <Device> <ID> <degrees C>
  
Datasheet at https://datasheets.maximintegrated.com/en/ds/DS18B20.pdf

"""

import datetime
import time

import DS18B20_Controller

DEBUG = 0
if DEBUG:
    import sys

SAMPLE_INTERVAL_IN_SECONDS = 60 * 10
OUTPUT_FORMAT = '{} DS18B20 {} {:.3f}\n'
RESULT_FILENAME = '/opt/Sensors/logs/DS18B20.log'

#
# main
#
if __name__ == '__main__':
    
    controller = DS18B20_Controller.DS18B20_Controller()

    with open(RESULT_FILENAME, 'a') as output:
        next_sample_time = time.time()
        while True:
            for device_id in controller.get_ids():
                when = datetime.datetime.now(datetime.timezone.utc).isoformat()
                temperature = controller.retrieve_temp(device_id)
                result = OUTPUT_FORMAT.format(when,
                                              device_id,
                                              temperature)
                output.write(result)
                output.flush()
                
            next_sample_time = next_sample_time + SAMPLE_INTERVAL_IN_SECONDS
            delay_time = next_sample_time - time.time()
            if DEBUG:
                print('delay_time = {}'.format(delay_time),
                      file=sys.stderr, flush=True)
        
            if 0 < delay_time:  # don't sleep if already next sample time
                time.sleep(delay_time)
