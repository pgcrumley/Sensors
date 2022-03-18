# Introduction
The DS18B20 temperature sensors are relatively inexpensive and accurate.  
I have used them for many projects -- often in large numbers.  
While the Raspberry Pi can be configured to connect sensors to multiple pins
(the default Raspberry Pi software attaches all the devices to a single pin 
with a single pull-up) there is little isolation to protect the Raspberry Pi
a wide range of failures and signaling issues.

This project provides various Arduino sketches which capture data from DS18B20
sensors attached to Arduinos and send the temperatures back via the serial
port connection.

There are also python programs to interact with these Arduino sketches to either
store periodic samples in a file or serve the values via a web server. 

# Connections
As the distances between the Raspberry Pi and the sensors grows, 
it can be difficult to maintain signal integrity at long distances and with
multi-drop and star wiring configurations.
There is also the undesirable property that a sensor that breaks can cause
other sensors to be unreachable. 
Finally, wiring problems with large bus and star topology can be difficult
to diagnose and if the sensors are in hostile environments I don't want the
loss of a single sensor to make all the other sensors useless.

For these reasons I decided to use inexpensive Arduino Nano devices between a
Raspberry Pi and the DS18B20 sensors.  
The Nano has many pins for use with DS18B20 sensors so I am able to wire
point to point, 
small multi-drop, or other patterns for each pin as needs dictate.

The use of the Arduino also gives a degree of electrical (i.e. USB level)
protection if the sensor are in less-than optimal locations.

A typical setup might look like this:

     --------------             --------------
    |              |           | Arduino Nano |<-- pin 2 - 13 --> | pull up resistor |--| DS18B20 sensors |
    |              |<-- USB -->| (or other)   |<-- pin 2 - 13 --> | pull up resistor |--| DS18B20 sensors |
    | Raspberry Pi |            -------------- 
    |              |<-- USB -->| Arduino Nano |<-- pin 2 - 13 --> | pull up resistor |--| DS18B20 sensors |
    |              |           | (or other)   |<-- pin 2 - 13 --> | pull up resistor |--| DS18B20 sensors |
     --------------             --------------

There are a lot of web pages showing how to hook up a DS18B20 to an Arduino so
I won't spend time on that
level of detail.  Find one, get a sensor & a pull-up resistor and try it out.

The pull-up can be placed for the best electrical
characeristics (I usually like to place it near the sensors but you are free
to choose for yourself).
With decent wire the sensors can be many meters from the Raspberry Pi, and 
I've seen USB extenders claim 100 meter distances (I've not tried these)

This is pretty easy to wire up on a proto board to try things out.
It is probably easiest to use a regular Arduino with the nice sockets to
experiment then use the less expensive Nano devices if you scale up and 
cost is an issue.

Of the Arduino programs provided, the only one that is probably needed is 
"DS18B20-SampleOnDemand.ino".
This version is the most capable of the many programs as it can sample multiple
sensors on multiple pins.  

The "Fast" version is optimized for faster sampling rates (seldom needed)
with the trade-off that each pin
of the Arduino can only be attached to a single DS18B20 sensor & pullup.

If you want to try the basic idea and don't have a sensor or pull-up you 
can load the "Mock" version of the Arduino program.  The "Mock" versions
pretend to have a boring sensor (stuck at one temperature).

# Arduino Sketches
The Arduino sketches interact with controlling programs in one of two ways:
-- Periodically send a Sample
-- Sample On-Demand

The first variety periodically sample the sensor(s) and send the data back to
the controller via serial port.

The On-Demand variety wait for the controller to send a '?' character then
sample the sensors and send back data for each sensor.
After a line is sent for each sensor, the sketch sends an empty line to
indicate all the sensor data has been sent.

"Mock" versions of the code that can fabricate data in either of the above
modes for testing and debug when real sensors are not available.

The programs look for sensors on the Arduino digital pins from 2-13, inclusive.
Pins 0 & 1 are not available as they are used for serial 
communication back to the controller.

Each pin must have a pull-up resistor to Vcc to operate correctly with the
DS18B20 device(s) on that pin.

All versions return the sensor value in the form:
  "DS18B20 xx.xx.xx.xx.xx.xx.xx.xx -999.99\n"
where:
  DS18B20 is a constant telling the type of sensor
  xx.xx....xx is the sensor ID and is 8, 8 bit hex bytes
  -999.99 is the temperature in degrees C
  \n is the <new-line> character
An empty line is sent after the data for each sensor is sent.

####DS18B20.ino:
This is the most basic program.  It periodically (once every 60 seconds) looks for devices on the digital pins, for 
any DS18B20 devices found samples the temperature and returns the data.  More than one device can be attached to 
each pin.  If many devices are attached, or if there are many retries, the code might not be able to keep up with 
the 60 second period.  If this happens the code will sample as often as possible.

####DS18B20-Mock.ino:
This is very basic program that obeys the normal protocol for use with testing and developing with real sensors are 
not available.

