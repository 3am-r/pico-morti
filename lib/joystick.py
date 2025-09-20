"""
Joystick driver - Device agnostic
Supports both digital 5-way and analog 2-axis joysticks
"""

from machine import Pin, ADC
import time
import sys

# Import hardware configuration
sys.path.append('devices')
from devices.hardware_runtime import get_hardware_config

class VirtualPin:
    """Virtual pin that mimics Pin interface for analog joystick"""
    def __init__(self, value_func):
        self.value_func = value_func
        
    def value(self):
        """Return the current state (0 = pressed, 1 = not pressed for pull-up logic)"""
        return self.value_func()

class Joystick:
    def __init__(self, x_pin=None, y_pin=None, sw_pin=None):
        """
        Initialize joystick using hardware configuration
        Supports both digital and analog joysticks
        """
        # Get hardware configuration
        hw_config = get_hardware_config()
        joystick_config = hw_config["JOYSTICK"]
        
        self.joystick_type = joystick_config.get("TYPE", "digital")
        
        if self.joystick_type == "analog":
            # Analog joystick configuration
            self.x_adc = ADC(Pin(joystick_config["X_PIN"]))
            self.y_adc = ADC(Pin(joystick_config["Y_PIN"]))
            
            # Center button
            pull_mode = Pin.PULL_UP if joystick_config["PULL_UP"] else None
            self.center_pin = Pin(joystick_config["CENTER"], Pin.IN, pull_mode)
            
            # Thresholds for analog to digital conversion
            self.threshold_low = joystick_config.get("THRESHOLD_LOW", 20000)
            self.threshold_high = joystick_config.get("THRESHOLD_HIGH", 45000)
            self.center_range = joystick_config.get("CENTER_RANGE", 5000)
            self.center_value = 32768  # Middle of 16-bit ADC range
            
            # Create virtual pins that mimic digital behavior
            self.up_pin = VirtualPin(lambda: self._check_analog_up())
            self.down_pin = VirtualPin(lambda: self._check_analog_down())
            self.left_pin = VirtualPin(lambda: self._check_analog_left())
            self.right_pin = VirtualPin(lambda: self._check_analog_right())
            
        else:
            # Digital joystick configuration
            pull_mode = Pin.PULL_UP if joystick_config["PULL_UP"] else None
            
            self.up_pin = Pin(joystick_config["UP"], Pin.IN, pull_mode)
            self.down_pin = Pin(joystick_config["DOWN"], Pin.IN, pull_mode)
            self.left_pin = Pin(joystick_config["LEFT"], Pin.IN, pull_mode)
            self.right_pin = Pin(joystick_config["RIGHT"], Pin.IN, pull_mode)
            self.center_pin = Pin(joystick_config["CENTER"], Pin.IN, pull_mode)
        
        # Debounce settings
        self.debounce_time = 150  # Default debounce time in ms
        self.last_press_time = 0
        self.last_direction_time = 0
        self.last_direction = None
        
        # Direction states
        self.directions = {
            'UP': False,
            'DOWN': False,
            'LEFT': False,
            'RIGHT': False,
            'CENTER': False
        }
    
    def _check_analog_up(self):
        """Check if analog joystick is pushed up (returns 0 if up, 1 if not)"""
        if self.joystick_type == "analog":
            y_value = self.y_adc.read_u16()
            return 0 if y_value < self.threshold_low else 1
        return 1
    
    def _check_analog_down(self):
        """Check if analog joystick is pushed down"""
        if self.joystick_type == "analog":
            y_value = self.y_adc.read_u16()
            return 0 if y_value > self.threshold_high else 1
        return 1
    
    def _check_analog_left(self):
        """Check if analog joystick is pushed left"""
        if self.joystick_type == "analog":
            x_value = self.x_adc.read_u16()
            return 0 if x_value < self.threshold_low else 1
        return 1
    
    def _check_analog_right(self):
        """Check if analog joystick is pushed right"""
        if self.joystick_type == "analog":
            x_value = self.x_adc.read_u16()
            return 0 if x_value > self.threshold_high else 1
        return 1
        
    def get_direction(self, debounce_override=None):
        """
        Get current joystick direction
        
        Args:
            debounce_override: Custom debounce time in ms (None uses default)
            
        Returns: String ('UP', 'DOWN', 'LEFT', 'RIGHT', 'CENTER', or None)
        """
        current_time = time.ticks_ms()
        debounce = debounce_override if debounce_override is not None else self.debounce_time
        
        # Get current pressed direction
        current_direction = None
        if not self.up_pin.value():
            current_direction = 'UP'
        elif not self.down_pin.value():
            current_direction = 'DOWN'
        elif not self.left_pin.value():
            current_direction = 'LEFT'
        elif not self.right_pin.value():
            current_direction = 'RIGHT'
        elif not self.center_pin.value():
            current_direction = 'CENTER'
        
        # If no direction is pressed, reset
        if current_direction is None:
            self.last_direction = None
            return None
            
        # If same direction as before, check debounce
        if current_direction == self.last_direction:
            if time.ticks_diff(current_time, self.last_direction_time) < debounce:
                return None
        
        # New direction or debounce time passed
        self.last_direction = current_direction
        self.last_direction_time = current_time
        return current_direction
        
    def get_direction_fast(self):
        """Get direction with shorter debounce for responsive navigation"""
        return self.get_direction(debounce_override=50)
        
    def get_direction_slow(self):
        """Get direction with longer debounce for menu navigation"""
        return self.get_direction(debounce_override=250)
        
    def get_direction_medium(self):
        """Get direction with medium debounce for home menu with many apps"""
        return self.get_direction(debounce_override=150)
        
    def update(self):
        """
        Update direction states
        Returns: Dictionary of current direction states
        """
        direction = self.get_direction()
        
        # Reset all directions
        for key in self.directions:
            self.directions[key] = False
            
        # Set current direction
        if direction:
            self.directions[direction] = True
            
        return self.directions
        
    def is_pressed(self, direction):
        """Check if specific direction is currently active"""
        if direction == 'UP':
            return not self.up_pin.value()
        elif direction == 'DOWN':
            return not self.down_pin.value()
        elif direction == 'LEFT':
            return not self.left_pin.value()
        elif direction == 'RIGHT':
            return not self.right_pin.value()
        elif direction == 'CENTER':
            return not self.center_pin.value()
        return False
        
    def wait_for_input(self, timeout=None):
        """
        Wait for joystick input
        
        Args:
            timeout: Timeout in milliseconds (None for no timeout)
            
        Returns: Direction string or None if timeout
        """
        start_time = time.ticks_ms()
        
        while True:
            direction = self.get_direction()
            if direction:
                return direction
                
            if timeout and time.ticks_diff(time.ticks_ms(), start_time) > timeout:
                return None
                
            time.sleep_ms(10)
            
    def read_raw(self):
        """Read raw digital pin values"""
        up = not self.up_pin.value()
        down = not self.down_pin.value()
        left = not self.left_pin.value()
        right = not self.right_pin.value()
        center = not self.center_pin.value()
        return up, down, left, right, center
        
    def read_position(self):
        """
        Read joystick position (compatibility method)
        Returns: (x, y, button_pressed) where x,y are -1, 0, or 1
        """
        up, down, left, right, center = self.read_raw()
        
        x = 0
        y = 0
        
        if left:
            x = -1
        elif right:
            x = 1
            
        if up:
            y = -1
        elif down:
            y = 1
            
        return x, y, center