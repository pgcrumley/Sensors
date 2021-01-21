#!/usr/bin/python3
"""
MIT License

Copyright (c) 2017, 2020 Paul G Crumley

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
  <Timestamp> <Device> <RPI_ID> <degrees C> <Rel Humidity>

"""

import argparse
import datetime
import time

import Si702x

DEBUG = 0
if DEBUG:
    import sys

DEFAULT_SAMPLE_INTERVAL_IN_SECONDS = 60 * 10
OUTPUT_FORMAT = '{} {} {} {:.3f} {:.3f}\n'
RESULT_FILENAME_BASE = '/opt/Sensors/logs/'

#
# main
#
if __name__ == '__main__':
    
    parser = argparse.ArgumentParser(description="Capture and log data from a Si702x sensor.")
    parser.add_argument("-d", "--debug", help="turn on debugging", action="store_true")
    parser.add_argument("-i", "--interval", help="how often to sample sensors in seconds", 
                        default=DEFAULT_SAMPLE_INTERVAL_IN_SECONDS)
    parser.add_argument("-s", "--id_suffix", help="apply a suffix to the id", 
                        default="")
    args = parser.parse_args()

    if (args.debug):
        DEBUG = 1
        print('turned on DEBUG from command line.',
              file=sys.stderr, flush=True)

    id_suffix = args.id_suffix
    sample_interval_in_seconds = int(args.interval)
    
    if DEBUG:
        print('id_suffix = "{}"'.format(id_suffix),
              file=sys.stderr, flush=True)
        print('sample_interval_in_seconds = {}'.format(sample_interval_in_seconds),
              file=sys.stderr, flush=True)

    if sample_interval_in_seconds < 0:
        sample_interval_in_seconds = 0
        if DEBUG:
            print('negative sample interval set to 0',
                  file=sys.stderr, flush=True)
    
    ##
    ## done parsing command line
    ##

    sensor = Si702x.Si702x()
    chip_type = sensor.get_chip_type()
    id_ = sensor.get_chip_eid()
    if DEBUG:
        print('sensor.get_chip_eid() = "{}":"{}"'.format(chip_type, id_),
              file=sys.stderr)

    if '' != id_suffix:
        id_ = id_ + '_' + id_suffix
    if DEBUG:
        print('id to use = "{}"'.format(id_),
              file=sys.stderr)


    data_name = RESULT_FILENAME_BASE + chip_type + '_' + id_
    
    with open(data_name, 'a') as output:
        next_sample_time = time.time()
        while True:
            when = datetime.datetime.now(datetime.timezone.utc).isoformat()
            temperature,rh = sensor.retrieve_temp_humidity_with_retries()    
            result = OUTPUT_FORMAT.format(when,
                                          chip_type,
                                          id_, 
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
