#!/usr/bin/env python3
"""
MIT License

Copyright (c) 2021, 2022 Paul G Crumley

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

A Controller to retrieve temperatures from one of the DS18B20_*_SampleOnDemand
devices.

"""

import argparse
import sys
import time

import serial.tools.list_ports

DEBUG = False

# remove these devices from list -- this list is ad hoc
# probably best to put the port names on the command line
FILTERED_OUT_PORTS = ['COM1', # windows seems to use this
                      '/dev/ttyAMA0'] # raspberry pi console

PORT_SPEED = 115200
TIMEOUT_IN_SEC = 2.0
RESET_TIME_IN_SEC = 3.0
MAX_VERSION_LINE_LENGTH = 256
MAX_SAMPLE_LINE_LENGTH = 256
MINIMUM_VERSION = 4

READ_VERSION_COMMAND = '`'.encode('UTF-8')
READ_TEMPERATURE_SENSORS_COMMAND = '?'.encode('UTF-8')


SENSOR_TYPE_NAME = 'DS18B20'

class DS18B20_OnDemand_via_Arduino_Controller:
    
    def __init__(self, serial_port_name=None, speed=PORT_SPEED, timeout=TIMEOUT_IN_SEC):
        self.__serial_port_name = serial_port_name
        self.__speed = speed
        self.__timeout_in_seconds = timeout
        if DEBUG:
            print(f'looking for usable device on port "{self.__serial_port_name}"',
                  file=sys.stderr, flush=True)
        self.__serial_port = serial.Serial(self.__serial_port_name, 
                                           baudrate=self.__speed, 
                                           timeout=self.__timeout_in_seconds)
        # give Arduino time to reset after serial open which causes a reset
        time.sleep(RESET_TIME_IN_SEC)  

        self.__serial_port.reset_input_buffer() #clears buffer before reading to remove any residual data.
        if DEBUG:
            print(f'on "{self.__serial_port_name}" made "{self.__serial_port}"',
                  file=sys.stderr, flush=True)
        if DEBUG:
            print(f'reading program version on "{self.__serial_port_name}"',
                  file=sys.stderr, flush=True)
        self.__serial_port.write(READ_VERSION_COMMAND)
        self.__serial_port.flush()

        version = self.__serial_port.read(MAX_VERSION_LINE_LENGTH).decode('UTF-8').strip()
#        version = self.__serial_port.read(MAX_VERSION_LINE_LENGTH)
#TBD        version = self.__serial_port.readline().decode('UTF-8').strip()
        if DEBUG:
            print(f'version command returned "{version}"',
                  file=sys.stderr, flush=True)
        self.__program_version = version
        if '_DS18B20_' not in self.__program_version:
            raise Exception(f'no valid program found on {serial_port_name}')
        if 'OnDemand' not in self.__program_version:
            raise Exception(f'no valid program found on {serial_port_name}')
        v =  int(self.__program_version.split('_')[0].split('V')[1])
        if v < MINIMUM_VERSION:
            raise Exception(f'found version {v}, but need >= {MINIMUM_VERSION}')

        if DEBUG:
            print(f'on port "{self.__serial_port_name}" found "{self.__program_version}"',
                  file=sys.stderr, flush=True)

        _junk = self.retrieve_temperatures()  # first read might be incomplete

        
    def __repr__(self):
        """
        tell what this is
        """
        return(f'DS18B20_OnDemand_via_Arduino_Controller with Arduino program version "{self.__program_version}" on {self.__serial_port_name}')
    
    def get_type(self):
        """
        return the type of sensor as a string.
        """
        return SENSOR_TYPE_NAME
            
    def get_arduino_program_version(self):
        """
        return the version string from the Arduino program.
        """
        return self.__program_version
            
    def retrieve_temperatures(self):
        """
        Retrieve temperatures of all sensors attached to the Arduino.
        Return a map of {device_id, degrees_c}
        """
        result = {}
        
        self.__serial_port.reset_input_buffer() #clears buffer before reading to remove any residual data.
        self.__serial_port.write(READ_TEMPERATURE_SENSORS_COMMAND)
        self.__serial_port.flush()

        line = self.__serial_port.readline(MAX_SAMPLE_LINE_LENGTH).decode('UTF-8').strip()
        if DEBUG:
            print(f'first line read: "{line}"',
                  file=sys.stderr, flush=True)
        while len(line):  # there are non-empty lines to read
            part = line.split()
            try:
                if 'DS18B20' == part[0]:
                    result[part[1].replace('.','')] = float(part[2])
            except:
                pass # ignore ill-formed lines
            
            # get next line
            line = self.__serial_port.readline(MAX_SAMPLE_LINE_LENGTH).decode('UTF-8').strip()
            if DEBUG:
                print(f'line read: "{line}"',
                      file=sys.stderr, flush=True)

        return result        
        

#####################
   
    
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


def find_DS18B20_device(port_list):
    """
    Try to find usable DS18B20 on the given ports.
    
    return a map of {name, controller}
    """
    result = {}
    for p in port_list:
        try:
            if DEBUG:
                print(f'looking for device on "{p}"',
                      file=sys.stderr, flush=True)
            # get serial port access for each serial device
            controller = DS18B20_OnDemand_via_Arduino_Controller(p)
            result[p] = controller
            if DEBUG:
                print(f'found "{result[p]}"',
                      file=sys.stderr, flush=True)
        except Exception as ex:
            if DEBUG:
                print(f'while looking for device on "{p}" caught "{ex}"',
                      file=sys.stderr, flush=True)            
    return result

#
# main
#
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Controller for Arduino running a DS18B20_Sample_OnDeman program attached via a serial port.")
    parser.add_argument("-d", "--debug", 
                        help="turn on debugging", 
                        action="store_true")
    parser.add_argument("-p", "--port", 
                        help="port to which Arduino is connected (suggested, otherwise looks at all ports)", 
                        required=False)
    args = parser.parse_args()

    if (args.debug):
        DEBUG = 1
        print('turned on DEBUG from command line.',
              file=sys.stderr, flush=True)

    given_port = args.port
    
    if DEBUG:
        print(f'given_port = {given_port}',
              file=sys.stderr, flush=True)

    if given_port:
        port_name_list = [given_port]
    else:
        port_name_list = determine_ports()
    if DEBUG:
        print(f'looking for DS18B20 device on ports {port_name_list}',
              file=sys.stderr, flush=True)
    
    # get serial port access for each serial device
    controller_map = find_DS18B20_device(port_name_list)

    for c in controller_map.keys():
        print(f'    {c} : {controller_map[c].get_type()} : {controller_map[c].get_arduino_program_version()}')
        print(controller_map[c].retrieve_temperatures())