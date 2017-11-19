"""
MIT License

Copyright (c) 2016 - 2017 Paul G Crumley

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

"""

import time
import RPi.GPIO as GPIO

"""
SEND_START
SEND_RESTART
SEND_STOP

SEND_1_BIT
SEND_0_BIT
SEND_BYTE
RECV_BYTE
SEND_ACK
SEND_NACK
RECV_ACK

DELAY

TO DO:
-- Create state machine for these classes in order to reduce # of transitions needed and hence run faster
-- Could use 4.7 uS and 4.0 uS for minimum LOW and HIGH clock times respectively.
---- Need to not violate max clock freq as seen between falling clock edges.
-- Could overlap data hold time with clock lOW time???
-- Only need 250 nS for data setup time for normal data (not START / STOP / RESTART)
-- Validate arbitration design and implementation (probably check data after rising clock edge is seen, yes?)
---- decide how to deal with lost arbitration (wait, return error, exception?  -- probably exception by default)
-- Look for transitions before starting a transfer
-- Create test suite?
-- Consider modes to trim spec (e.g. only look for clock stretching between bytes)
-- The I2C suggestions that a Stuck Data line be cleared by sending 9 clocks, checking that the slave releases after each.
-- Implement the DEVICE-ID command (0xF8)?  Note: must use RESTART


"""



class I2cIllegalStateError(Exception):
    """
    raised when a function expects the HW or SW to be in a particular defined
    state before the operation can be successfully carried out and the HW or SW
    state is not defined or is in a defined state but that defined state is not 
    valid for the operation to take place.
    """
    def __init__( self, exception_text ):
        self.exception_text = exception_text
        Exception.__init__(self, exception_text)
        
class I2cInvalidArgumentError(Exception):
    """
    raised when the value of an argument is not a legal value.
    """
    def __init__( self, exception_text ):
        self.exception_text = exception_text
        Exception.__init__(self, exception_text)
        
class I2cLostArbitration(Exception):
    """
    raised when a master determines some other master is transmitting and this 
    master has lost the arbitration.
    """
    def __init__( self, exception_text ):
        self.exception_text = exception_text
        Exception.__init__(self, exception_text)
        
        

class I2cPort:
    VALID_ADDRESS_LIST = range(0x08, 0x78)
    
    MIN_CLOCK_CYCLE_SEC = 1.0 / 100000.0  # no more than 100KHz as seen at falling clock edges

    MIN_LOW_TIME_SEC  = 4.7   / 1000000.0   # minimum width of low clock
    MIN_HIGH_TIME_SEC = 4.0   / 1000000.0   # minimum width of high clock
    MIN_DATA_SETUP_SEC = 0.25 / 1000000.0 # data must be valid at least 250 nSec before rising clock
    
    MAX_CLOCK_RISE_TIME_SEC = 10.0        # timeout after this time if the clock signal does not rise
    MAX_CLOCK_FALL_TIME_SEC = 5.0         # timeout after this time if the clock signal does not fall
    MAX_DATA_RISE_TIME_SEC = 5.0          # timeout after this time if the data signal does not rise
    MAX_DATA_FALL_TIME_SEC = 5.0          # timeout after this time if the data signal does not fall
    
    DEFAULT_DEBOUNCE_TIME = 1 / 1000000.0  # de-bounce signals for at least 1 uSec
    
    def __init__(self, clock_pin=0, data_pin=0):
        '''
        Must provide clock_pin and data_pin values between 1 and 39
        '''
        if (clock_pin < 1 or clock_pin > 39):
            raise ValueError('clock_pin value of {} is not between 0 and 39'.format(clock_pin))
        if (data_pin < 1 or data_pin > 39):
            raise ValueError('data_pin value of {} is not between 0 and 39'.format(data_pin))

        self.clock_pin = clock_pin
        self.data_pin = data_pin
        
        GPIO.setmode(GPIO.BOARD)
        self.set_idle()
        self.state = 'initialized'