####DS18B20-SampleOnDemand.ino:
This is the most basic program for the on-demand protocol.  When the controller sends a <new-line> character the code
looks for devices on the digital pins, and for any DS18B20 devices found samples the temperature and returns the data.
More than one device can be attached to each pin.  The controller should not send a <new-line> character till the data
from the previous request is complete.  (i.e. an empty line is received)

####DS18B20-SampleOnDemand-Mock.ino:
This is very basic program that obeys the on-demand protocol for use with testing and developing with real sensors 
are not available.

####DS18B20-Fast-SampleOnDemand.ino:
This uses the same communication protocol but the Arduino program samples the sensors in parallel rather than serially
so the data can be returned faster.  
NOTE:  At this time the code only supports a single sensor per digital pin rather than multiple DS18B20 devices per pin
as for the DS18B20.ino and DS18B20-SampleOnDemand.ino programs.

####DS18B20-Fast-SampleOnDemand-Mock.ino:
This is very basic program that obeys the on-demand protocol for use with testing and developing with real sensors 
are not available.


#Python Programs
####SampleOnDemandSensors.py
This periodically (defaults to every 10 minutes) samples the sensors and 
saves the values in /opt/Sensors/logs


#Installation and Setup
### Configure the software (15 minutes -- longer if system is not up-to-date)

This is for Raspberry Pi or Ubuntu Linux.  Setup on other systems varies.

Install python3 using a command of:

    sudo apt-get -y install python3 python3-dev git
    
Now make sure python3 is installed correctly

    $ python3 --version
    Python 3.10.2


### Install the software in the Raspberry Pi (5 minutes)

The software and scripts assume the software is installed in `/opt`, a
standard directory for "optional" software.  To install the software use

    sudo sh -c 'cd /opt ; git clone https://github.com/pgcrumley/Sensor.git'

This will place a copy of the software in `/opt` and leave behind
information that makes it easy to retrieve updates later if needed.

Next 

    cd /opt/Sensors/DS18B20-via-Arduino
    
and make sure there are a number of python programs and other scripts present.

### Attach Arduino to development system and program sketch. (15 minutes)

If you are new to Arduino you probably want to do some of the
[tutorials](https://www.arduino.cc/en/Tutorial/HomePage)

If you use a system other than your Raspberry Pi as your Arduino development
system you will need to get a copy of the `DS18B20_Fast_SampleOnDemand.ino` file
to the development system.  

Attach your Arduino to your development computer (which might be your 
Raspbery Pi) and download the sketch called `DS18B20_Fast_SampleOnDemand.ino`
using the normal Arduino tools.  

You can use the serial port of the IDE to try out the operation of the 
Arduino.  Remember to set the serial port speed to 115200.

You can read all the pin values with '?'  The version command '`' (that 
is back-tic) prints a version number.

### Attach the Arduino to the Raspberry Pi USB port (2 minutes)

Once this is working attach the Arduino to a USB port on the Raspberry Pi.

If you programmed the Arduino on the same system it is already connected but
you may need to stop the Arduino IDE to release the serial port connection.

Look for the device in `/dev`.  It will have a name such as 
`/dev/ttyxxx#  ` where `xxx` is `ACM` or `USB` depending on the 
version of Arduino card you have, and `#` is a number.

Try this: (on my example system the Arduino is connected on /dev/ttyUSB0)

    $ ./DS18B20_OnDemand_via_Arduino_Controller.py
    COM6 : DS18B20 : V4_DS18B20_Fast_SampleOnDemand
    {'28ff2c9fa2160474': 17.75, '28ff5360a0160351': 16.875}


If you don't see something like the above there is a problem.

**Note:** In the above example there are 2 DS18B20 sensors attached to the
Arduino.  If there are no sensors connected only the first 2 lines will
print.

### Run the REST server
You can try the REST server as a simple way to read temperature sensors
from any host.

    pgc@test:$ sudo su -
    root@test:/$ cd /opt/Sensors/DS18B20_via_Arduino
    root@test:/opt/Sensors/DS18B20_via_Arduino# ./DS18B20_via_Arduino_WebServer.py
    running server listening on ('0.0.0.0', 18820)...

in a different terminal try 

    $ curl localhost:18820
    {
     "28ff256ea316058c": 19.3125
    }

You can also read the temperature from a different system by using the 
IP address or name for __localhost__ .


### Set up (optional) REST server to allow reading the sensors via a network
 
The python server can be installed to run
automatically or you can start the program when you like.  

By default the code listens on IP port 18820 and allows connections from any 
system that can reach the server on the network.  

To install the server to run automatically every time the system is started
you can use this script: 

    sudo su -
    cd /opt/Sensors/DS18B20_via_Arduino
    InstallWebServer.sh
        
That will install needed packages and use a configuration which will use
any usable Arduino connected on serial ports


### Enjoy! 
