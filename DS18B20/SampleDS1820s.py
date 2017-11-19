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
  YYYYMMDD_HHMMSS <ID> <degrees C>
  
Datasheet at https://datasheets.maximintegrated.com/en/ds/DS18B20.pdf

"""

import datetime
import time

import DS18B20_Controller

SAMPLE_INTERVAL_IN_SECONDS = 60

while True:
    controller = DS18B20_Controller.DS18B20_Controller()
    with open('/opt/Sensors/logs/DS18B20.log', 'a') as output:
        for i in controller.get_ids():
            temp = controller.retrieve_temp(i)
            result = '{} {} {:9.4f}'.format(
                datetime.datetime.now().strftime('%Y%m%d_%H%M%S'),
                i,
                temp)
            print(result, file=output, flush=True)
        time.sleep(SAMPLE_INTERVAL_IN_SECONDS)
