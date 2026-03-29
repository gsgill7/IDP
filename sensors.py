from machine import Pin, I2C
import time
import math

from libs.VL53L0X.VL53L0X import VL53L0X

# TCS34725 I2C address
TCS34725_ADDR = 0x29
COMMAND_BIT = 0x80

# Register addresses
REG_ENABLE = 0x00
REG_ATIME = 0x01
REG_CONTROL = 0x0F
REG_ID = 0x12
REG_CDATAL = 0x14  # Clear channel data low byte
REG_RDATAL = 0x16
REG_GDATAL = 0x18
REG_BDATAL = 0x1A

# Enable register bits
ENABLE_AEN = 0x02  # RGBC enable
ENABLE_PON = 0x01  # Power ON


class LineSensor:
    """Reads digital line sensor values."""

    @staticmethod
    def read(pin_num):
        """Read a sensor value from a pin number."""
        return Pin(pin_num, Pin.IN, Pin.PULL_UP).value()



class TCS34725:
    def __init__(self, i2c, integration_time=0xEB, gain=0x01):
        self.i2c = i2c
        self.integration_time = integration_time
        self.gain = gain

        # Check sensor ID
        sensor_id = self._read8(REG_ID)
        if sensor_id not in (0x44, 0x10):
            raise RuntimeError("TCS34725 not found or wrong ID: 0x{:02X}".format(sensor_id))

        # Set integration time and gain
        self._write8(REG_ATIME, self.integration_time)
        self._write8(REG_CONTROL, self.gain)

        # Enable the device
        self.enable()

    def enable(self):
        self._write8(REG_ENABLE, ENABLE_PON)
        time.sleep_ms(3)
        self._write8(REG_ENABLE, ENABLE_PON | ENABLE_AEN)

    def disable(self):
        reg = self._read8(REG_ENABLE)
        self._write8(REG_ENABLE, reg & ~(ENABLE_PON | ENABLE_AEN))

    def _read8(self, reg):
        return self.i2c.readfrom_mem(TCS34725_ADDR, COMMAND_BIT | reg, 1)[0]

    def _read16(self, reg):
        data = self.i2c.readfrom_mem(TCS34725_ADDR, COMMAND_BIT | reg, 2)
        return data[1] << 8 | data[0]

    def _write8(self, reg, value):
        self.i2c.writeto_mem(TCS34725_ADDR, COMMAND_BIT | reg, bytes([value]))

    def read_raw(self):
        """Returns raw (clear, red, green, blue) values."""
        clear = self._read16(REG_CDATAL)
        red = self._read16(REG_RDATAL)
        green = self._read16(REG_GDATAL)
        blue = self._read16(REG_BDATAL)
        return clear, red, green, blue

    def calculate_color_temperature(self, r, g, b):
        """Approximate color temperature in Kelvin."""
        if r == 0 or g == 0 or b == 0:
            return 0
        X = (-0.14282 * r) + (1.54924 * g) + (-0.95641 * b)
        Y = (-0.32466 * r) + (1.57837 * g) + (-0.73191 * b)
        Z = (-0.68202 * r) + (0.77073 * g) + (0.56332 * b)
        if X + Y + Z == 0:
            return 0
        xc = X / (X + Y + Z)
        yc = Y / (X + Y + Z)
        n = (xc - 0.3320) / (0.1858 - yc)
        return int((449 * (n ** 3)) + (3525 * (n ** 2)) + (6823.3 * n) + 5520.33)

    def calculate_lux(self, r, g, b):
        """Approximate lux value."""
        return int((-0.32466 * r) + (1.57837 * g) + (-0.73191 * b))
    
    def normalize(self, r, g, b, c):
        if c == 0:
            return 0, 0, 0
        return r/c, g/c, b/c

    def classify_color(self, rn, gn, bn, temp):
        if rn > gn and rn > bn:
            return "RedJunction"
        if bn > rn and bn > gn and temp<10000:
            return "BlueJunction"
        if bn > gn > rn and (gn - rn) > 0.10 and temp>10000:
            return "GreenJunction"
        if (gn > rn) and bn < 0.35 and (gn + rn) > 0.60:
            return "YellowJunction"
        return "GreenJunction"
    
    def get_color(self):
        clear, red, green, blue = self.read_raw()
        temp = self.calculate_color_temperature(red, green, blue)
        lux = self.calculate_lux(red, green, blue)

        rn, gn, bn = self.normalize(red, green, blue, clear)
        return self.classify_color(rn, gn, bn, temp)


class VL53l0X:
    def __init__(self, i2c):
        self.i2c = i2c
        self.vl53l0 = VL53L0X(i2c)
        
        self.vl53l0.set_Vcsel_pulse_period(vl53l0.vcsel_period_type[0], 18)
        self.vl53l0.set_Vcsel_pulse_period(vl53l0.vcsel_period_type[1], 14)

        self.vl53l0.start()
        
    def distance(self):
        
        return self.vl53l0.read()