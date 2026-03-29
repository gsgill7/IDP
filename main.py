from machine import Pin, I2C
import time

from robot import Robot
from actuators import Actuator
from sensors import TCS34725, VL53L0X

# ------------------ MAIN ------------------

if __name__ == "__main__":
    robot = Robot()
    
    button = Pin(12, Pin.IN, Pin.PULL_DOWN)
    
    colour_sensor_power = Pin(22, Pin.OUT)
    colour_sensor_power.value(0)
    
    i2c_0 = I2C(0, scl=Pin(17), sda=Pin(16), freq=400000)
    i2c_1 = I2C(1, sda=Pin(18), scl=Pin(19))
    
    actuator = Actuator(0, 1)
    actuator.set_height(30)
    
    distance_sensor = VL53L0X(i2c_1)

    print("Robot initialized. Press button to start/stop navigation.")
    
    while button.value() == 0:
        pass

    while True:
        if not robot.stopped:
            
            rack_nodes = [
                "LowerRackA6", "LowerRackA5", "LowerRackA4", "LowerRackA3", "LowerRackA2", "LowerRackA1",
                "LowerRackB1", "LowerRackB2", "LowerRackB3", "LowerRackB4", "LowerRackB5", "LowerRampB6",
                "UpperRackA1", "UpperRackA2", "UpperRackA3", "UpperRackA4", "UpperRackA5", "UpperRackA6",
                "UpperRackB6", "UpperRackB5", "UpperRackB4", "UpperRackB3", "UpperRackB2", "UpperRackB1"
                ]
            
            for node in rack_nodes:
            
                robot.navigate_path(node)
                
                if "LowerRackA" in node or "UpperRackB" in node:
                    robot.turn_abs(1)
                else:
                    robot.turn_abs(3)
                
                if "Lower" in node:
                    actuator.set_height(30)
                else:
                    actuator.set_height(0)
                
                robot.line_follow_for_time(1575, 60)
                
                if distance_sensor.read() < 100:
                    box = True
                    
                    colour_sensor_power.value(1)
                    i2c_0 = I2C(0, scl=Pin(17), sda=Pin(16), freq=400000)
                    time.sleep(1)
                    colour_sensor = TCS34725(i2c_0)
                    time.sleep(1) # Delay to allow the colour sensor to initialise
                    box_colour = colour_sensor.get_color()
                    colour_sensor_power.value(0)
                    
                    actuator.set_height(35)
                else:
                    box = False
                
                robot.reverse_from_bay()
                
                if box:
                    actuator.set_height(15)
                    robot.turn_abs(2, 50, 0.835)
                    robot.line_follow_for_time(200)
                    robot.navigate_path(box_colour)
                    robot.turn_abs(2)
                    robot.line_follow_for_time(2000)
                    actuator.set_height(0)
                    robot.reverse_for_time(1500)
                    robot.uturn()
                    robot.continue_to_junction()
                    robot.navigate_path(node)
                elif node == "UpperRackA6" or node == "UpperRackB1":
                    robot.turn_abs(2,50, 0.835)
                    robot.line_follow_for_time(200)
                else:
                    robot.turn_abs(0, 50, 0.835)
                    robot.line_follow_for_time(200)
            
            robot.navigate_path("BoxInside")
            robot.stopped = True  # Prevent immediate restart after completion
