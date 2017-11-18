This project provides multiple Arduino programs, a simple python program which captures data from 
the On Demand versions of the sensors, and a 'services' file which can be installed to run the sampling
program with a system is started and try to keep the sample program running at all time.

The DS18B20 temperature sensors are relatively inexpensive and accurate.  I have used them for many 
projects -- often in large numbers -- and the electrical characteristics can make such use difficult 
as the normal Raspberry Pi connection attaches all the devices to a single pin with a single pull-up.

As the distances between the Raspberry Pi and the sensors grows, it can be difficult to maintain signal
integrity at long distances and with multi-drop and star wiring configurations.  There is also the 
undesirable property that a sensor that breaks can cause all the sensors to be unreachable.  Finally,
wiring problems with large bus and star topology can be difficult to diagnose and if the sensors are in
hostile environments I don't want the loss of a single sensor to make all the other sensors useless.

For these reasons I decided to use inexpensive Arduino Nano devices between the Raspberry Pi and the 
DS18B20 sensors.  The Nano has many pins for use with DS18B20 sensors, I am able to wire point to point, 
small multi-drop, or other patterns for each pin as needs dictate.  The use of the Arduino also gives 
some degree of electrical (i.e. USB level) protection if the sensor are in less-than optimal locations.

A typical setup might look like this:

 --------------             --------------
|              |           | Arduino Nano |<-- pin 2 - 13 --> | pull up resistor |--| DS18B20 sensors |
|              |<-- USB -->| (or other)   |<-- pin 2 - 13 --> | pull up resistor |--| DS18B20 sensors |
| Raspberry Pi |            -------------- 
|              |<-- USB -->| Arduino Nano |<-- pin 2 - 13 --> | pull up resistor |--| DS18B20 sensors |
|              |           | (or other)   |<-- pin 2 - 13 --> | pull up resistor |--| DS18B20 sensors |
 --------------             --------------

There are a lot of web pages showing how to hook up a DS18B20 to an Arduino so I won't spend time on that
level of detail.  Find one, get a sensor & a pull-up resistor and try it out.

I can have a lot of sensors this way ;-) and the pull-up can be placed for the best electrical
characeristics (I usually like to place it near the sensors but you are free to choose for yourself).
With decent wire the sensors can be many meters from the Raspberry Pi, and the I've seen USB extenders 
claim 100 meter distances (I've not tried these)

This is pretty easy to wire up on a proto board to try things out.  It is probably easiest to use a regular
Arduino with the nice sockets to experiment then use the less expensive Nano devices if you scale up and 
cost is an issue.

There are a bunch of Arduino programs provided but the only one that is probably needed is 
"DS18B20-SampleOnDemand.ino".  This version is the most capable of the many programs.

The "Fast" version is optimized for faster sampling rates (seldom needed) with the trade-off that each pin
of the Arduino can only be attached to a single DS18B20 sensor & pullup.

If you want to try the basic idea and don't have a sensor or pull-up just now you can load the "Mock" 
version of the Arduino program.  It pretends to have a boring sensor (stuck at one temperature).


The Arduino programs interact with controlling programs in one of two ways:
-- Sample On Demand
-- Normal

The Normal variety periodically sample the sensor(s) and send the data back to the controller via serial port.

The On-Demand variety wait for the controller to send a <new line> character then sample the sensors and send
back data for each then send an empty line to indicate all the sensor data has been sent.

There are also "mock" versions of the code that can fabricate data in either of the above modes for testing and
debug when real sensors are not available.

The programs look for sensors on the Arduino digital pins from 2-13, inclusive.  Pins 0 & 1 are used for serial
communication back to the controller.

Each pin must have a pull-up resistor to Vcc to operate correctly with the DS18B20 device(s) on that pin.

All versions return the sensor value in the form:
  "DS18B20 xx.xx.xx.xx.xx.xx.xx.xx -999.99\n"
where:
  DS18B20 is a constant telling the type of sensor
  xx.xx....xx is the sensor ID and is 8, 8 bit hex bytes
  -999.99 is the temperature in degrees C
  \n is the <new-line> character
An empty line is sent after the data for each sensor is sent.


Normal Mode Programs:
=====================
DS18B20.ino:
-----------
This is the most basic program.  It periodically (once every 60 seconds) looks for devices on the digital pins, for 
any DS18B20 devices found samples the temperature and returns the data.  More than one device can be attached to 
each pin.  If many devices are attached, or if there are many retries, the code might not be able to keep up with 
the 60 second period.  If this happens the code will sample as often as possible.

DS18B20-Mock.ino:
----------------
This is very basic program that obeys the normal protocol for use with testing and developing with real sensors are 
not available.


On-Demand Mode Programs:
========================
DS18B20-SampleOnDemand.ino:
--------------------------
This is the most basic program for the on-demand protocol.  When the controller sends a <new-line> character the code
looks for devices on the digital pins, and for any DS18B20 devices found samples the temperature and returns the data.
More than one device can be attached to each pin.  The controller should not send a <new-line> character till the data
from the previous request is complete.  (i.e. an empty line is received)

DS18B20-SampleOnDemand-Mock.ino:
-------------------------------
This is very basic program that obeys the on-demand protocol for use with testing and developing with real sensors 
are not available.

DS18B20-Fast-SampleOnDemand.ino:
------------------------------
This uses the same communication protocol but the Arduino program samples the sensors in parallel rather than serially
so the data can be returned faster.  
NOTE:  At this time the code only supports a single sensor per digital pin rather than multiple DS18B20 devices per pin
as for the DS18B20.ino and DS18B20-SampleOnDemand.ino programs.

DS18B20-Fast-SampleOnDemand-Mock.ino:
-------------------------------
This is very basic program that obeys the on-demand protocol for use with testing and developing with real sensors 
are not available.


The python script is called SampleOnDemandSensors.py.  It is normally installed in /opt/sensors and the log file
will be written to a directory called "logs" in this same directory.  The script expects to run as root so it
is able to access the serial ports.  

If you place the python script in some other location the .services file will need to be altered with that
location.

The SampleOnDemandSensors.service file tells how to install and initialize the automatic operation.



