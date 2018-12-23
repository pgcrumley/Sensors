/*
 * MIT License
 * 
 * Copyright (c) 2017, 2018 Paul G Crumley
 * 
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to deal
 * in the Software without restriction, including without limitation the rights
 * to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
 * copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:
 * 
 * The above copyright notice and this permission notice shall be included in all
 * copies or substantial portions of the Software.
 * 
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
 * OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
 * SOFTWARE.
 * 
 * @author: pgcrumley@gmail.com
 */

/*
 * This code waits for '\n' on the Serial port and when a '\n' is seen
 * the code will cycle through pins specified in PINS_TO_USE.   
 * For each sensor found the temperature is sampled and if no errors are found
 * the sample is formatted and sent out the serial port at SERIAL_BAUD_RATE baud.
 * 
 * If a '?' is received the it will return a line with the name of the
 * sketch and a version with an extra new line.
 *
 * The code allows more than one sensor to be attached to each pin.  The code simply
 * walks through all the sensors so if many devices are attached to an Arduino it can
 * take many seconds to retrieve all the samples.
 *
 * Data is in the format of:
 *   "DS18B20 AA.AA.AA.AA.AA.AA.AA.AA   DD.DDDD\n"
 * where:
 *   DS18B20 indicates the sensor type
 *   AA....AA is the device ID
 *   DD.DDDD is degrees Celsius -- possibly negative
 *
 * Malformed data is silently discarded.
 */

#include <OneWire.h>

#define DEBUG 0
#define SERIAL_BAUD_RATE 115200
#define SAMPLE_DELAY_IN_MSEC 30000

#define DS18B20_BYTES_IN_ADDRESS 8
#define DS18B20_BYTES_IN_DATA 8
#define DS18B20_BYTES_IN_DATA_PLUS_CRC 9
#define DS18B20_ID_CONSTANT (0x28)
#define DS18B20_CONVERSION_TIME_IN_MSEC (760)  /* spec says 750 */

/* the code will look for DS18B20 sensors on these pins */
const byte PINS_TO_USE[] = { 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13 };

void setup(void) {
  for (int i = 0 ; i < sizeof(PINS_TO_USE); i++) {
    pinMode(PINS_TO_USE[i], OUTPUT);
  }
  Serial.begin(SERIAL_BAUD_RATE);
}

/* 
   Format the address & temperature then
   send the output for a sensor out the serial port 
*/
void sendOutput(byte addr[], byte data[]) {

  int16_t raw_temp = (data[1] << 8) | (0xff & data[0]);
  float temp = raw_temp * 1.0;
  temp = temp / 16.0;
  char temp_str[] = "\0\0\0\0\0\0\0\0\0\0\0\0"; // more than needed
  dtostrf(temp, 9, 4, temp_str);

  char output_str[] = "DS18B20 xx.xx.xx.xx.xx.xx.xx.xx -999.99\n\0\0\0\0";
  sprintf(output_str, "DS18B20 %02x.%02x.%02x.%02x.%02x.%02x.%02x.%02x %s\n", 
          addr[0], addr[1], addr[2], addr[3], addr[4], addr[5], addr[6], addr[7], 
          temp_str);
  Serial.print(output_str);
} // sendOutput

/*  
 *   return 0 if success, < 0 if problem.
 *   Assume data is always overwritten.
 */
int getSample(OneWire ds, byte addr[], byte data[]) {
  byte present = 0;

  present = ds.reset();
  if (0 == present) {
    if (DEBUG) {
      Serial.print("! no initial PRESENCE returned\n");
    }
    return -1;
  }
  ds.select(addr);
  ds.write(0x44,1);         // start conversion, with parasite power on at the end

  delay(DS18B20_CONVERSION_TIME_IN_MSEC);
  // we could do a ds.depower() here, but the reset will take care of it.

  present = ds.reset();
  if (0 == present) {
    if (DEBUG) {
      Serial.print("! no second PRESENCE returned\n");
    }
    return -2;
  }
  ds.select(addr);    
  ds.write(0xBE);         // Read Scratch Pad

  for (int i = 0; i < DS18B20_BYTES_IN_DATA_PLUS_CRC; i++) {
    data[i] = ds.read();
  }
  byte crc = OneWire::crc8( data, DS18B20_BYTES_IN_DATA);
  if (data[(DS18B20_BYTES_IN_DATA_PLUS_CRC - 1)] != crc) {
    if (DEBUG) {
      Serial.print("! CRC mismatch\n");
    }
    return -10;
  }

  if (0 == data[0] &&
      0 == data[1] &&
      0 == data[2] &&
      0 == data[3] &&
      0 == data[4] &&
      0 == data[5] &&
      0 == data[6] &&
      0 == data[7]) {
        if (DEBUG) {
          Serial.println("all data bytes == 0");
        }
        return -11;
      }

  if (DEBUG) {
    Serial.print("P=");
    Serial.print(present,HEX);
    Serial.print(" ");
    for (int i = 0; i < DS18B20_BYTES_IN_DATA_PLUS_CRC; i++) {
      Serial.print(data[i], HEX);
      Serial.print(" ");
    }

    Serial.print(" CRC=");
    Serial.print( crc, HEX);
    Serial.print("\n");
  }
  
  return 0;  // success
}  // getSample()


void sampleSensors() {    
  /* loop through all the pins we are given to search */
  for (int i = 0; i < sizeof(PINS_TO_USE); i++) {
    int pin = PINS_TO_USE[i];
    if (DEBUG) {
      Serial.println(pin);
    }
    OneWire ds(pin);

    /* find all one-wire devices and 
       if a DS18B20 try to read the temperature */
    byte addr[DS18B20_BYTES_IN_ADDRESS];
    ds.reset_search();
    while ( ds.search(addr)) {
      if (DS18B20_ID_CONSTANT == addr[0]) { // only try to read DS18B20 devices
        int rc = 1;
        /* normally leave this loop via break */
        for (int retry = 0; retry < 5; retry++) {
          byte data[DS18B20_BYTES_IN_DATA_PLUS_CRC];
          rc = getSample(ds, addr, data);
          if (0 == rc) {
            sendOutput(addr, data);
            break;
          }
        } // for retry
      } // if (DS18B20_ID_CONSTANT == ...
    }
    if (DEBUG) {
      Serial.println("done with loop().  waiting....");
    }
  }
  /* indicate all sensors have been sampled */
  Serial.write('\n');
}


void loop(void) {
  /* wait till the controller tells us to take samples by sending a '\n' */
  int ch = Serial.read();
  if (ch == '\n') {
    sampleSensors();
  } else if (ch == '?') {
    Serial.println("DS18B20_SampleOnDemand_V2\n");
  }
} // loop()
