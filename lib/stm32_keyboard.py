"""
STM32 Keyboard Controller Driver for PicoCalc
QWERTY keyboard with backlight controlled via I2C interface
Supports key scanning, modifiers, and special functions
"""

import time
from micropython import const

# STM32 I2C Register definitions
_REG_KEY_STATUS = const(0x00)    # Key status register
_REG_KEY_DATA = const(0x01)      # Key data register (scan code)
_REG_KEY_MODIFIER = const(0x02)  # Modifier keys status
_REG_KEY_BUFFER = const(0x03)    # Key buffer (up to 6 keys)
_REG_BACKLIGHT = const(0x10)     # Keyboard backlight control
_REG_CONFIG = const(0x20)        # Configuration register
_REG_VERSION = const(0x30)       # Firmware version
_REG_RESET = const(0xFF)         # Reset keyboard controller

# Key status flags
_STATUS_KEY_PRESSED = const(0x01)
_STATUS_KEY_RELEASED = const(0x02)
_STATUS_BUFFER_FULL = const(0x04)
_STATUS_ERROR = const(0x80)

# Modifier key bits
_MOD_SHIFT_L = const(0x01)
_MOD_SHIFT_R = const(0x02)
_MOD_CTRL_L = const(0x04)
_MOD_CTRL_R = const(0x08)
_MOD_ALT_L = const(0x10)
_MOD_ALT_R = const(0x20)
_MOD_FN = const(0x40)
_MOD_CAPS_LOCK = const(0x80)

# Scan code to ASCII mapping
SCANCODE_MAP = {
    # Letters (lowercase)
    0x04: 'a', 0x05: 'b', 0x06: 'c', 0x07: 'd', 0x08: 'e',
    0x09: 'f', 0x0A: 'g', 0x0B: 'h', 0x0C: 'i', 0x0D: 'j',
    0x0E: 'k', 0x0F: 'l', 0x10: 'm', 0x11: 'n', 0x12: 'o',
    0x13: 'p', 0x14: 'q', 0x15: 'r', 0x16: 's', 0x17: 't',
    0x18: 'u', 0x19: 'v', 0x1A: 'w', 0x1B: 'x', 0x1C: 'y',
    0x1D: 'z',

    # Numbers
    0x1E: '1', 0x1F: '2', 0x20: '3', 0x21: '4', 0x22: '5',
    0x23: '6', 0x24: '7', 0x25: '8', 0x26: '9', 0x27: '0',

    # Special characters
    0x28: '\n',    # Enter
    0x29: '\x1b',  # Escape
    0x2A: '\x08',  # Backspace
    0x2B: '\t',    # Tab
    0x2C: ' ',     # Space
    0x2D: '-', 0x2E: '=', 0x2F: '[', 0x30: ']', 0x31: '\\',
    0x33: ';', 0x34: "'", 0x35: '`', 0x36: ',', 0x37: '.',
    0x38: '/',

    # Function keys
    0x3A: 'F1', 0x3B: 'F2', 0x3C: 'F3', 0x3D: 'F4',
    0x3E: 'F5', 0x3F: 'F6', 0x40: 'F7', 0x41: 'F8',
    0x42: 'F9', 0x43: 'F10', 0x44: 'F11', 0x45: 'F12',

    # Navigation
    0x4F: 'RIGHT', 0x50: 'LEFT', 0x51: 'DOWN', 0x52: 'UP',
    0x4A: 'HOME', 0x4D: 'END', 0x4E: 'PGDN', 0x4B: 'PGUP',
    0x49: 'INS', 0x4C: 'DEL'
}

# Shifted characters
SHIFT_MAP = {
    '1': '!', '2': '@', '3': '#', '4': '$', '5': '%',
    '6': '^', '7': '&', '8': '*', '9': '(', '0': ')',
    '-': '_', '=': '+', '[': '{', ']': '}', '\\': '|',
    ';': ':', "'": '"', ',': '<', '.': '>', '/': '?',
    '`': '~'
}

