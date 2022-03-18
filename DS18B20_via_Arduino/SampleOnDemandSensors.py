#!/usr/bin/env python3
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


Capture data from DS18B20 sensors which are attached to Arduinos accessed by
serial ports

It is assumed this code runs as root and by default will place the data it
collects in 
  /opt/sensors/DS18B20-via-Arduinos.log
the file is created if it does not exist and is appended if it does exist.
There are no provisions to prune or manage the file size.

By default the sensors are sampled about every 60 seconds.

Data in the file is of the form:
  <Timestamp> <Device> <ID> <degrees C>

The program looks for serially attached Arduino devices on '/dev/ttyUSB*', and 
'/dev/ttyACM*'.  The line rate is 115200 baud.  The Arduino code can be found
in the same github which held this code.
  
The program takes the following command-line arguments:
  --help               print a help message
  -p, --ports          ports which holds Arduino with sensors (comma separated)
  -l, --log_filename   filename for the log file
  -i, --interval       the sampling period in seconds
  -d, --debug          turn on debugging
  
Note:  If this program finds no active USB serial ports to sample it will 
happily run, create/append to the log file and monitor nothing.
"""

import argparse
import datetime
import os
import sys
import time

import DS18B20_OnDemand_via_Arduino_Controller

DEBUG = 0

DEFAULT_SAMPLE_INTERVAL_IN_SECONDS = 60 * 10  # every 10 minutes by default
OUTPUT_FORMAT = '{} {} {} {}\n'
DEFAULT_LOG_FILE_NAME = '/opt/Sensors/logs/DS18B20-via-Arduinos.log'

#
# main
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture and log data from Arduino-attached sensors via serial ports.")
    parser.add_argument("-d", "--debug", help="turn on debugging", action="store_true")
    default_ports_list = ','.join(DS18B20_OnDemand_via_Arduino_Controller.determine_ports())
    parser.add_argument("-p", "--ports", help="ports which hold Arduino with sensors (comma separated)",
                        default=default_ports_list)
    parser.add_argument("-l", "--log_filename", help="file to log data, create or append", 
                        default=DEFAULT_LOG_FILE_NAME)
    parser.add_argument("-i", "--interval", help="how often to sample sensors in seconds", 
                        default=DEFAULT_SAMPLE_INTERVAL_IN_SECONDS)
    args = parser.parse_args()

    if (args.debug):
        DEBUG = 1
        print('turned on DEBUG from command line.',
              file=sys.stderr, flush=True)

    log_filename = args.log_filename
    sample_interval_in_seconds = int(args.interval)
    ports=args.ports
    port_name_list = ports.split(',')

    if DEBUG:
        print(f'log_filename = {log_filename}',
              file=sys.stderr, flush=True)
        print(f'sample_interval_in_seconds = {sample_interval_in_seconds}',
              file=sys.stderr, flush=True)
        print(f'ports = "{ports}"',
              file=sys.stderr, flush=True)

        print(f'port_name_list = {port_name_list}',
              file=sys.stderr, flush=True)

    if sample_interval_in_seconds < 0:
        sample_interval_in_seconds = DEFAULT_SAMPLE_INTERVAL_IN_SECONDS
        if DEBUG:
            print(f'negative sample interval set to {sample_interval_in_seconds}',
                  file=sys.stderr, flush=True)
    
    ##
    ## done parsing command line
    ##

    # get serial port access for each serial device
    controller_map = DS18B20_OnDemand_via_Arduino_Controller.find_DS18B20_device(port_name_list)
    if DEBUG:
        print(f'controller_map = "{controller_map}"',
              file=sys.stderr, flush=True)


    os.makedirs(os.path.dirname(log_filename), exist_ok=True)
    with open(log_filename, 'a') as output:
        next_sample_time = time.time()
        while True:
            for c in controller_map.keys():
                when = datetime.datetime.now(datetime.timezone.utc).isoformat()
                samples = controller_map[c].retrieve_temperatures()
                for s in samples.keys():
                    if DEBUG:
                        print(f'sample at {when} {controller_map[c].get_type()} {s} {samples[s]}  ')
                    result = OUTPUT_FORMAT.format(when,
                                                  controller_map[c].get_type(),
                                                  s,
                                                  samples[s])
                    output.write(result)
            output.flush()
            
            next_sample_time = next_sample_time + sample_interval_in_seconds
            delay_time = next_sample_time - time.time()
            if DEBUG:
                print(f'delay_time = {delay_time}',
                      file=sys.stderr, flush=True)
        
            if 0 < delay_time:  # don't sleep if already next sample time
                time.sleep(delay_time)