#     def __del__(self):
#         GPIO.setup(self.data_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#         GPIO.setup(self.clock_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
#         
#         self.state = 'deleted'

    def read_clock(self):
        """
        Return current value of clock pin.
        """
        value = GPIO.input(self.clock_pin)
        return value

    def read_data(self):
        """
        Return current value of data pin.
        """
        value = GPIO.input(self.data_pin)
        return value

    def read_stable_clock(self, debounce_time=DEFAULT_DEBOUNCE_TIME):
        """
        Return the value of a pin after the same value has been sampled twice with at least the debounce time between.
        """
        last_value = self.read_clock()
        while True:
            done_time = time.time() + debounce_time
            while done_time > time.time():
                pass
            value = self.read_clock()
            if value == last_value:
                return value
            last_value = value

    def raise_clock(self, timeout=MAX_CLOCK_RISE_TIME_SEC):
        """
        Verify clock pin is low, if not low return -1
        Set mode of clock pin to be input with pull up
        Determine timeout time
        Loop till timeout occurs, waiting for clock pin to be high then return 1
        if timeout occurs raise I2cIllegalStateError
        """
# TBD        if self.read_clock() is not 0:
# TBD            print('clock not low in raise_clock')
# TBD             raise I2cIllegalStateError('clock is not low at start of raise_clock()')

        GPIO.setup(self.clock_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        timeout_time = time.time() + timeout
        while time.time() < timeout_time:
            if GPIO.input(self.clock_pin) is 1:
                return 1
            
        raise I2cIllegalStateError('clock did not rise before timeout')

    def lower_clock(self, timeout=MAX_CLOCK_FALL_TIME_SEC):
        """
        Verify clock pin is high, if not high return -1
        Set mode of clock pin to be output with low value
        Determine timeout time
        Loop till timeout occurs, waiting for clock pin to be low then return 0
        if timeout occurs raise I2cIllegalStateError
        """
# TBD        if self.read_clock() is not 1:
# TBD            print('clock not high in lower_clock')
# TBD            raise I2cIllegalStateError('clock is not high at start of lower_clock()')

        GPIO.setup(self.clock_pin, GPIO.OUT, initial=0)
        
        timeout_time = time.time() + timeout
        while time.time() < timeout_time:
            if GPIO.input(self.clock_pin) is 0:
                return 0
            
        raise I2cIllegalStateError('clock did not fall before timeout')

    def raise_data(self, timeout=MAX_DATA_RISE_TIME_SEC):
        """
        Set mode of data pin to be input with pull up
        Determine timeout time
        Loop till timeout occurs, waiting for data pin to be high then return 1
        if timeout occurs raise I2cIllegalStateError
        """
        GPIO.setup(self.data_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

        timeout_time = time.time() + timeout
        while time.time() < timeout_time:
            if GPIO.input(self.data_pin) is 1:
                return 1
            
        raise I2cIllegalStateError('data did not rise before timeout')

    def float_data(self):
        """
        Set mode of data pin to be input with pull up
        Some other device might be pulling the data signal down so we can't be sure of the value
        """
        GPIO.setup(self.data_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def lower_data(self, timeout=MAX_DATA_FALL_TIME_SEC):
        """
        Set mode of data pin to be output with low value
        Determine timeout time
        Loop till timeout occurs, waiting for clock to be low then return 0
        if timeout occurs raise I2cIllegalStateError
        """
        GPIO.setup(self.data_pin, GPIO.OUT, initial=0)

        timeout_time = time.time() + timeout
        while time.time() < timeout_time:
            if GPIO.input(self.data_pin) is 0:
                return 0
            
        raise I2cIllegalStateError('data did not fall before timeout')

    def set_idle(self):
        """
        Ignores current state and puts clock and data pins in high state using pulls ups.
        TBD -- try to do a better job with this from various states
        """
        GPIO.setup(self.data_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        GPIO.setup(self.clock_pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    def send_start(self):
        """
        Clock and data must be high to begin a START symbol
        If they are not high, raise I2cIllegalStateError

        After delaying with both high, drop data
        Then delay then drop clock and delay
        """
        if (self.read_clock() is 0 or self.read_data() is 0):
            raise I2cIllegalStateError("can not begin START symbol unless clock and data are both high")
        end_time = time.time() + I2cPort.MIN_HIGH_TIME_SEC
        while time.time() < end_time:
            pass  # delay
        
        self.lower_data()
        end_time = time.time() + I2cPort.MIN_LOW_TIME_SEC
        while time.time() < end_time:
            pass  # delay        
        self.lower_clock()
        end_time = time.time() + I2cPort.MIN_LOW_TIME_SEC
        while time.time() < end_time:
            pass  # delay        

    def send_restart(self):
        """
        If the clock is not low raise I2cIllegalStateError


        """    
        if self.read_clock() is not 0:
            raise I2cIllegalStateError('can not start STOP symbol with clock in high state')
        
        end_time = time.time() + I2cPort.MIN_LOW_TIME_SEC
        while time.time() < end_time:
            pass  # delay
        self.raise_data()
        end_time = time.time() + I2cPort.MIN_HIGH_TIME_SEC
        while time.time() < end_time:
            pass  # delay
        self.raise_clock()
        end_time = time.time() + I2cPort.MIN_HIGH_TIME_SEC
        while time.time() < end_time:
            pass  # delay

        self.lower_data()
        end_time = time.time() + I2cPort.MIN_LOW_TIME_SEC
        while time.time() < end_time:
            pass  # delay        
        self.lower_clock()
        end_time = time.time() + I2cPort.MIN_LOW_TIME_SEC
        while time.time() < end_time:
            pass  # delay        

    def send_stop(self):
        """
        Clock and data must be low to begin a STOP symbol
        If clock is not low raise I2cIllegalStateError
        With clock low, ensure data is low
        Then raise clock then raise data
        """    
        if self.read_clock() is not 0:
            raise I2cIllegalStateError('can not start STOP symbol with clock in high state')
        end_time = time.time() + I2cPort.MIN_LOW_TIME_SEC
        while time.time() < end_time:
            pass  # delay
        self.lower_data()
        end_time = time.time() + I2cPort.MIN_LOW_TIME_SEC
        while time.time() < end_time:
            pass  # delay
        self.raise_clock()
        end_time = time.time() + I2cPort.MIN_HIGH_TIME_SEC
        while time.time() < end_time:
            pass  # delay
        self.raise_data()
        end_time = time.time() + I2cPort.MIN_HIGH_TIME_SEC
        while time.time() < end_time:
            pass  # delay

    def send_bit(self, value):
        """
        Send a bit of value on the I2C port.
        Check the data signal before dropping the clock to ensure that no other master is driving the signal and that this master
        has lost the arbitration.
        Return value, or raise I2cLostArbitration exception if the master lost arbitration
        """
        if (value is 0) or (value is 1):
            self.lower_clock()
            end_time = time.time() + I2cPort.MIN_LOW_TIME_SEC
            while time.time() < end_time:
                pass  # delay till clock high time has passed

            if value:
                self.raise_data()
            else:
                self.lower_data()

            self.raise_clock()
            end_time = time.time() + I2cPort.MIN_HIGH_TIME_SEC
            while time.time() < end_time:
                pass  # delay till clock high time has passed
            read_value = self.read_data()
            if read_value is not value:
                raise I2cLostArbitration('master lost arbitration')

            self.lower_clock()
            end_time = time.time() + I2cPort.MIN_LOW_TIME_SEC
            while time.time() < end_time:
                pass  # delay till clock high time has passed

            return read_value

        else:
            raise I2cInvalidArgumentError('bit value of {} is not o or 1'.format(value))

    def send_ack(self, ack):
        """"
        send an ack bit
        raise I2cInvalidArgumentError if ack is not a bool
        """
        if not isinstance(ack, bool):
            raise I2cInvalidArgumentError("ack to send must be a bool")
        if ack:
            self.send_bit(0)
        else:
            self.send_bit(1)

    def receive_bit(self):
        """
        Send a bit of value '1' on the I2C port.
        Sample the data signal before dropping the clock and return the value.
        """

        self.lower_clock()
        end_time = time.time() + I2cPort.MIN_LOW_TIME_SEC
        while time.time() < end_time:
            pass  # delay till clock high time has passed

        self.float_data()

        self.raise_clock()
        end_time = time.time() + I2cPort.MIN_HIGH_TIME_SEC
        while time.time() < end_time:
            pass  # delay till clock high time has passed
        read_value = self.read_data()
        
        self.lower_clock()
        end_time = time.time() + I2cPort.MIN_LOW_TIME_SEC
        while time.time() < end_time:
            pass  # delay till clock high time has passed
        
        return read_value

    def receive_ack(self):
        """
        Send a bit of floated data on the I2C port.
        Sample the data signal before dropping the clock and return the value.
        """
        return self.receive_bit() is 0

    def send_byte(self, value):
        """"
        send one byte of data, MSbit first
        read an ACK bit and return that bit
        raise I2cInvalidArgumentError if value is < 0 or > 255
        raise I2cIllegalStateError if the port is in a problem state
        """
        if (value < 0 or value > 255):
            raise I2cInvalidArgumentError("value to send must be > -1 and < 256")
        for i in range(8):
            bit_to_send = (value >> (7-i)) & 1
            self.send_bit(bit_to_send)
        ack = self.receive_ack()
        return ack

    def receive_byte(self, ack):
        """"
        receive one byte of data, MSbit first
        send an ACK bit
        return the read byte
        raise I2cInvalidArgumentError if akc is not a bool
        raise I2cIllegalStateError if the port is in a problem state
        """
        if not isinstance(ack, bool):
            raise I2cInvalidArgumentError("ack to send must be a bool")
        result = 0
        for _ in range(8):
            result = result << 1
            b = self.receive_bit()
            result = result | b
        self.send_ack(ack)
        return result

    def ping_address(self, addr):
        """
        send a byte with the addr (shifted a bit left) and 0 for WRITE
        return the ACK from that send
        raise I2cInvalidArgumentError if addr is < 0 or > 127
        raise I2cIllegalStateError if the port is in a problem state
        """
        if addr not in self.VALID_ADDRESS_LIST:
            raise I2cInvalidArgumentError("address to ping must be >= {} and <= {}".format(self.VALID_ADDRESS_LIST[0], self.VALID_ADDRESS_LIST[:1]))
        
        value = addr << 1
        self.send_start()
        ack = self.send_byte(value)
        self.send_stop()
        
        return ack

class I2cDevice():
    """
    This provides ways to interact with a device at a particular address on a given I2cPort.
    """
        
    def __init__(self, i2c_port, device_address):
        if device_address not in i2c_port.VALID_ADDRESS_LIST:
            raise I2cInvalidArgumentError('device_address of {} is not valid'.format(device_address))
        self.port = i2c_port
        self.addr = device_address
        self.addr_byte_for_write = self.addr << 1
        self.addr_byte_for_read = self.addr_byte_for_write | 1
        if not self.port.ping_address(self.addr):
            raise I2cIllegalStateError('no device detected at address {}'.format(self.addr))

    def send_bytes_no_offset(self, data):
        """
        Send the given list of data bytes to the device without sending an offset.
        Return the last ack from the device
        """
        p = self.port
        
        p.send_start()
        ack = p.send_byte(self.addr_byte_for_write)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack its address')
        ack = False
        for d in data:
            ack = p.send_byte(d)
        p.send_stop()
        return ack

    def receive_bytes_no_offset(self, count):
        """
        Receive count bytes from the device without sending an offset.
        Send NACK on last byte read
        return the list of data bytes received from the device
        """
        p = self.port
        
        p.send_start()
        ack = p.send_byte(self.addr_byte_for_read)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack its address')
        result = []
        for i in range(count):
            result.append(p.receive_byte(i < (count - 1)))
            
        p.send_stop()

        return result

    def send_bytes_8bit_offset(self, offset, data):
        """
        Send the given list of data bytes to the device after sending 8 bits of offset.
        Only the 8 low order bits of offset are used, the rest are ignored.
        Return the last ack from the device
        """
        p = self.port
        
        p.send_start()
        ack = p.send_byte(self.addr_byte_for_write)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack its address')
        ack = p.send_byte(offset & 0xff)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack after offset')
        ack = False
        for d in data:
            ack = p.send_byte(d)
        p.send_stop()
        return ack

    def receive_bytes_8bit_offset(self, offset, count):
        """
        Receive count bytes from the device after sending 8 bits of offset.
        Only the 8 low order bits of offset are used, the rest are ignored.
        Send NACK on last byte read
        return the list of data bytes received from the device
        """
        p = self.port
        
        p.send_start()
        ack = p.send_byte(self.addr_byte_for_write)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack its address')
        ack = p.send_byte(offset & 0xff)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack after offset')
        p.send_restart()
        
        ack = p.send_byte(self.addr_byte_for_read)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack its address')

        result = []
        for i in range(count):
            result.append(p.receive_byte(i < (count - 1)))
            
        p.send_stop()

        return result

    def send_bytes_16bit_offset(self, offset, data):
        """
        Send the given list of data bytes to the device after sending 16 bits of offset.
        Only the 16 low order bits of offset are used, the rest are ignored.
        Return the last ack from the device
        """
        p = self.port
        
        p.send_start()
        ack = p.send_byte(self.addr_byte_for_write)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack its address')
        ack = p.send_byte((offset >> 8) & 0xff)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack after offset')
        ack = p.send_byte(offset & 0xff)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack after offset')
        ack = False
        for d in data:
            ack = p.send_byte(d)
        p.send_stop()
        return ack

    def receive_bytes_16bit_offset(self, offset, count):
        """
        Receive count bytes from the device after sending 16 bits of offset.
        Only the 16 low order bits of offset are used, the rest are ignored.
        Send NACK on last byte read
        Return a list of data bytes received
        """
        p = self.port
        
        p.send_start()
        ack = p.send_byte(self.addr_byte_for_write)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack its address')
        ack = p.send_byte((offset >> 8) & 0xff)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack after offset')
        ack = p.send_byte(offset & 0xff)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack after offset')
        p.send_restart()
        
        ack = p.send_byte(self.addr_byte_for_read)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack its address')

        result = []
        for i in range(count):
            result.append(p.receive_byte(i < (count - 1)))
            
        p.send_stop()

        return result

    def send_bytes_32bit_offset(self, offset, data):
        """
        Send the given list of data bytes to the device after sending 32 bits of offset.
        Only the 32 low order bits of offset are used, the rest are ignored.
        Return the last ack from the device
        """
        p = self.port
        
        p.send_start()
        ack = p.send_byte(self.addr_byte_for_write)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack its address')
        ack = p.send_byte((offset >> 24) & 0xff)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack after offset')
        ack = p.send_byte((offset >> 16) & 0xff)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack after offset')
        ack = p.send_byte((offset >> 8) & 0xff)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack after offset')
        ack = p.send_byte(offset & 0xff)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack after offset')
        ack = False
        for d in data:
            ack = p.send_byte(d)
        p.send_stop()
        return ack

    def receive_bytes_32bit_offset(self, offset, count):
        """
        Receive count bytes from the device after sending 32 bits of offset.
        Only the 32 low order bits of offset are used, the rest are ignored.
        Send NACK on last byte read
        return the list of data bytes received from the device
        """
        p = self.port
        
        p.send_start()
        ack = p.send_byte(self.addr_byte_for_write)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack its address')
        ack = p.send_byte((offset >> 24) & 0xff)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack after offset')
        ack = p.send_byte((offset >> 16) & 0xff)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack after offset')
        ack = p.send_byte((offset >> 8) & 0xff)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack after offset')
        ack = p.send_byte(offset & 0xff)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack after offset')
        p.send_restart()
        
        ack = p.send_byte(self.addr_byte_for_read)
        if not ack:
            p.send_stop()
            raise I2cIllegalStateError('device did not ack its address')

        result = []
        for i in range(count):
            result.append(p.receive_byte(i < (count - 1)))
            
        p.send_stop()

        return result


        
# ################################################################
    
def scan_i2c_port(clock_pin, data_pin):
    """
    TBD how to make this a class method?
    """
    port = I2cPort(clock_pin=clock_pin, data_pin=data_pin)
    port.set_idle()
    port.set_idle()
    print('')
    print('scanning clock_pin={}, data_pin={}'.format(clock_pin, data_pin))
    total_time = 0.0
    for a in port.VALID_ADDRESS_LIST:
        st = time.time()
        ack = port.ping_address(a)
        total_time += (time.time() - st)
        if ack:
            print('got ACK from address 0x{:X}'.format(a))
              
    print('average ping time is {} mSec'.format(1000.0 * total_time / len(port.VALID_ADDRESS_LIST)))
    print('')
    GPIO.cleanup()
