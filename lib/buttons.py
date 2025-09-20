"""
Button driver - Device agnostic
4 user buttons (A, B, X, Y)
"""

from machine import Pin
import time
import sys

# Import hardware configuration
sys.path.append('devices')
from devices.hardware_runtime import get_hardware_config

class Button:
    def __init__(self, pin, name, pull_up=True):
        """
        Initialize a single button
        
        Args:
            pin: GPIO pin number
            name: Button name/identifier
            pull_up: Use internal pull-up resistor
        """
        self.pin = Pin(pin, Pin.IN, Pin.PULL_UP if pull_up else None)
        self.name = name
        self.pull_up = pull_up
        
        # Button state tracking
        self.pressed = False
        self.last_state = self.pin.value()
        self.last_change_time = time.ticks_ms()
        
        # Debounce settings
        self.debounce_time = 50  # ms
        
        # Long press detection
        self.press_start_time = 0
        self.long_press_time = 1000  # ms for long press
        self.is_long_press = False
        
        # Simple debounce for is_pressed()
        self.last_press_time = 0
        self.press_debounce_time = 200  # ms between press detections
        
        # Callback functions
        self.on_press = None
        self.on_release = None
        self.on_long_press = None
        
    def read(self):
        """Read current button state (True if pressed)"""
        # Inverted logic if pull-up is used
        return not self.pin.value() if self.pull_up else self.pin.value()
        
    def update(self):
        """
        Update button state with debouncing
        Returns: 'pressed', 'released', 'long_press', or None
        """
        current_state = self.read()
        current_time = time.ticks_ms()
        
        # Check for state change with debouncing
        if current_state != self.last_state:
            if time.ticks_diff(current_time, self.last_change_time) > self.debounce_time:
                self.last_state = current_state
                self.last_change_time = current_time
                
                if current_state:  # Button pressed
                    self.pressed = True
                    self.press_start_time = current_time
                    self.is_long_press = False
                    if self.on_press:
                        self.on_press(self)
                    return 'pressed'
                else:  # Button released
                    self.pressed = False
                    if self.on_release:
                        self.on_release(self)
                    if not self.is_long_press:
                        return 'released'
                    self.is_long_press = False
                    
        # Check for long press
        if self.pressed and not self.is_long_press:
            if time.ticks_diff(current_time, self.press_start_time) > self.long_press_time:
                self.is_long_press = True
                if self.on_long_press:
                    self.on_long_press(self)
                return 'long_press'
                
        return None
        
    def is_pressed(self):
        """Check if button is currently pressed (with debouncing)"""
        current_time = time.ticks_ms()
        
        # Check if button is physically pressed and enough time has passed
        if self.read() and time.ticks_diff(current_time, self.last_press_time) > self.press_debounce_time:
            self.last_press_time = current_time
            return True
        return False
        
    def is_held(self):
        """Check if button is currently held down (raw state, no debouncing)"""
        return self.read()
        
    def wait_for_press(self, timeout=None):
        """
        Wait for button press
        
        Args:
            timeout: Timeout in milliseconds
            
        Returns: True if pressed, False if timeout
        """
        start_time = time.ticks_ms()
        
        while True:
            if self.read():
                # Wait for release (debounce)
                time.sleep_ms(self.debounce_time)
                return True
                
            if timeout and time.ticks_diff(time.ticks_ms(), start_time) > timeout:
                return False
                
            time.sleep_ms(10)
            
    def set_callback(self, event, callback):
        """
        Set callback function for button events
        
        Args:
            event: 'press', 'release', or 'long_press'
            callback: Function to call (receives Button instance)
        """
        if event == 'press':
            self.on_press = callback
        elif event == 'release':
            self.on_release = callback
        elif event == 'long_press':
            self.on_long_press = callback


