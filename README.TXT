This project holds code to sample and monitor a variety of sensors which are
attached to Raspberry Pi systems.

The code and ancillary files assume the project is placed in /opt.  A simple 
  sudo bash -c ' cd /opt ; git clone git@github.com:pgcrumley/Sensors.git '
will put the code in the appropriate location.  git pulls will obtain updates.
  
When some of the programs run they will create a directory of /opt/Sensors/log to 
hold their output.

The various sensors attach to the Raspberry Pi in a variety of ways including:
  I2C pins (i.e. board pins 3 & 5)
    BMP280  (also needs +3.3 & Ground)
    BME280  (also needs +3.3 & Ground)
  W1 pin (i.e. board pin 7)
    DS18B20  (also needs +3.3 & Ground)
  USB ports
    DS18B20-On-Arduino  (also needs an Arduino attached DS18B20 devices)
  Other GPIO pins (you pick but stay away from above and some special purpose pins)
    HTU21D  (also needs +3.3 & Ground, defaults: data / clock on board pins 11 / 13)
    Si702x  (also needs +3.3 & Ground, defaults: data / clock on board pins 11 / 13)
    HC-SR04  (also needs +5 & Ground AND the "ECHO" pin needs a voltage divider)

    