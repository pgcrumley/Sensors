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

Very simple web server to provide JSON representation of the DS18B20 devices.
  
Datasheet at https://datasheets.maximintegrated.com/en/ds/DS18B20.pdf

"""

import datetime
import json
from http.server import BaseHTTPRequestHandler, HTTPServer

import DS18B20_Controller

DEFAULT_LISTEN_ADDRESS = '0.0.0.0'     # respond to request from any address
#DEFAULT_LISTEN_ADDRESS = '127.0.0.1'   # responds to only requests from localhost
DEFAULT_LISTEN_PORT = 1820                  # IP port 1820
#DEFAULT_LISTEN_PORT = TBD                  # Pick some other port if you prefer
DEFAULT_SERVER_ADDRESS = (DEFAULT_LISTEN_ADDRESS, DEFAULT_LISTEN_PORT)


class DS18B20_HTTPServer_RequestHandler(BaseHTTPRequestHandler):
    '''
    A subclass of BaseHTTPRequestHandler to provide information about DS18B20 sensors.
    '''
    
    # holds the controller for the DS18B20 devices, will be created when first needed
    __controller = None
    
    def do_GET(self):
        '''
        handle the HTTP GET request
        '''
        # first time through get create the controller
        if self.__controller is None:
            self.__controller = DS18B20_Controller.DS18B20_Controller()
        
        # Send response status code
        self.send_response(200)
 
        # Send headers
        self.send_header('Content-type','application/json')
        self.end_headers()

        result=[]
         
        for i in self.__controller.get_ids():
            sample = {}
            sample['type'] = self.__controller.get_sensor_type()
            sample['id']=i
            temp = self.__controller.retrieve_temp(i)
            sample['temp_C'] = temp
            sample['when'] = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            result.append(sample)
        # Write content as utf-8 data
        self.wfile.write(bytes(json.dumps(result), "utf8"))
        return
    
 
def run():
    httpd_server = HTTPServer(DEFAULT_SERVER_ADDRESS, DS18B20_HTTPServer_RequestHandler)
    print('running server listening on {}...'.format(DEFAULT_SERVER_ADDRESS))
    httpd_server.serve_forever()
    
run()
