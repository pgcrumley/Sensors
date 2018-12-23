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
  -l, --log_filename   filename for the log file
  -i, --interval       the sampling period in seconds
  -d, --debug          turn on debugging
  
Note:  If this program finds no active USB serial ports to sample it will 
happily run, create/append to the log file and monitor nothing.
"""

import argparse
import datetime
import glob
import os
import queue
import serial
import threading
import time

DEBUG = 0
if DEBUG:
    import sys

DEFAULT_SAMPLE_INTERVAL_IN_SECONDS = 60 * 10
OUTPUT_FORMAT = '{} DS18B20 {} {}\n'
DEFAULT_LOG_FILE_NAME = '/opt/Sensors/logs/DS18B20-On-Arduino.log'

SERIAL_FILENAME_GLOBS = ('/dev/ttyUSB*', '/dev/ttyACM*')
PORT_SPEED = 115200
NL = '\n'.encode('UTF-8')  # used to ask Arudino to send sensor data


class writer_thread (threading.Thread):
    '''
    Wait on queue and write/flush each entry that arrives

    Mark ourself as a daemon as we don't have a job when everything else is done
    '''
    def __init__(self, where, queue):
        threading.Thread.__init__(self)
        self.daemon = True
        self.where = where
        self.queue = queue
    def run(self):
        while True:
            data = self.queue.get()
            if data:
                self.where.write(data)
                self.where.flush()
            self.queue.task_done()


class sensor_reader_thread(threading.Thread):
    '''
    Sample the sensors on a serial port and queue up the 
    results to be written to the log

    If a line from the Arduino is not well-formated silently discard the data
    '''
    def __init__(self, write_queue, port):
        threading.Thread.__init__(self)
        self.daemon = True
        self.write_queue = write_queue
        self.port = port
        
    def run(self):
        self.port.write(NL)  # ask for samples
        
        # read first line returned
        split_line = self.port.readline().decode('UTF-8').split()
        if DEBUG:
            print('line: "{}"'.format(split_line))
        # process till a blank line is returned
        while len(split_line) > 0:
            if len(split_line) == 3:
                when = datetime.datetime.now(datetime.timezone.utc).isoformat()
                result = OUTPUT_FORMAT.format(when,
                                              split_line[1].replace('.', ''),
                                              split_line[2])
                self.write_queue.put(result)
            
            # get another line
            split_line = self.port.readline().decode('UTF-8').split()
            if DEBUG:
                print('line:  "{}"'.format(split_line))
        
#
# main
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Capture and log data from Arduino-attached sensors via serial ports.")
    parser.add_argument("-d", "--debug", help="turn on debugging", action="store_true")
    parser.add_argument("-l", "--log_filename", help="file to log data, create or append", default=DEFAULT_LOG_FILE_NAME)
    parser.add_argument("-i", "--interval", help="how often to sample sensors in seconds", default=DEFAULT_SAMPLE_INTERVAL_IN_SECONDS)
    args = parser.parse_args()

    if (args.debug):
        DEBUG = 1
        print('turned on DEBUG from command line.',
              file=sys.stderr, flush=True)

    log_filename = args.log_filename
    sample_interval = int(args.interval)
    
    if DEBUG:
        print('log_filename = {}'.format(log_filename),
              file=sys.stderr, flush=True)
        print('sample_interval = {}'.format(sample_interval),
              file=sys.stderr, flush=True)

    if sample_interval < 0:
        sample_interval = 0
        if DEBUG:
            print('negative sample interval set to 0',
                  file=sys.stderr, flush=True)
    
    ##
    ## done parsing command line
    ##

    serial_devices = []
    for g in SERIAL_FILENAME_GLOBS:
        serial_devices.extend(glob.glob(g))
    if DEBUG:
        print('available devices include:  {}\n'.format(serial_devices),
              file=sys.stderr, flush=True)

    ports = []
    for s in serial_devices:
        ports.append(serial.Serial(s, PORT_SPEED))
    if DEBUG:
        print('ports include:  {}\n'.format(ports),
              file=sys.stderr, flush=True)

    if len(ports) > 0:
        time.sleep(3)  # give the Arduinos time to reset after serial open()
    else:
        if DEBUG:
            print('no ports found to monitor.  continuing...',
                  file=sys.stderr, flush=True)

    os.makedirs(os.path.dirname(log_filename), exist_ok=True)
    with open(log_filename, 'a') as output:
        # set up queue to handle output to single place between many
        # reading threads
        write_queue = queue.Queue(20)
        writer = writer_thread(output, write_queue)
        writer.start()

        next_sample_time = time.time()
        # each time through loop collect data from each port of sensors
        while True:
            threads = []
            for port in ports:
                srt = sensor_reader_thread(write_queue, port)
                threads.append(srt)
                srt.start()
            # wait for everything to complete
            for t in threads:
                t.join()
        
            next_sample_time = next_sample_time + sample_interval
            delay_time = next_sample_time - time.time()
            if DEBUG:
                print('delay_time = {}'.format(delay_time),
                      file=sys.stderr, flush=True)
        
            if 0 < delay_time:  # don't sleep if already past next sample time
                time.sleep(delay_time)

    # will probably never get here but if we do this will cause queue to
    # drain and flush out any remaining data
    write_queue.join()
