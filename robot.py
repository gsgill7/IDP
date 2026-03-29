from machine import Pin
from utime import sleep, ticks_ms
from actuators import Motor
from sensors import LineSensor
from navigation import maze_map, relative_turn, find_shortest_path


class Robot:
    """Main robot class encapsulating all navigation and control logic."""

    # Robot state constants
    STATE_LINE_FOLLOWING = "line_following"
    STATE_COMPLETED = "completed"

    def __init__(self):
        """Initialize robot with motor and sensor pins."""

        # Motors
        self.left_motor = Motor(4, 5)
        self.right_motor = Motor(7, 6)

        # Sensor pins
        self.line_left_pin = 9
        self.line_right_pin = 10
        self.junction_left_pin = 8
        self.junction_right_pin = 11
        self.button_pin = 12
        self.yellow_light_pin = 28

        # Navigation state
        self.stopped = False
        self.junction_detected = False
        self.robot_state = self.STATE_LINE_FOLLOWING
        self.direction = 0  # Current orientation
        self.node = "BoxInside"
        self.active = False

        # Setup flashing yellow light
        self.yellow_light = Pin(self.yellow_light_pin, Pin.OUT)
        self.yellow_light.value(1)

        # Setup junction detection interrupts
        self.junction_pin1 = Pin(self.junction_left_pin, Pin.IN, Pin.PULL_UP)
        self.junction_pin2 = Pin(self.junction_right_pin, Pin.IN, Pin.PULL_UP)
        self.junction_pin1.irq(trigger=Pin.IRQ_RISING, handler=self._junction_interrupt)
        self.junction_pin2.irq(trigger=Pin.IRQ_RISING, handler=self._junction_interrupt)

    def _junction_interrupt(self, pin):
        """Interrupt handler for junction detection."""
        # print(f"INTERRUPT: Junction detected on pin {pin}! Value: {pin.value()}")
        # self.left_motor.off()
        # self.right_motor.off()
        self.junction_detected = True

    def _button_interrupt(self, pin):
        """Interrupt handler for button press (stop/start toggle)."""
        print(f"INTERRUPT: Button pressed on pin {pin}! Value: {pin.value()}")
        self.stopped = not self.stopped
        print(f"Robot {'STOPPED' if self.stopped else 'STARTED'}")

    def update_node(self, new_node):
        """Update the current node of the robot."""
        self.node = new_node

        if new_node == "BoxInside":
            self.active = False
            self.yellow_light(1)
        else:
            self.active = True
            self.yellow_light(0)

    def line_follow(self, base_speed=80, correction_factor=15):
        """Follow a line using differential steering."""
        left_sensor = LineSensor.read(self.line_left_pin)
        right_sensor = LineSensor.read(self.line_right_pin)
        diff = (left_sensor - right_sensor) * correction_factor

        self.left_motor.speed(base_speed - diff)
        self.right_motor.speed(base_speed + diff)

    def line_follow_for_time(self, time, base_speed=80, correction_factor=15):
        """Follow a line using differential steering."""
        start_time = ticks_ms()
        while ticks_ms() - start_time < time:
            self.line_follow(base_speed, correction_factor)
        self.right_motor.off()
        self.left_motor.off()
            
    def reverse_for_time(self, time, speed=40):
        start_time = ticks_ms()
        while ticks_ms() - start_time < time:
            self.left_motor.speed(-speed)
            self.right_motor.speed(-speed)
        self.right_motor.off()
        self.left_motor.off()

    def reverse_from_bay(self, speed=60):

        self.left_motor.speed(-speed)
        self.right_motor.speed(-speed)

        while LineSensor.read(self.junction_left_pin) == 0 and LineSensor.read(self.junction_right_pin) == 0:
            pass

        self.left_motor.off()
        self.right_motor.off()
        
    def continue_to_junction(self, speed=60):

        while LineSensor.read(self.junction_left_pin) == 0 and LineSensor.read(self.junction_right_pin) == 0:
            self.line_follow()

        self.left_motor.off()
        self.right_motor.off()


    def turn(self, rel_dir, speed=75, correction_factor=0.67):
        """
        Execute a turn based on relative direction.
        Updates the robot's direction state after turning.

        Args:
            rel_dir: Relative turn direction (+1=right, -1=left, 2=U-turn, 0=straight)
            speed: Motor speed during turn (default 75)
            correction_factor: Speed correction factor for outer wheel (default 0.85)
        """
        start_time = ticks_ms()
        min_turn_time = 750  # minimum turn time 

        if rel_dir == 1:  # Turn right
            self.left_motor.speed(speed*correction_factor)
            self.right_motor.speed(-speed)
            while ticks_ms() - start_time < min_turn_time:
                pass
            while LineSensor.read(self.line_left_pin) == 0:
                pass
        elif rel_dir == -1:  # Turn left
            self.left_motor.speed(-speed)
            self.right_motor.speed(speed*correction_factor)
            while ticks_ms() - start_time < min_turn_time:
                pass
            while LineSensor.read(self.line_right_pin) == 0:
                pass
        elif rel_dir == 2:  # U-turn (SHOULD NOT BE USED)
            dirs = set(maze_map[self.node].values())
            turn_dirs = {self.direction, self.direction+rel_dir}
            dir = dirs.difference(turn_dirs)
            
            self.turn_abs(dir.pop())
            self.turn_abs(self.direction+rel_dir)
            

        self.left_motor.off()
        self.right_motor.off()

        # Update direction state based on relative turn
        self.direction = (self.direction + rel_dir) % 4
        
    def turn_abs(self, abs_dir, speed=75, correction_factor=1):
        rel_dir = relative_turn(self.direction, abs_dir)
        self.turn(rel_dir, speed, correction_factor)
        
    def uturn(self, speed=75):
        
        start_time = ticks_ms()
        min_turn_time = 750
        
        self.left_motor.speed(speed)
        self.right_motor.speed(-speed)
        
        while ticks_ms() - start_time < min_turn_time:
            pass
        while LineSensor.read(self.line_left_pin) == 0:
            pass
        
        self.direction = (self.direction + 2) % 4
        self.left_motor.off()
        self.right_motor.off()

    def navigate_path(self, destination_node):
        """
        Navigate from the robot's current node to the destination node.
        Automatically finds the shortest path and updates the robot's current node.

        Args:
            destination_node: The target node name (string)
        """
        # Find the shortest path from current position to destination
        path = find_shortest_path(self.node, destination_node)

        if path is None:
            print(f"Error: Cannot find path from {self.node} to {destination_node}")
            return

        # Reset navigation state
        current_path_index = 0
        self.junction_detected = False
        self.robot_state = self.STATE_LINE_FOLLOWING

        print(f"Starting navigation: {path[0]} -> {path[-1]}")
        
        self.turn_abs(maze_map[path[0]][path[1]])
        self.junction_detected = False

        try:
            while current_path_index < len(path) - 1:

                print(f"State: {self.robot_state}, Path index: {current_path_index}/{len(path)-1}")

                # Check if stopped
                if self.stopped:
                    self.right_motor.off()
                    self.left_motor.off()
                    return

                if self.robot_state == self.STATE_LINE_FOLLOWING:
                    self._follow_line_to_junction(path, current_path_index)

                    if self.stopped:
                        self.right_motor.off()
                        self.left_motor.off()
                        return

                    if self.junction_detected:
                        # sleep(0.1)
                        current_path_index = self._handle_junction(path, current_path_index)

            print("Path navigation completed!")
            self.robot_state = self.STATE_COMPLETED

            # Update robot's current node to the destination
            self.update_node(destination_node)
            print(f"Robot now at node: {self.node}")

        except KeyboardInterrupt:
            print("Navigation interrupted by user")
            self.right_motor.off()
            self.left_motor.off()

        self.right_motor.off()
        self.left_motor.off()

    def _follow_line_to_junction(self, path, current_path_index):
        """Continue line following until a junction is detected."""
        print(f"Line following mode: {path[current_path_index]} -> {path[current_path_index + 1]}")
        print(f"Sensors - Left junction: {LineSensor.read(self.junction_left_pin)}, "
              f"Right junction: {LineSensor.read(self.junction_right_pin)}")

        while not self.junction_detected and not self.stopped:
            self.line_follow()

    def _handle_junction(self, path, current_path_index):
        """Handle junction detection and execute appropriate turn."""
        # Move to next node
        
        self.left_motor.off()
        self.right_motor.off()
        
        current_path_index += 1
        current_node = path[current_path_index]

        # Update robot's current node
        self.update_node(current_node)

        print(f"Junction detected! Now at node: {current_node}")

        # Check if there's a next node to navigate to
        if current_path_index < len(path) - 1:
            next_node = path[current_path_index + 1]
            new_dir = maze_map[current_node][next_node]
            rel = relative_turn(self.direction, new_dir)

            print(f"Navigation: {current_node} -> {next_node}")
            print(f"Direction change: {self.direction} -> {new_dir} (rel_turn={rel})")

            # Execute turn if needed (this will also update self.direction)
            if rel != 0:
                print(f"Executing turn: {rel}")
                self.turn(rel)
                if self.stopped:
                    return current_path_index
            else:
                print("No turn needed - going straight")


            self.left_motor.speed(80)
            self.right_motor.speed(80)
            sleep(0.1)
            self.left_motor.off()
            self.right_motor.off()

            print(f"Completed turn at {current_node}, resuming line following")

        # Reset junction detection
        self.junction_detected = False
        self.robot_state = self.STATE_LINE_FOLLOWING

        return current_path_index