class DummyButton:
    """Dummy button for devices that don't have all 4 buttons"""
    def __init__(self, name):
        self.name = name
        self.pressed = False
        self.last_state = True  # Not pressed
        self.last_change_time = 0
        self.debounce_time = 50
        self.press_start_time = 0
        self.long_press_time = 1000
        self.is_long_press = False
        self.last_press_time = 0
        self.press_debounce_time = 200
        
    def read(self):
        """Always return False (not pressed)"""
        return False
        
    def update(self):
        """No-op for dummy button"""
        return None
        
    def is_pressed(self):
        """Always return False (not pressed)"""
        return False
        
    def is_held(self):
        """Always return False (not held)"""
        return False
        
    def wait_for_press(self, timeout=None):
        """Never pressed, so return False after timeout"""
        if timeout:
            time.sleep_ms(timeout)
        return False
        
    def set_callback(self, event, callback):
        """No-op for dummy button"""
        pass


class Buttons:
    def __init__(self):
        """
        Initialize buttons using hardware configuration
        """
        # Get hardware configuration
        hw_config = get_hardware_config()
        buttons_config = hw_config["BUTTONS"]
        
        # Initialize only available buttons (skip -1 pins)
        self.buttons = {}
        
        for button_name in ['A', 'B', 'X', 'Y']:
            pin_num = buttons_config.get(button_name, -1)
            if pin_num >= 0:  # Only create button if pin is valid
                self.buttons[button_name] = Button(pin_num, button_name, buttons_config['PULL_UP'])
            else:
                # Create a dummy button that's never pressed for compatibility
                self.buttons[button_name] = DummyButton(button_name)
        
        # Track button combinations
        self.combo_callbacks = {}
        
    def update(self):
        """
        Update all button states
        Returns: Dictionary of button events
        """
        events = {}
        for name, button in self.buttons.items():
            event = button.update()
            if event:
                events[name] = event
                
        # Check for button combinations
        self._check_combos()
        
        return events
        
    def get_pressed(self):
        """
        Get list of currently pressed buttons
        Returns: List of button names
        """
        pressed = []
        for name, button in self.buttons.items():
            if button.is_held():
                pressed.append(name)
        return pressed
        
    def is_pressed(self, button_name):
        """Check if specific button is pressed (with debouncing)"""
        if button_name in self.buttons:
            return self.buttons[button_name].is_pressed()
        return False
        
    def is_held(self, button_name):
        """Check if specific button is currently held down (raw state)"""
        if button_name in self.buttons:
            return self.buttons[button_name].is_held()
        return False
        
    def wait_for_any(self, timeout=None):
        """
        Wait for any button press
        
        Args:
            timeout: Timeout in milliseconds
            
        Returns: Button name or None if timeout
        """
        start_time = time.ticks_ms()
        
        while True:
            for name, button in self.buttons.items():
                if button.is_held():
                    # Wait for release
                    while button.is_held():
                        time.sleep_ms(10)
                    return name
                    
            if timeout and time.ticks_diff(time.ticks_ms(), start_time) > timeout:
                return None
                
            time.sleep_ms(10)
            
    def set_callback(self, button_name, event, callback):
        """
        Set callback for specific button event
        
        Args:
            button_name: 'A', 'B', 'X', or 'Y'
            event: 'press', 'release', or 'long_press'
            callback: Function to call
        """
        if button_name in self.buttons:
            self.buttons[button_name].set_callback(event, callback)
            
    def set_combo_callback(self, buttons, callback):
        """
        Set callback for button combination
        
        Args:
            buttons: Tuple of button names (e.g., ('A', 'B'))
            callback: Function to call when combo is pressed
        """
        combo_key = tuple(sorted(buttons))
        self.combo_callbacks[combo_key] = callback
        
    def _check_combos(self):
        """Check for button combinations"""
        pressed = self.get_pressed()
        if len(pressed) > 1:
            combo_key = tuple(sorted(pressed))
            if combo_key in self.combo_callbacks:
                self.combo_callbacks[combo_key]()
                
    def get_button(self, name):
        """Get specific button object"""
        return self.buttons.get(name)
        
    def reset_all(self):
        """Reset all button states"""
        for button in self.buttons.values():
            button.pressed = False
            button.is_long_press = False
            button.last_state = button.pin.value()