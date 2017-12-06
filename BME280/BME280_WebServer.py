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

Very simple web server to provide JSON representation of the BME280 devices.

"""

import datetime
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

import BME280

DEFAULT_LISTEN_ADDRESS = '0.0.0.0'     # respond to request from any address
#DEFAULT_LISTEN_ADDRESS = '127.0.0.1'   # responds to only requests from localhost
DEFAULT_LISTEN_PORT = 10280                 # IP port 10280
#DEFAULT_LISTEN_PORT = TBD                  # Pick some other port if you prefer
DEFAULT_SERVER_ADDRESS = (DEFAULT_LISTEN_ADDRESS, DEFAULT_LISTEN_PORT)


class BME280_HTTPServer_RequestHandler(BaseHTTPRequestHandler):
    '''
    A subclass of BaseHTTPRequestHandler to provide information about BME280 sensors.
    '''
    
    # holds the device class, it will be created when needed
    __device = None
    
    def do_GET(self):
        '''
        handle the HTTP GET request
        '''
        # first time through get create the controller
        if self.__device is None:
            self.__device = BME280.BME280()
        
        # Send response status code
        self.send_response(200)
 
        # Send headers
        self.send_header('Content-type','application/json')
        self.end_headers()

        result=[]
        sample = {}
        sample['type'] = self.__device.get_chip_type()
        sample['id']=self.__device.get_uid()
        temperature,pressure,humidity = self.__device.retrieve_temperature_pressure_humidity()
        sample['temp_C'] = temperature
        sample['rel_hum'] = humidity
        sample['pressure'] = pressure
        sample['when'] = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        result.append(sample)
        
        # Write content as utf-8 data
        self.wfile.write(bytes(json.dumps(result, indent=1), "utf8"))
        return
    
 
def run():
    httpd_server = HTTPServer(DEFAULT_SERVER_ADDRESS, BME280_HTTPServer_RequestHandler)
    print('running server listening on {}...'.format(DEFAULT_SERVER_ADDRESS))
    httpd_server.serve_forever()
    
run()
