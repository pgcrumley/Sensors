#!/usr/bin/python3
"""
MIT License

Copyright (c) 2017, 2022 Paul G Crumley

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
By default CLOCK is board pin 13 and DATA is board pin 11.
The device should be powered at 3.3 volts.

Datasheet available from :
https://www.silabs.com/documents/public/data-sheets/Si7021-A20.pdf

Capture data from a HTU21D device attached to a Raspberry Pi and 
periodically send the results to a file.

send data in format of:
  <Timestamp> <Device> <sensor_id> <degrees C> <Rel Humidity>
"""

import argparse
import datetime
import sys
import time

import HTU21D

DEBUG = 0

DEFAULT_SAMPLE_INTERVAL_IN_SECONDS = 60 * 10
OUTPUT_FORMAT = '{} {} {} {:.3f} {:.3f}\n'
RESULT_FILENAME_BASE = '/opt/Sensors/logs/HTU21D_'

#
# main
#
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description='Capture and log data from a HTU21D sensor.')
    parser.add_argument('-d', '--debug',
                        help='turn on debugging',
                        action='store_true')
    parser.add_argument('-i', '--interval',
                        help='how often to sample sensors in seconds', 
                        type=int,
                        default=DEFAULT_SAMPLE_INTERVAL_IN_SECONDS)
    parser.add_argument('-n', '--name',
                        help='provide a name rather than an id',
                        type=str, 
                        default=None)
    parser.add_argument('-s', '--id_suffix',
                        help='apply a suffix to the id',
                        type=str, 
                        default=None)
    args = parser.parse_args()

    if (args.debug):
        DEBUG = 1
        print('DEBUG enabled.',
              file=sys.stderr,
              flush=True)

    id_suffix = args.id_suffix
    name = args.name
    sample_interval_in_seconds = args.interval
    
    if DEBUG:
        print('sample_interval_in_seconds = {}'.format(sample_interval_in_seconds),
              file=sys.stderr, flush=True)
        print('name = "{}"'.format(name),
              file=sys.stderr, flush=True)
        print('id_suffix = "{}"'.format(id_suffix),
              file=sys.stderr, flush=True)

    if sample_interval_in_seconds < 0:
        sample_interval_in_seconds = DEFAULT_SAMPLE_INTERVAL_IN_SECONDS
        if DEBUG:
            print('negative sample interval set to {}'.format(sample_interval_in_seconds),
                  file=sys.stderr, flush=True)

    ##
    ## done parsing command line
    ##
    
    # get ID based on Raspberry Pi serial number
    sensor_id = 'ID_TBD'
    if name:
        sensor_id=name
    else:
        with open('/proc/cpuinfo') as f:
            for line in f:
                info = line.split()
                if len(info) > 0 and 'Serial' == info[0]:
                    sensor_id = info[2]
                    break

    if id_suffix:
        sensor_id = sensor_id + '_' + id_suffix 
    
    if DEBUG:
        print('sensor_id = "{}"'.format(sensor_id),
              file=sys.stderr)
    
    data_file_name = RESULT_FILENAME_BASE + sensor_id

    sensor = HTU21D.HTU21D()
    
    with open(data_file_name, 'a') as output:
        # start now
        next_sample_time = time.time()

        while True:
            when = datetime.datetime.now(datetime.timezone.utc).isoformat()
            temperature,rh = sensor.retrieve_temp_humidity()
            result = OUTPUT_FORMAT.format(when,
                                          sensor.get_chip_type(), 
                                          sensor_id,
                                          temperature,
                                          rh)
            output.write(result)
            output.flush()
            
            next_sample_time = next_sample_time + sample_interval_in_seconds
            delay_time = next_sample_time - time.time()
            if DEBUG:
                print('delay_time = {}'.format(delay_time),
                      file=sys.stderr, flush=True)
        
            if 0 < delay_time:  # don't sleep if already next sample time
                time.sleep(delay_time)
