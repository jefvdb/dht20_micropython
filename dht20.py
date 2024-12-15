"""
Asair DHT20, I2C humidity & temperature sensor driver for MicroPython
jef@slechte.info, 2024-12
MIT license
vim: expandtab sw=4 ts=4 :

History:
    * 2024-12 initial release, tested on MicroPython v1.24.1 on ESP32

Usage (with this file as /lib/dht20.py):

import machine
from dht20 import DHT20

i2c = machine.SoftI2C(scl=machine.Pin(22), sda=machine.Pin(21))
dht = DHT20(i2c)

rh, t = dht.get_humidity_temperature()

"""
import struct
import time


class DHT20:
    def __init__(self, bus, address=0x38):
        self.bus = bus
        self.address = address

        """
        datasheet: send it 0x71 to initialize, the return should
        contain bits 0x18, if not then more initialization is needed
        but this is not detailed in the datasheet

        datasheet: wait at least 100ms after power-on before initializing

        datasheet: wait at least 10ms after initialization before talking to it
        """

        self.bus.writeto(self.address, b'\x71')

        check = self.bus.readfrom(self.address, 1)[0]
        if (check & 0x18) != 0x18:
            raise IOError

    def get_humidity_temperature(self):
        """
        since this involves waiting on the sensor, return both in one go
        as a (relative_humidity, temperature) tuple)
        """

        """
        datasheet; send it 0xac, 0x33, 0x00 to start a reading, which should
        take around 80ms

        my module here however is ready at around 50ms, so polling from
        there on out

        datasheet: a CRC8 is returned, which we don't use, same for the CAL bit
        """
        self.bus.writeto(self.address, b'\xac\x33\x00')

        time.sleep(0.050)

        while self.bus.readfrom(self.address, 1)[0] & 0x80:
            time.sleep(0.010)

        data = struct.unpack('>BHHH', self.bus.readfrom(self.address, 7))

        rh = (data[1] << 4) | (data[2] >> 12)
        t = ((data[2] & 0x0fff) << 8) | ((data[3] & 0xff) >> 8)

        rh = (rh / 0x100000) * 100
        t = (t / 0x100000) * 200 - 50

        return (rh, t)
