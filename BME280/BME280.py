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

Capture data from BME280 attached to Raspberry Pi I2C bus.

This puts the chip in a mode that is continuously taking samples and 
smoothing the values to try to eliminate spurious data.  The sample rate
is 250 mSec and 8 samples are smoothed so changes take about 2 seconds
to be fully integrated in to the retrieved values.

Official datasheet available from :
https://www.bosch-sensortec.com/bst/products/all_products/bme280
"""

from ctypes import c_short
from ctypes import c_ushort
from ctypes import c_byte
from ctypes import c_ubyte
import hashlib
import smbus
import time

DEBUG = 0
if DEBUG:
    import sys

BME280_DEFAULT_I2C_ADDR = 0x76  # Default device I2C address

# Register Addresses
BME280_CALIBRATION_1_BASE_ADDR   = 0x88
BME280_CALIBRATION_1_COUNT   = 24
BME280_CALIBRATION_2_BASE_ADDR   = 0xA1
BME280_CALIBRATION_2_COUNT   = 1
BME280_REG_CHIP_ID_ADDR   = 0xD0
BME280_REG_RESET_ADDR   = 0xE0
BME280_CALIBRATION_3_BASE_ADDR   = 0xE1
BME280_CALIBRATION_3_COUNT   = 7
BME280_REG_CONTROL_HUM_ADDR = 0xF2
BME280_REG_CONTROL_MEAS_ADDR = 0xF4
BME280_REG_CONFIG_ADDR = 0xF5
BME280_REG_DATA_ADDR = 0xF7
BME280_REG_DATA_COUNT = 8
BME280_REG_HUM_MSB_ADDR = 0xFD
BME280_REG_HUM_LSB_ADDR = 0xFE

# Values for some registers
BME280_REG_CHIP_ID  = 0x60  # this is the ID for BME280 chips
BME280_REG_RESET_CMD = 0xB6 # write this to BME280_REG_RESET_ADDR for RESET

BME280_REG_CONTROL_HUM_OS_NONE = 0x00  # skipped, output set to 0x8000
BME280_REG_CONTROL_HUM_OS_1 = 0x01  # oversampling x 1
BME280_REG_CONTROL_HUM_OS_2 = 0x02  # oversampling x 2
BME280_REG_CONTROL_HUM_OS_4 = 0x03  # oversampling x 4
BME280_REG_CONTROL_HUM_OS_8 = 0x04  # oversampling x 8
BME280_REG_CONTROL_HUM_OS_16 = 0x05  # oversampling x 16
BME280_REG_CONTROL_HUM_VALUE = BME280_REG_CONTROL_HUM_OS_8

BME280_REG_CONTROL_MEAS_T_OS_NONE = 0x00 # skipped, output set to 0x8000
BME280_REG_CONTROL_MEAS_T_OS_1 = 0x20 # Temp oversampling x 1
BME280_REG_CONTROL_MEAS_T_OS_2 = 0x040 # Temp oversampling x 2
BME280_REG_CONTROL_MEAS_T_OS_4 = 0x60 # Temp oversampling x 4
BME280_REG_CONTROL_MEAS_T_OS_8 = 0x80 # Temp oversampling x 8
BME280_REG_CONTROL_MEAS_T_OS_16 = 0xA0 # Temp oversampling x 16
BME280_REG_CONTROL_MEAS_P_OS_NONE = 0x00 # skipped, output set to 0x8000
BME280_REG_CONTROL_MEAS_P_OS_1 = 0x04 # Temp oversampling x 1
BME280_REG_CONTROL_MEAS_P_OS_2 = 0x08 # Temp oversampling x 2
BME280_REG_CONTROL_MEAS_P_OS_4 = 0x0C # Temp oversampling x 4
BME280_REG_CONTROL_MEAS_P_OS_8 = 0x10 # Temp oversampling x 8
BME280_REG_CONTROL_MEAS_P_OS_16 = 0x14 # Temp oversampling x 16
BME280_REG_CONTROL_MEAS_MODE_SLEEP = 0x00 # no measurements
BME280_REG_CONTROL_MEAS_MODE_FORCED = 0x01 # Forced -- one measurement
BME280_REG_CONTROL_MEAS_MODE_NORMAL = 0x03 # Normal -- runs continually
BME280_REG_CONTROL_MEAS_VALUE = (BME280_REG_CONTROL_MEAS_T_OS_8 |
                                 BME280_REG_CONTROL_MEAS_P_OS_8 |
                                 BME280_REG_CONTROL_MEAS_MODE_NORMAL)

BME280_REG_CONFIG_T_SB_MS_0_5 = 0x00     # Standby times
BME280_REG_CONFIG_T_SB_MS_62_5 = 0x20
BME280_REG_CONFIG_T_SB_MS_125 = 0x40
BME280_REG_CONFIG_T_SB_MS_250 = 0x60
BME280_REG_CONFIG_T_SB_MS_500 = 0x80
BME280_REG_CONFIG_T_SB_MS_1000 = 0xA0
BME280_REG_CONFIG_T_SB_MS_10 = 0xC0
BME280_REG_CONFIG_T_SB_MS_20 = 0xE0
BME280_REG_CONFIG_FILTER_OFF = 0x00
BME280_REG_CONFIG_FILTER_2 = 0x04
BME280_REG_CONFIG_FILTER_4 = 0x08
BME280_REG_CONFIG_FILTER_8 = 0x0C
BME280_REG_CONFIG_FILTER_16 = 0x10
BME280_REG_CONFIG_VALUE = (BME280_REG_CONFIG_T_SB_MS_250 | BME280_REG_CONFIG_FILTER_8)

BME280_RESET_TIME_IN_SECONDS = 0.001    # not specified, this seems like enough
BME280_SETTLE_TIME_IN_SECONDS = 0.25 * 8 # normal update every 250 mS x 8 samples


class BME280:
    
    def __init__(self, i2c_bus=None, i2c_addr=BME280_DEFAULT_I2C_ADDR):
        self.__i2c_bus = i2c_bus
        self.__i2c_addr = i2c_addr
        
        if self.__i2c_bus:
            # a bus was specified use only that value
            self.__smbus = smbus.SMBus(self.__i2c_bus)
        else:
            try: # the usual address is tried first
                self.__smbus = smbus.SMBus(1)
                self.__i2c_bus = 1
            except Exception as ex: # not on 1 -- if not on 0 it is an error
                self.__smbus = smbus.SMBus(0)
                self.__i2c_bus = 0
 
        # soft reset
        self.__smbus.write_byte_data(self.__i2c_addr, BME280_REG_RESET_ADDR, BME280_REG_RESET_CMD)
        time.sleep(BME280_RESET_TIME_IN_SECONDS)
        # make sure we have the expected type of chip
        self.__chip_id = self.__smbus.read_i2c_block_data(self.__i2c_addr, BME280_REG_CHIP_ID_ADDR, 1)[0]
        if BME280_REG_CHIP_ID != self.__chip_id:
            raise Exception('expected chip ID of 0x{:02x} but got 0x{:02x}'.format(BME280_REG_CHIP_ID, self.__chip_id))

        # Read blocks of calibration data from EEPROM
        # See data sheet
        self.__cal1 = self.__smbus.read_i2c_block_data(self.__i2c_addr, 
                                                       BME280_CALIBRATION_1_BASE_ADDR,
                                                       BME280_CALIBRATION_1_COUNT)
        self.__cal2 = self.__smbus.read_i2c_block_data(self.__i2c_addr, 
                                                       BME280_CALIBRATION_2_BASE_ADDR,
                                                       BME280_CALIBRATION_2_COUNT)
        self.__cal3 = self.__smbus.read_i2c_block_data(self.__i2c_addr, 
                                                       BME280_CALIBRATION_3_BASE_ADDR,
                                                       BME280_CALIBRATION_3_COUNT)
        
        # Convert byte data to word values
        self.__dig_T1 = self.__getUShort(self.__cal1, 0)
        self.__dig_T2 = self.__getShort(self.__cal1, 2)
        self.__dig_T3 = self.__getShort(self.__cal1, 4)
        
        self.__dig_P1 = self.__getUShort(self.__cal1, 6)
        self.__dig_P2 = self.__getShort(self.__cal1, 8)
        self.__dig_P3 = self.__getShort(self.__cal1, 10)
        self.__dig_P4 = self.__getShort(self.__cal1, 12)
        self.__dig_P5 = self.__getShort(self.__cal1, 14)
        self.__dig_P6 = self.__getShort(self.__cal1, 16)
        self.__dig_P7 = self.__getShort(self.__cal1, 18)
        self.__dig_P8 = self.__getShort(self.__cal1, 20)
        self.__dig_P9 = self.__getShort(self.__cal1, 22)
        
        self.__dig_H1 = self.__getUChar(self.__cal2, 0)
        self.__dig_H2 = self.__getShort(self.__cal3, 0)
        self.__dig_H3 = self.__getUChar(self.__cal3, 2)
        self.__dig_H4 = self.__getChar(self.__cal3, 3)
        self.__dig_H4 = (self.__dig_H4 << 24) >> 20
        self.__dig_H4 = self.__dig_H4 | (self.__getChar(self.__cal3, 4) & 0x0F)
        self.__dig_H5 = self.__getChar(self.__cal3, 5)
        self.__dig_H5 = (self.__dig_H5 << 24) >> 20
        self.__dig_H5 = self.__dig_H5 | (self.__getUChar(self.__cal3, 4) >> 4 & 0x0F)
        self.__dig_H6 = self.__getChar(self.__cal3, 6)

        # set the control registers to oversample and continuously monitor so we 
        # can read at any time
        
        if DEBUG:
            print('BME280_REG_CONTROL_MEAS_MODE_SLEEP: 0x{:2x}'.format(BME280_REG_CONTROL_MEAS_MODE_SLEEP), file=sys.stderr)
            print('BME280_REG_CONFIG_VALUE: 0x{:2x}'.format(BME280_REG_CONFIG_VALUE), file=sys.stderr)
            print('BME280_REG_CONTROL_HUM_VALUE: 0x{:2x}'.format(BME280_REG_CONTROL_HUM_VALUE), file=sys.stderr)
            print('BME280_REG_CONTROL_MEAS_VALUE: 0x{:2x}'.format(BME280_REG_CONTROL_MEAS_VALUE), file=sys.stderr)
        
        # put in sleep node as docs says other register writes must be seen in SLEEP mode
        self.__smbus.write_byte_data(self.__i2c_addr, 
                                     BME280_REG_CONTROL_MEAS_ADDR, 
                                     BME280_REG_CONTROL_MEAS_MODE_SLEEP)
        self.__smbus.write_byte_data(self.__i2c_addr, 
                                     BME280_REG_CONFIG_ADDR, 
                                     BME280_REG_CONFIG_VALUE)
        self.__smbus.write_byte_data(self.__i2c_addr, 
                                     BME280_REG_CONTROL_HUM_ADDR, 
                                     BME280_REG_CONTROL_HUM_VALUE)
        self.__smbus.write_byte_data(self.__i2c_addr, 
                                     BME280_REG_CONTROL_MEAS_ADDR, 
                                     BME280_REG_CONTROL_MEAS_VALUE)
        # wait 2 second for samples to get averaged out
        time.sleep(BME280_SETTLE_TIME_IN_SECONDS)
        
        h = hashlib.new('md5')
        h.update(bytes(self.__cal1))
        h.update(bytes(self.__cal2))
        h.update(bytes(self.__cal3))
        self.__uid = h.hexdigest()

        
    def get_chip_id(self):
        '''
        retrieve the chip_id byte from the device
        '''
        return self.__chip_id
    
    def get_uid(self):
        '''
        retrieve the UID generated from the MD5 of the chip calibration data
        '''
        return self.__uid
    
    def __get_cal_1_data(self):
        return self.__cal1
    
    def __get_cal_2_data(self):
        return self.__cal2
    
    def __get_cal_3_data(self):
        return self.__cal3
    
    
    def retrieve_temperature_pressure_humidity(self):
        '''
        Retrieve the raw data from the BME280 and apply the various correction factors to
        determine temperature, pressure and relative humidity
        Return the tuple <temperature in degrees C>, <pressure in hPa>, <relative humidity %>
        '''
         # Read temperature/pressure/humidity
        data = self.__smbus.read_i2c_block_data(self.__i2c_addr, BME280_REG_DATA_ADDR, BME280_REG_DATA_COUNT)
        pres_raw = (data[0] << 12) | (data[1] << 4) | (data[2] >> 4)
        temp_raw = (data[3] << 12) | (data[4] << 4) | (data[5] >> 4)
        hum_raw = (data[6] << 8) | data[7]
        
        # Refine temperature
        var1 = ((((temp_raw >> 3) - (self.__dig_T1 << 1))) * (self.__dig_T2)) >> 11
        var2 = (((((temp_raw >> 4) - (self.__dig_T1)) * ((temp_raw >> 4) - (self.__dig_T1))) >> 12) * (self.__dig_T3)) >> 14
        t_fine = var1 + var2
        temperature = float(((t_fine * 5) + 128) >> 8);
        
        # Refine pressure and adjust for temperature
        var1 = t_fine / 2.0 - 64000.0
        var2 = var1 * var1 * self.__dig_P6 / 32768.0
        var2 = var2 + var1 * self.__dig_P5 * 2.0
        var2 = var2 / 4.0 + self.__dig_P4 * 65536.0
        var1 = (self.__dig_P3 * var1 * var1 / 524288.0 + self.__dig_P2 * var1) / 524288.0
        var1 = (1.0 + var1 / 32768.0) * self.__dig_P1
        if var1 == 0:
            pressure = 0
        else:
            pressure = 1048576.0 - pres_raw
            pressure = ((pressure - var2 / 4096.0) * 6250.0) / var1
            var1 = self.__dig_P9 * pressure * pressure / 2147483648.0
            var2 = pressure * self.__dig_P8 / 32768.0
            pressure = pressure + (var1 + var2 + self.__dig_P7) / 16.0
        
         # Refine humidity
        humidity = t_fine - 76800.0
        humidity = (hum_raw - (self.__dig_H4 * 64.0 + self.__dig_H5 / 16384.0 * humidity)) * (self.__dig_H2 / 65536.0 * (1.0 + self.__dig_H6 / 67108864.0 * humidity * (1.0 + self.__dig_H3 / 67108864.0 * humidity)))
        humidity = humidity * (1.0 - self.__dig_H1 * humidity / 524288.0)
        if humidity > 100:
            humidity = 100.0
        elif humidity < 0:
            humidity = 0.0
        
        return temperature / 100.0, pressure / 100.0, humidity
        
    def __getShort(self, data, index):
        # return two bytes from data as a signed 16-bit value
        return c_short((data[index + 1] << 8) + data[index]).value
    
    def __getUShort(self, data, index):
        # return two bytes from data as an unsigned 16-bit value
        return c_ushort((data[index + 1] << 8) + data[index]).value
    
    def __getChar(self, data, index):
        # return one byte from data as a signed char
        return c_byte(data[index]).value
    
    def __getUChar(self, data, index):
        # return one byte from data as an unsigned char
        return c_ubyte(data[index]).value
    

#
# main
#
if __name__ == '__main__':
    
    sensor = BME280()  # take defaults
    print('found BME280 with chip ID of 0x{:2x}'.format(sensor.get_chip_id()))
    print('UID:  {}'.format(sensor.get_uid()))

    temperature,pressure,humidity = sensor.retrieve_temperature_pressure_humidity()
    print ("Temperature : {} C".format(temperature))
    print ("Pressure :    {} hPa".format(pressure))
    print ("Humidity :    {} %".format(humidity))