class STM32Keyboard:
    """Driver for STM32-based keyboard controller"""

    def __init__(self, i2c, address=0x5F):
        """
        Initialize STM32 keyboard controller

        Args:
            i2c: I2C bus instance
            address: I2C address (default 0x5F)
        """
        self.i2c = i2c
        self.address = address

        # Key state
        self.key_buffer = []
        self.modifiers = 0
        self.caps_lock = False
        self.num_lock = False
        self.scroll_lock = False

        # Key repeat
        self.repeat_enabled = True
        self.repeat_delay = 500  # ms before repeat starts
        self.repeat_rate = 30    # ms between repeats
        self.last_key = None
        self.last_key_time = 0
        self.key_repeating = False

        # Backlight
        self.backlight_level = 100

        # Initialize keyboard
        self.init_keyboard()

    def init_keyboard(self):
        """Initialize the keyboard controller"""
        try:
            # Check if keyboard controller is present
            version = self.read_reg(_REG_VERSION)
            print(f"STM32 Keyboard firmware version: 0x{version:02X}")

            # Configure keyboard
            self.write_reg(_REG_CONFIG, 0x01)  # Enable keyboard scanning

            # Set initial backlight
            self.set_backlight(self.backlight_level)

        except:
            print("STM32 keyboard controller not found")

    def write_reg(self, reg, value):
        """Write to keyboard controller register"""
        self.i2c.writeto_mem(self.address, reg, bytes([value]))

    def read_reg(self, reg, count=1):
        """Read from keyboard controller register"""
        data = self.i2c.readfrom_mem(self.address, reg, count)
        if count == 1:
            return data[0]
        return data

    def scan(self):
        """Scan for key presses"""
        # Read key status
        status = self.read_reg(_REG_KEY_STATUS)

        if status & _STATUS_KEY_PRESSED:
            # Read key data
            scancode = self.read_reg(_REG_KEY_DATA)
            modifiers = self.read_reg(_REG_KEY_MODIFIER)

            # Update modifiers
            self.modifiers = modifiers

            # Update lock keys
            if modifiers & _MOD_CAPS_LOCK:
                self.caps_lock = not self.caps_lock

            # Convert scancode to character
            key = self.scancode_to_key(scancode, modifiers)

            if key:
                # Add to buffer
                self.key_buffer.append(key)

                # Handle key repeat
                self.last_key = key
                self.last_key_time = time.ticks_ms()
                self.key_repeating = False

                return key

        elif self.repeat_enabled and self.last_key:
            # Handle key repeat
            current_time = time.ticks_ms()

            if not self.key_repeating:
                # Check if we should start repeating
                if time.ticks_diff(current_time, self.last_key_time) > self.repeat_delay:
                    self.key_repeating = True
                    self.last_key_time = current_time
                    return self.last_key
            else:
                # Continue repeating
                if time.ticks_diff(current_time, self.last_key_time) > self.repeat_rate:
                    self.last_key_time = current_time
                    return self.last_key

        elif status & _STATUS_KEY_RELEASED:
            # Key released, stop repeating
            self.last_key = None
            self.key_repeating = False

        return None

    def scancode_to_key(self, scancode, modifiers):
        """Convert scancode and modifiers to key/character"""
        # Get base key
        key = SCANCODE_MAP.get(scancode, None)

        if key is None:
            return None

        # Handle letters with shift/caps lock
        if len(key) == 1 and key.isalpha():
            if (modifiers & (_MOD_SHIFT_L | _MOD_SHIFT_R)) or self.caps_lock:
                key = key.upper()
            else:
                key = key.lower()

        # Handle shifted characters
        elif (modifiers & (_MOD_SHIFT_L | _MOD_SHIFT_R)) and key in SHIFT_MAP:
            key = SHIFT_MAP[key]

        # Handle function key combinations
        if modifiers & _MOD_FN:
            # Function key mappings
            fn_map = {
                '1': 'F1', '2': 'F2', '3': 'F3', '4': 'F4',
                '5': 'F5', '6': 'F6', '7': 'F7', '8': 'F8',
                '9': 'F9', '0': 'F10', '-': 'F11', '=': 'F12'
            }
            if key in fn_map:
                key = fn_map[key]

        # Handle control key combinations
        if modifiers & (_MOD_CTRL_L | _MOD_CTRL_R):
            # Convert to control character
            if len(key) == 1 and key.isalpha():
                key = chr(ord(key.upper()) - ord('A') + 1)

        return key

    def get_key(self):
        """Get next key from buffer"""
        key = self.scan()
        if key:
            return key

        # Check buffer
        if self.key_buffer:
            return self.key_buffer.pop(0)

        return None

    def has_key(self):
        """Check if key is available"""
        if self.key_buffer:
            return True

        key = self.scan()
        if key:
            self.key_buffer.append(key)
            return True

        return False

    def clear_buffer(self):
        """Clear key buffer"""
        self.key_buffer = []
        self.last_key = None
        self.key_repeating = False

    def set_backlight(self, level):
        """Set keyboard backlight level (0-100)"""
        self.backlight_level = max(0, min(100, level))
        value = int(self.backlight_level * 255 / 100)
        self.write_reg(_REG_BACKLIGHT, value)

    def reset(self):
        """Reset keyboard controller"""
        self.write_reg(_REG_RESET, 0xFF)
        time.sleep_ms(100)
        self.init_keyboard()

    def get_modifiers(self):
        """Get current modifier key state"""
        return {
            'shift': bool(self.modifiers & (_MOD_SHIFT_L | _MOD_SHIFT_R)),
            'ctrl': bool(self.modifiers & (_MOD_CTRL_L | _MOD_CTRL_R)),
            'alt': bool(self.modifiers & (_MOD_ALT_L | _MOD_ALT_R)),
            'fn': bool(self.modifiers & _MOD_FN),
            'caps_lock': self.caps_lock,
            'num_lock': self.num_lock,
            'scroll_lock': self.scroll_lock
        }

