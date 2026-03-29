from machine import Pin, PWM
from utime import sleep


class Motor:
    """Controls a single DC motor with direction and PWM speed control."""

    def __init__(self, dir_pin, pwm_pin):
        self.dir_pin = Pin(dir_pin, Pin.OUT)
        self.pwm = PWM(Pin(pwm_pin))
        self.pwm.freq(1000)
        self.off()

    def off(self):
        """Stop the motor."""
        self.pwm.duty_u16(0)

    def speed(self, speed):
        """Set motor direction and speed. Positive = forward, negative = reverse, 0 = stop."""
        if speed == 0:
            self.off()
        else:
            direction = 1 if speed < 0 else 0
            self.dir_pin.value(direction)
            self.pwm.duty_u16(int(65535 * abs(speed) / 100))


class Actuator:

    def __init__(self, dir_pin, pwm_pin):
        self.dir_pin = Pin(dir_pin, Pin.OUT)
        self.pwm = PWM(Pin(pwm_pin))
        self.pwm.freq(1000)
        self.off()
        self.base_speed = 33
        self.ground_height = 0
        self.relative_height = 0

        self.reset()

    def off(self):
        """Stop the motor."""
        self.pwm.duty_u16(0)

    def speed(self, speed):
        """Set motor direction and speed. Positive = forward, negative = reverse, 0 = stop."""
        if speed == 0:
            self.off()
        else:
            direction = 1 if speed < 0 else 0
            self.dir_pin.value(direction)
            self.pwm.duty_u16(int(65535 * abs(speed) / 100))
            
    def reset(self):
        print("Resetting actuator height")
        self.speed(-self.base_speed)
        sleep(15)
        self.set_height(self.ground_height)
        self.relative_height = 0
        self.off()
            
    def set_height(self, relative_height):
        print("Setting relative height to", relative_height)
        if relative_height > self.relative_height:
            self.speed(self.base_speed)
        else:
            self.speed(-self.base_speed)
            
        sleep(abs(relative_height - self.relative_height) / (0.07 * self.base_speed))
        
        self.relative_height = relative_height
        
        self.off()
        

class Servo:
    def __init__(self, pwm_pin_no):
        self.pwm_pin = PWM(Pin(pwm_pin_no))
        self.pwm_pin.freq(50)


    def set_angle(self, angle):
        angle = max(0, min(180, angle))
        
        min_us = 500
        max_us = 2500
        us = min_us + (max_us - min_us) * angle / 180

        duty = int(us / 20000 * 65535)
        self.pwm_pin.duty_u16(duty)
        

if __name__ == "__main__":
    
    servo = Servo(15)
    servo.set_angle(0)
    sleep(1)
    servo.set_angle(180)
    
    actuator = Actuator(0, 1)
    actuator.speed(50)
    actuator.reset()
    actuator.set_height(10)
