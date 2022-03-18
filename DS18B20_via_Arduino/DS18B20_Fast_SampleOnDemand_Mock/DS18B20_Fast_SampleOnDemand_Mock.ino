/*
 * MIT License
 *
 * Copyright (c) 2017, 2022 Paul G Crumley
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
 * This code emits valid data to test DS18B20 consumption code with an
 * Arduino but no sensors.
 *
 * This code waits for '\n' on the Serial port and when a "\n" is seen
 * the code will send data out the serial port at SERIAL_BAUD_RATE baud.
 *
 * If a '?' is received the it will return a line with the name of the
 * sketch and a version with an extra new line.
 *
 * Data is in the format of:
 *   "DS18B20 AA.AA.AA.AA.AA.AA.AA.AA   DD.DDDD\n"
 * where:
 *   DS18B20 indicates the sensor type
 *   AA....AA is the device ID
 *   DD.DDDD is degrees Celsius -- possibly negative
 *
 * Malformed data is silently discarded.
 *
 * V2   '?' command provides version info
 * V3   Respond to '\r' the same as '\n'
 * V4   NOTE:  Commands are changed!
 *      '`' for version, '?' for samples, '\r' and '\n' are ignored with other commands
 *
 */


// DS18S20 Temperature chip i/o

int use_new_commands = 0;  /* start using execution using the old commands */

#define DEBUG 0
#define SERIAL_BAUD_RATE 115200

#define DS18B20_BYTES_IN_ADDRESS 8
#define DS18B20_BYTES_IN_DATA 8
#define DS18B20_BYTES_IN_DATA_PLUS_CRC 9
#define DS18B20_ID_CONSTANT (0x28)
#define DS18B20_CONVERSION_TIME_IN_MSEC (760)  /* spec says 750 */

void setup(void) {
  Serial.begin(SERIAL_BAUD_RATE);
}

/*
   Format the address & temperture then
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

/* Mock data */
byte addr1[] = {0x28, 0xff, 0x21, 0x43, 0x65, 0x87, 0xa9, 0xff};
byte data1[] = {0x52, 0x01, 0x4B, 0x46, 0x7F, 0xFF, 0x0C, 0x10, 0x07};
byte addr2[] = {0x28, 0xff, 0x12, 0x34, 0x56, 0x78, 0x9a, 0xff};
byte data2[] = {0x75, 0x01, 0x4B, 0x46, 0x7F, 0xFF, 0x0C, 0x10, 0x07};

/*
   Where the work is done
*/
void sampleSensors() {
  // first fake sample
  delay(DS18B20_CONVERSION_TIME_IN_MSEC+10);  // delay a bit as the real one would
  sendOutput(addr1, data1);

  // second fake sample
  delay(10);  // a bit more delay
  sendOutput(addr2, data2);

  /* indicate all sensors have been sampled */
  Serial.write('\n');
}


void loop(void) {
    /* wait till the controller tells us to take samples by sending a '\n' */
    int ch = Serial.read();
    if (ch > 0) {
      if (DEBUG) {
        Serial.print("Command: 0x");
        Serial.print(ch, HEX);
        Serial.print('\n');
      }
    }
    if ('`' == ch) {  /* switch to new command set once a '`' is received */
      use_new_commands = 1;
    }

    if (use_new_commands) {
      if ('?' == ch) {
        sampleSensors();
      } else if ('`' == ch) {
        Serial.println("V4_DS18B20_Fast_SampleOnDemand_Mock");
      }
    } else {
      /* use old commands */
      if ((ch == '\n') || (ch == '\r')) {
        sampleSensors();
      } else if (ch == '?') {
        Serial.println("DS18B20_Fast_SampleOnDemand_Mock_V4\n");
      }
    }
} // loop()
