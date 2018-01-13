#!/usr/bin/python3
"""
MIT License

Copyright (c) 2018 Paul G Crumley

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

Base class for a variety of sensors
"""

import json

class Sensor:
    """
    Base class for a variety of sensors.
    
    This provides the minimum set of routines and must be subclassed to be
    of use.
    
    Implementations of a few functions should be usable without 
    overrides in subclasses.  The functino of 
      get_sensor_type_name(self)
      get_sensor_id(self)
    and the implementation of the functions of
      retrieve_data(self)
      retrieve_data_string(self)
    which use the results of retrieve_data(self) and get_data_tuple_names(self)
    to provide valid results.
    
    It is possible to extend the class with additional methods for special
    types of data retrieval or names that are must descriptive.
    """
    
    def __init__(self, device_type_name, sensor_id=None):
        """
        Create a new instance of a Sensor.
        
        A device_type_name must be provided.  The subclass will probably 
        determine the sensor_id as part of its initialization code.
        
        If the subclass initialization code fails it should set 
        self.__alive to False or raise an Error so an invalid instance is
        not created.
        """
        if device_type_name is None:
            raise ValueError('must provide device_type_name')
        
        self.__device_type_name = device_type_name
        self.__sensor_id = sensor_id
        self.__alive = True
        
    def close(self):
        """
        Stop using the device and release resources.
        """
        self.__alive = False
        
    def get_sensor_type_name(self):
        """
        Return the name of the type of sensor as a string.
        """
        if not self.__alive:
            raise ValueError('device is closed')
        
        return self.__device_type_name
            
    def get_sensor_id(self):
        """
        Return the id of the sensor as a string.
        """
        if not self.__alive:
            raise ValueError('device is closed')
        
        return self.__sensor_id
    
    def get_data_tuple_names(self):
        """
        Return a tuple with the names of the data in the data tuple.
        """
        raise NotImplementedError('Base class must be subclassed')


    def retrieve_data_tuple(self):
        """
        Retrieve data from the sensor and return as a tuple.
        """
        raise NotImplementedError('Base class must be subclassed')

    def retrieve_data_csv_string(self):
        """
        Retrieve data from the sensor as a CSV string with fields in 
        the same as the tuple. 
        """
        if not self.__alive:
            raise ValueError('device is closed')
        
        d = self.retrieve_data_tuple()
        result = ' , '.join([str(i) for i in d])
        return result
    
    def retrieve_data_string(self):
        """
        Retrieve data from the sensor as space string with fields in 
        the same as the tuple. 
        """
        if not self.__alive:
            raise ValueError('device is closed')
        
        d = self.retrieve_data_tuple()
        result = ' '.join([str(i) for i in d])
        return result
    
    def retrieve_data(self):
        """
        Retrieve data from the sensor and return it in a JSON dictionary.
        """
        if not self.__alive:
            raise ValueError('device is closed')
        
        keys = self.get_data_tuple_names()
        data = self.retrieve_data_tuple()
        if len(keys) != len(data):
            raise ValueError('name and data tuples are not the same length')
        result = {}
        for i in range(len(keys)):
            result[keys[i]] = data[i]
        return json.dumps(result)

#
# main
#
if __name__ == '__main__':
    pass
