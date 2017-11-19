#!/usr/bin/env python3
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

Very simple web server to provide JSON representation of the DS18B20 devices
attached via Arduino devices.
  
Datasheet at https://datasheets.maximintegrated.com/en/ds/DS18B20.pdf

"""

import datetime
import glob
import json
import serial
import sys
import time
from http.server import BaseHTTPRequestHandler, HTTPServer


DEFAULT_LISTEN_ADDRESS = '0.0.0.0'     # respond to request from any address
#DEFAULT_LISTEN_ADDRESS = '127.0.0.1'   # responds to only requests from localhost
DEFAULT_LISTEN_PORT = 18820                 # IP port 18820
#DEFAULT_LISTEN_PORT = TBD                  # Pick some other port if you prefer
DEFAULT_SERVER_ADDRESS = (DEFAULT_LISTEN_ADDRESS, DEFAULT_LISTEN_PORT)

DATETIME_FORMAT = '%Y%m%d_%H%M%S'

SERIAL_FILENAME_GLOBS = ('/dev/ttyUSB*', '/dev/ttyACM*')
PORT_SPEED = 115200
NL = '\n'.encode('UTF-8')  # used to ask Arudino to send sensor data

DEBUG = 0


class DS18B20_on_Arduino_HTTPServer_RequestHandler(BaseHTTPRequestHandler):
    '''
    A subclass of BaseHTTPRequestHandler to provide information about DS18B20 sensors.
    '''
    
    # holds the ports for the DS18B20 devices, will be created when first needed
    __ports = None
    
    def do_GET(self):
        '''
        handle the HTTP GET request
        '''
        # first time through get create the ports list
        if self.__ports is None:
            serial_devices = []
            for g in SERIAL_FILENAME_GLOBS:
                serial_devices.extend(glob.glob(g))
            if DEBUG:
                print('available devices include:  {}\n'.format(serial_devices), file=sys.stderr, flush=True)
        
            self.__ports = []
            for s in serial_devices:
                self.__ports.append(serial.Serial(s, PORT_SPEED))
            if DEBUG:
                print('ports include:  {}\n'.format(self.__ports), file=sys.stderr, flush=True)
            time.sleep(3) # wait 3 seconds for Arduinos to reset
            
        # Send response status code
        self.send_response(200)
 
        # Send headers
        self.send_header('Content-type','application/json')
        self.end_headers()

        result=[]
        
        if DEBUG:
            print('self.__ports is {}'.format(self.__ports), file=sys.stderr, flush=True)
            
        for port in self.__ports:
            port.write(NL)  # ask for samples
            
            # read first line returned
            split_line = port.readline().decode('UTF-8').split()
            if DEBUG:
                print('line: "{}"'.format(split_line))
            # process till a blank line is returned
            while len(split_line) > 0:
                if len(split_line) == 3:
                    sample = {}
                    sample['type'] = 'DS18B20_on_Arduino'
                    sample['id']=split_line[1].replace('.','')
                    sample['temp_C'] = split_line[2]
                    sample['when'] = datetime.datetime.now().strftime(DATETIME_FORMAT)
                    result.append(sample)
                # get another line
                split_line = port.readline().decode('UTF-8').split()
                if DEBUG:
                    print('line:  "{}"'.format(split_line))
            
        # Write content as utf-8 data
        self.wfile.write(bytes(json.dumps(result), "utf8"))
        return
    
 
def run():
    httpd_server = HTTPServer(DEFAULT_SERVER_ADDRESS, DS18B20_on_Arduino_HTTPServer_RequestHandler)
    print('running server listening on {}...'.format(DEFAULT_SERVER_ADDRESS))
    httpd_server.serve_forever()
    
run()
