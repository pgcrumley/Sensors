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

Capture data from HTU21D attached to Raspberry Pi GPIO pins.
By default CLOCK is pin 5 and DATA is pin 3

Datasheet available from :
https://www.silabs.com/documents/public/data-sheets/Si7021-A20.pdf
"""

import time

import I2cAccess

DEFAULT_DATA_BOARD_PIN = 11
DEFAULT_CLOCK_BOARD_PIN = 13  

HTU21D_DEFAULT_I2C_ADDR = 0x40  # Default device I2C address

# Register Addresses
HTU21D_CMD_MEASURE_RH_HOLD_MASTER_MODE = 0xE5
HTU21D_CMD_MEASURE_RH_NO_HOLD_MASTER_MODE = 0xF5
HTU21D_CMD_MEASURE_TEMP_HOLD_MASTER_MODE = 0xE3
HTU21D_CMD_MEASURE_TEMP_NO_HOLD_MASTER_MODE = 0xF3
HTU21D_CMD_RESET = 0xFE
HTU21D_CMD_WRITE_USER_REG_1 = 0xE6
HTU21D_CMD_READ_USER_REG_1 = 0xE7

HTU21D_REST_TIME_IN_SEC = 0.1
HTU21D_MAX_TEMP_CONVERSION_TIME_IN_SEC = 0.06
HTU21D_MAX_RH_CONVERSION_TIME_IN_SEC = 0.02

class HTU21D:
    
    def __init__(self, i2c_addr=HTU21D_DEFAULT_I2C_ADDR, 
                 gpio_clock=DEFAULT_CLOCK_BOARD_PIN, gpio_data=DEFAULT_DATA_BOARD_PIN):
        self.__i2c_addr = i2c_addr
        
        self.__i2c_port = I2cAccess.I2cPort(clock_pin=gpio_clock, data_pin=gpio_data)
        self.__i2c_dev = I2cAccess.I2cDevice(self.__i2c_port, self.__i2c_addr)

        # reset the device
        self.__i2c_dev.send_bytes_no_offset((HTU21D_CMD_RESET,))
        time.sleep(HTU21D_REST_TIME_IN_SEC)
        
        ur_val = self.__i2c_dev.receive_bytes_8bit_offset(HTU21D_CMD_READ_USER_REG_1, 1)
        if 0x02 != ur_val[0]:
            raise Exception('expected 0x02 from USER_REG after reset but got 0x{:02x}'.format(ur_val[0]))
    
        self.__chip_type = 'HTU21D'


    def get_chip_type(self):
        '''
        return the chip's firmware revision
        '''
        return self.__chip_type
        
        
    def get_uid(self):
        '''
        return the electronic ID from the chip.  (should be unique)
        '''
        return 'no_id'
    
    

    def retrieve_temp_humidity(self):
        '''
        Retrieve the raw data from the HTU21D and apply the various correction factors to
        determine temperature and relative humidity
        Return the tuple <temperature in degrees C>, <relative humidity %>
        '''
        # Read humidity -- wait...
        self.__i2c_dev.send_bytes_no_offset((HTU21D_CMD_MEASURE_RH_NO_HOLD_MASTER_MODE,))
        time.sleep(HTU21D_MAX_RH_CONVERSION_TIME_IN_SEC)
        raw_bytes = self.__i2c_dev.receive_bytes_no_offset(3)
        raw = ((raw_bytes[0] & 0xff) << 8) + (raw_bytes[1] & 0xff)
        rh = (raw * 125 / 65536.0) - 6.0
        if rh > 100:
            rh = 100.0
        elif rh < 0:
            rh = 0.0

        # Then get the temperature
        self.__i2c_dev.send_bytes_no_offset((HTU21D_CMD_MEASURE_TEMP_NO_HOLD_MASTER_MODE,))
        time.sleep(HTU21D_MAX_TEMP_CONVERSION_TIME_IN_SEC)
        raw_bytes = self.__i2c_dev.receive_bytes_no_offset(3)
        raw = ((raw_bytes[0] & 0xff) << 8) + (raw_bytes[1] & 0xff)
        temp = (raw * 175.72 / 65536.0) - 46.85

        return temp, rh

#
# main
#
if __name__ == '__main__':
    
    sensor = HTU21D()  # take defaults
    print("found HTU21D with chip type of {}".format(sensor.get_chip_type()))

    temp,rh = sensor.retrieve_temp_humidity()
    print ("Temperature :  {} C".format(temp))
    print ("Rel Humidity : {} %".format(rh))