class KeyboardButtons:
    """Virtual button handler using keyboard keys"""

    def __init__(self, keyboard):
        """
        Initialize keyboard-based buttons

        Args:
            keyboard: STM32Keyboard instance
        """
        self.keyboard = keyboard

        # Key to button mapping
        self.key_map = {
            ' ': 'A',      # Space -> A
            '\x1b': 'B',   # Escape -> B
            'x': 'X',      # X key -> X
            'X': 'X',      # X (shift) -> X
            'y': 'Y',      # Y key -> Y
            'Y': 'Y',      # Y (shift) -> Y
            '\n': 'START', # Enter -> Start
            '\t': 'SELECT' # Tab -> Select
        }

        # Button states
        self.button_states = {
            'A': False,
            'B': False,
            'X': False,
            'Y': False,
            'START': False,
            'SELECT': False
        }

        # Previous states for edge detection
        self.prev_states = self.button_states.copy()

    def update(self):
        """Update button states from keyboard"""
        # Clear current states
        for button in self.button_states:
            self.prev_states[button] = self.button_states[button]
            self.button_states[button] = False

        # Check for key presses
        while self.keyboard.has_key():
            key = self.keyboard.get_key()
            if key in self.key_map:
                button = self.key_map[key]
                self.button_states[button] = True

    def is_pressed(self, button):
        """Check if button was just pressed (rising edge)"""
        return self.button_states.get(button, False) and not self.prev_states.get(button, False)

    def is_held(self, button):
        """Check if button is currently held"""
        return self.button_states.get(button, False)

    def is_released(self, button):
        """Check if button was just released (falling edge)"""
        return not self.button_states.get(button, False) and self.prev_states.get(button, False)

class KeyboardJoystick:
    """Virtual joystick using keyboard arrow keys"""

    def __init__(self, keyboard):
        """
        Initialize keyboard-based joystick

        Args:
            keyboard: STM32Keyboard instance
        """
        self.keyboard = keyboard

        # Direction states
        self.directions = {
            'up': False,
            'down': False,
            'left': False,
            'right': False,
            'center': False
        }

        # Create virtual pins for compatibility
        self.up_pin = VirtualPin(self, 'up')
        self.down_pin = VirtualPin(self, 'down')
        self.left_pin = VirtualPin(self, 'left')
        self.right_pin = VirtualPin(self, 'right')
        self.center_pin = VirtualPin(self, 'center')

    def update(self):
        """Update joystick state from keyboard"""
        # Clear states
        for direction in self.directions:
            self.directions[direction] = False

        # Check for arrow keys
        while self.keyboard.has_key():
            key = self.keyboard.get_key()

            if key == 'UP':
                self.directions['up'] = True
            elif key == 'DOWN':
                self.directions['down'] = True
            elif key == 'LEFT':
                self.directions['left'] = True
            elif key == 'RIGHT':
                self.directions['right'] = True
            elif key == '\n':  # Enter as center/select
                self.directions['center'] = True

    def is_pressed(self, direction):
        """Check if direction is pressed"""
        self.update()
        return self.directions.get(direction, False)

class VirtualPin:
    """Virtual pin for compatibility"""

    def __init__(self, joystick, direction):
        self.joystick = joystick
        self.direction = direction

    def value(self):
        """Get pin value (0 = pressed, 1 = not pressed)"""
        return 0 if self.joystick.directions[self.direction] else 1