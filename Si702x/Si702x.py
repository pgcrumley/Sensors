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

Capture data from a Si702x device attached to a Raspberry Pi and 
periodically send the results to a file.

Datasheet available from :
https://www.silabs.com/documents/public/data-sheets/Si7021-A20.pdf

By default CLOCK is pin 13 and DATA is pin 11  (these are the board pin #s)

NOTE:  The SI7013 can capture data from an external voltage or sensor.  This
    code only supports the same data as the SI702X chips.

"""


import time

import I2cAccess

DEBUG = 0
if DEBUG:
    import sys
    
DEFAULT_RETRIES=5

DEFAULT_DATA_BOARD_PIN = 11
DEFAULT_CLOCK_BOARD_PIN = 13  

Si702x_DEFAULT_I2C_ADDR = 0x40  # Default device I2C address

# Register Addresses
Si702x_CMD_MEASURE_RH_HOLD_MASTER_MODE = 0xE5
Si702x_CMD_MEASURE_RH_NO_HOLD_MASTER_MODE = 0xF5
Si702x_CMD_MEASURE_TEMP_HOLD_MASTER_MODE = 0xE3
Si702x_CMD_MEASURE_TEMP_NO_HOLD_MASTER_MODE = 0xF3
Si702x_CMD_READ_TEMP_FROM_RH_MEASUREMENT = 0xE0
Si702x_CMD_RESET = 0xFE
Si702x_CMD_WRITE_USER_REG_1 = 0xE6
Si702x_CMD_READ_USER_REG_1 = 0xE7
Si702x_CMD_WRITE_HEATER_REG = 0x51
Si702x_CMD_READ_HEATER_REG = 0x11
Si702x_CMD_READ_EID_1 = 0xFA0F
Si702x_CMD_READ_EID_2 = 0xFCC9
Si702x_CMD_READ_FW_REVISION = 0x84B8

Si702x_REST_TIME_IN_SEC = 0.1
Si702x_MAX_CONVERSION_TIME_IN_SEC = 0.02

class Si702x:
    
    def __init__(self, i2c_addr=Si702x_DEFAULT_I2C_ADDR, 
                 board_clock_pin=DEFAULT_CLOCK_BOARD_PIN, board_data_pin=DEFAULT_DATA_BOARD_PIN):
        self.__i2c_addr = i2c_addr
        
        self.__i2c_port = I2cAccess.I2cPort(clock_pin=board_clock_pin, data_pin=board_data_pin)
        self.__i2c_dev = I2cAccess.I2cDevice(self.__i2c_port, self.__i2c_addr)

        # reset the device
        self.__i2c_dev.send_bytes_no_offset((Si702x_CMD_RESET,))
        time.sleep(Si702x_REST_TIME_IN_SEC)
        
        ur_val = self.__i2c_dev.receive_bytes_8bit_offset(Si702x_CMD_READ_USER_REG_1, 1)
        if 0x3a != ur_val[0]:
            raise Exception('expected 0x02 from USER_REG after reset but got 0x{:02x}'.format(ur_val[0]))

    
        # get firmware revision    
        self.__fw_rev = self.__i2c_dev.receive_bytes_16bit_offset(Si702x_CMD_READ_FW_REVISION, 1)
        self.__fw_rev = self.__fw_rev[0]  # get value from list

        # get the chip type & electronic ID
        eid_1_bytes = self.__i2c_dev.receive_bytes_16bit_offset(Si702x_CMD_READ_EID_1, 4)
        eid_2_bytes = self.__i2c_dev.receive_bytes_16bit_offset(Si702x_CMD_READ_EID_2, 4)
        
        snb3 = eid_2_bytes[0]
        if 21 == snb3:
            self.__chip_type = 'Si7021'
        elif 20 == snb3:
            self.__chip_type = 'Si7020'
        elif 13 == snb3:
            self.__chip_type = 'Si7013'
        else:
            self.__chip_type = 'Si70??'
            
        self.__eid = '{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}{:02x}'.format(eid_1_bytes[0], eid_1_bytes[1], eid_1_bytes[2], eid_1_bytes[3], 
                                                                               eid_2_bytes[0], eid_2_bytes[1], eid_2_bytes[2], eid_2_bytes[3])


    def get_chip_type(self):
        '''
        return the chip type
        '''
        return self.__chip_type

        
    def get_chip_fw_rev(self):
        '''
        return the chip's firmware revision
        '''
        return self.__fw_rev

        
    def get_chip_eid(self):
        '''
        return the electronic ID from the chip.  (should be unique)
        '''
        return self.__eid
    
    
    def get_uid(self):
        '''
        same as get_chip_eid but different name for compatibilityZZ
        '''
        return self.__eid
    
    
    def retrieve_temp_humidity(self):
        '''
        Retrieve the raw data from the Si702x and apply the various correction factors to
        determine temperature and relative humidity
        Return the tuple <temperature in degrees C>, <relative humidity %>
        '''
         # Read humidity -- wait...
        self.__i2c_dev.send_bytes_no_offset((Si702x_CMD_MEASURE_RH_NO_HOLD_MASTER_MODE,))
        time.sleep(Si702x_MAX_CONVERSION_TIME_IN_SEC)
        raw_bytes = self.__i2c_dev.receive_bytes_no_offset(3)
        raw = ((raw_bytes[0] & 0xff) << 8) + (raw_bytes[1] & 0xff)
        rh = (raw * 125 / 65536.0) - 6.0
        if rh > 100:
            rh = 100.0
        elif rh < 0:
            rh = 0.0

        # Then get the temperature
        raw_bytes = self.__i2c_dev.receive_bytes_8bit_offset(Si702x_CMD_READ_TEMP_FROM_RH_MEASUREMENT, 3)
        raw = ((raw_bytes[0] & 0xff) << 8) + (raw_bytes[1] & 0xff)
        temp = (raw * 175.72 / 65536.0) - 46.85

        return temp,rh

    def retrieve_temp_humidity_with_retries(self, retries=DEFAULT_RETRIES):
        """
        Retrieve the temperature and humidity.  This will retry the action
        "retries" times before giving up on errors.
        """
        for t in range(retries):
            try:
                temp,rh = self.retrieve_temp_humidity()
                return temp,rh
            except Exception as e:
                # just toss problems for now and try again
                pass
        
        raise RuntimeError('exceeded {} retries while retrieving data'.format(retries))


#
# main
#
if __name__ == '__main__':
    
    sensor = Si702x()  # take defaults
    print("found Si702x with chip type of {}".format(sensor.get_chip_type()))
    print('chip has FW version of {}'.format(sensor.get_chip_fw_rev()))
    print('chip has EID of {}'.format(sensor.get_chip_eid()))

    temp,rh = sensor.retrieve_temp_humidity_with_retries()
    print ("Temperature :  {} C".format(temp))
    print ("Rel Humidity : {} %".format(rh))
