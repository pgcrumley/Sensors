#Sensors

This project holds code to sample and monitor a variety of sensors which are
attached to Raspberry Pi systems.

The code and ancillary files assume the project is placed in /opt.  A simple 
  `sudo bash -c 'cd /opt ; git clone https://github.com:pgcrumley/Sensors.git'`
will put the code in the appropriate location.  
The code can then be updated with `git pull` commands run as root.
An example would be: `sudo bash -c 'cd /opt ; git pull'`
  
When some of the programs run they will create a directory of 
`/opt/Sensors/log` 
to hold their output.

The various sensors attach to the Raspberry Pi in a variety of ways including:

    I2C pins (i.e. data / clock are board pins 3 / 5)
      BMP280  (also needs +3.3 & Ground)
      BME280  (also needs +3.3 & Ground)
    W1 pin (board pin 7, can use different pin with /boot/config.txt parameter)
      DS18B20  (also needs +3.3 & Ground)
    USB ports
      DS18B20_via_Arduino  (also needs an Arduino with attached DS18B20 devices)
    Other GPIO pins (you pick, stay away from above and some special purpose pins)
      HTU21D  (also needs +3.3 & Ground, defaults: data/clock on board pins 11/13)
      Si702x  (also needs +3.3 & Ground, defaults: data/clock on board pins 11/13)
      HC-SR04  (also needs +5 & Ground AND the "ECHO" pin needs a voltage divider)

Simple web servers are provided for the sensors.  By default these 
only allow programs on the Raspberry Pi which with the running REST server to 
access the device.  The REST servers can be configured with command line
parameters to move the port or allow access from other systems.

The REST servers use JSON format for the data which is retrieved
from the devices.  

The default port numbers for the REST servers are:

| Port | Device |
| ---: | :----- |
| 10280 | BMP280 |
| 20280 | BME280 |
| 1820 | DS18B20 |
| 18820 | DS18B20 on Arduino |
| 2100 | HTU21D |
| 7020 | Si702x |
| 10004 | HC-SR004 |
  
  