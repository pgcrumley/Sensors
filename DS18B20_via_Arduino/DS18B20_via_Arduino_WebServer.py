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

Very simple web server to provide JSON representation of the DS18B20 devices
attached via Arduino devices.
  
Datasheet at https://datasheets.maximintegrated.com/en/ds/DS18B20.pdf

"""

import json
import serial
import serial.tools.list_ports
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

import DS18B20_OnDemand_via_Arduino_Controller

DEBUG = False


DEFAULT_LISTEN_ADDRESS = '0.0.0.0'     # respond to request from any address
#DEFAULT_LISTEN_ADDRESS = '127.0.0.1'   # responds to only requests from localhost
DEFAULT_LISTEN_PORT = 18820                 # IP port 18820
#DEFAULT_LISTEN_PORT = TBD                  # Pick some other port if you prefer
DEFAULT_SERVER_ADDRESS = (DEFAULT_LISTEN_ADDRESS, DEFAULT_LISTEN_PORT)


# remove these devices from list -- this list is ad hoc
# probably best to put the port names on the command line
FILTERED_OUT_PORTS = ['COM1', # windows seems to use this
                      '/dev/ttyAMA0'] # raspberry pi console



def determine_ports():
    """
    Go through serial ports available and try to find possible
    ports for the controller.
    
    Return a list of ports
    """
    filtered_ports = []

    # this will hold the names of serial port devices which might have Arduino
    serial_devices = [comport.device for comport in serial.tools.list_ports.comports()]
    for d in serial_devices:
        if d not in FILTERED_OUT_PORTS:
            filtered_ports.append(d)
        else:
            if DEBUG:
                print(f'removed "{d}" from device list',
                      file=sys.stderr, flush=True)
    if DEBUG:
        print(f'found ports include:  {filtered_ports}\n', 
              file=sys.stderr, flush=True)
    
    return filtered_ports


def find_DS18B20_devices():
    """
    Try to find usable DS18B20 on the given ports.
    
    return a map of {name, controller}
    """
    result = {}
    for p in determine_ports():
        try:
            if DEBUG:
                print(f'looking for device on "{p}"',
                      file=sys.stderr, flush=True)
            # get serial port access for each serial device
            controller = DS18B20_OnDemand_via_Arduino_Controller.DS18B20_OnDemand_via_Arduino_Controller(p)
            result[p] = controller
            if DEBUG:
                print(f'found "{result[p]}"',
                      file=sys.stderr, flush=True)
        except Exception as ex:
            if DEBUG:
                print(f'while looking for device on "{p}" caught "{ex}"',
                      file=sys.stderr, flush=True)            
    return result



class DS18B20_on_Arduino_HTTPServer_RequestHandler(BaseHTTPRequestHandler):
    '''
    A subclass of BaseHTTPRequestHandler to provide information about DS18B20 sensors.
    '''
    
    # holds the controllers for the DS18B20 devices, will be created when first needed
    __controllers = None
    
    def do_GET(self):
        '''
        handle the HTTP GET request
        '''
        if DEBUG:
            print(f'{DS18B20_on_Arduino_HTTPServer_RequestHandler.__controllers}',
                  file=sys.stderr, flush=True)
        
        # first time through get create the ports list
        if None == DS18B20_on_Arduino_HTTPServer_RequestHandler.__controllers:
            DS18B20_on_Arduino_HTTPServer_RequestHandler.__controllers = find_DS18B20_devices()
            if DEBUG:
                for c in DS18B20_on_Arduino_HTTPServer_RequestHandler.__controllers.keys():
                    print(f'    {c} : {DS18B20_on_Arduino_HTTPServer_RequestHandler.__controllers[c].get_type()} : {DS18B20_on_Arduino_HTTPServer_RequestHandler.__controllers[c].get_arduino_program_version()}',
                          file=sys.stderr, flush=True)
                    print(DS18B20_on_Arduino_HTTPServer_RequestHandler.__controllers[c].retrieve_temperatures(),
                          file=sys.stderr, flush=True)
            
        # Send response status code
        self.send_response(200)
 
        # Send headers
        self.send_header('Content-type','application/json')
        self.end_headers()

        result={}
        for c in DS18B20_on_Arduino_HTTPServer_RequestHandler.__controllers.keys():
            result.update(DS18B20_on_Arduino_HTTPServer_RequestHandler.__controllers[c].retrieve_temperatures())
        if DEBUG:
            print(f'results are: {result}',
                  file=sys.stderr, flush=True)
            
        # Write content as utf-8 data
        self.wfile.write(bytes(json.dumps(result, indent=1), "utf8"))
        return

    def log_request(self, junk):
        pass

    def log_message(self, junk):
        pass

    
 
def run():
    httpd_server = HTTPServer(DEFAULT_SERVER_ADDRESS, DS18B20_on_Arduino_HTTPServer_RequestHandler)
    print('running server listening on {}...'.format(DEFAULT_SERVER_ADDRESS))
    httpd_server.serve_forever()
    
run()
