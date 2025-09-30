"""
FT3168 Capacitive Touch Controller Driver
For ESP32-S3-Touch-AMOLED-2.06 with 410×502 display
Supports multi-touch, gestures, and virtual buttons
"""

from micropython import const
import time

# FT3168 Register definitions
_REG_DEV_MODE = const(0x00)      # Device mode register
_REG_GEST_ID = const(0x01)       # Gesture ID register
_REG_TD_STATUS = const(0x02)     # Touch points register
_REG_TOUCH_XH = const(0x03)      # Touch X high byte
_REG_TOUCH_XL = const(0x04)      # Touch X low byte
_REG_TOUCH_YH = const(0x05)      # Touch Y high byte
_REG_TOUCH_YL = const(0x06)      # Touch Y low byte
_REG_TOUCH_WEIGHT = const(0x07)  # Touch weight
_REG_TOUCH_AREA = const(0x08)    # Touch area
_REG_TOUCH2_XH = const(0x09)     # Touch point 2 X high
_REG_TOUCH2_XL = const(0x0A)     # Touch point 2 X low
_REG_TOUCH2_YH = const(0x0B)     # Touch point 2 Y high
_REG_TOUCH2_YL = const(0x0C)     # Touch point 2 Y low

# Control registers
_REG_THGROUP = const(0x80)       # Threshold group
_REG_THPEAK = const(0x81)        # Threshold peak
_REG_THCAL = const(0x82)         # Threshold calibration
_REG_THWATER = const(0x83)       # Threshold water
_REG_THTEMP = const(0x84)        # Threshold temperature
_REG_THDIFF = const(0x85)        # Threshold difference
_REG_CTRL = const(0x86)          # Control register
_REG_TIMEENTERMONITOR = const(0x87) # Time to enter monitor mode
_REG_PERIODACTIVE = const(0x88)  # Active period
_REG_PERIODMONITOR = const(0x89) # Monitor period
_REG_RADIAN_VALUE = const(0x91)  # Radian value
_REG_OFFSET_LEFT_RIGHT = const(0x92) # Offset left/right
_REG_OFFSET_UP_DOWN = const(0x93) # Offset up/down
_REG_DISTANCE_ZOOM = const(0x94) # Distance zoom
_REG_LIB_VERSION = const(0xA1)   # Library version
_REG_CIPHER = const(0xA3)        # Cipher
_REG_G_MODE = const(0xA4)        # G-sensor mode
_REG_PWR_MODE = const(0xA5)      # Power mode
_REG_FIRMID = const(0xA6)        # Firmware ID
_REG_FOCALTECH_ID = const(0xA8)  # FocalTech ID
_REG_RELEASE_CODE = const(0xAF)  # Release code

# Gesture IDs
_GEST_ID_NO_GESTURE = const(0x00)
_GEST_ID_MOVE_UP = const(0x10)
_GEST_ID_MOVE_RIGHT = const(0x14)
_GEST_ID_MOVE_DOWN = const(0x18)
_GEST_ID_MOVE_LEFT = const(0x1C)
_GEST_ID_ZOOM_IN = const(0x48)
_GEST_ID_ZOOM_OUT = const(0x49)

# Touch event flags
_EVENT_PRESS_DOWN = const(0x00)
_EVENT_LIFT_UP = const(0x01)
_EVENT_CONTACT = const(0x02)
_EVENT_NO_EVENT = const(0x03)

class TouchPoint:
    """Container for touch point data"""
    def __init__(self, x=0, y=0, event=_EVENT_NO_EVENT, id=0):
        self.x = x
        self.y = y
        self.event = event
        self.id = id
        self.weight = 0
        self.area = 0

class FT3168Touch:
    """Driver for FT3168 capacitive touch controller"""

    def __init__(self, i2c, address=0x38, width=410, height=502, int_pin=None, rst_pin=None):
        """
        Initialize FT3168 touch controller

        Args:
            i2c: I2C bus instance
            address: I2C address (default 0x38)
            width: Display width
            height: Display height
            int_pin: Interrupt pin (optional)
            rst_pin: Reset pin (optional)
        """
        self.i2c = i2c
        self.address = address
        self.width = width
        self.height = height
        self.int_pin = int_pin
        self.rst_pin = rst_pin

        # Touch state
        self.touches = []
        self.gesture = _GEST_ID_NO_GESTURE
        self.touch_count = 0

        # Virtual button zones (for emulating physical buttons)
        self.button_zones = {
            'A': {'x': 320, 'y': 420, 'w': 80, 'h': 60, 'pressed': False},
            'B': {'x': 10, 'y': 420, 'w': 80, 'h': 60, 'pressed': False},
            'X': {'x': 320, 'y': 10, 'w': 80, 'h': 60, 'pressed': False},
            'Y': {'x': 10, 'y': 10, 'w': 80, 'h': 60, 'pressed': False}
        }

        # Gesture detection
        self.gesture_enabled = True
        self.swipe_threshold = 50  # Minimum distance for swipe
        self.long_press_time = 500  # ms for long press
        self.double_tap_time = 300  # ms for double tap

        # Touch tracking for gestures
        self.last_touch_time = 0
        self.touch_start_pos = None
        self.touch_start_time = 0

        # Initialize hardware
        self.init_hardware()

    def init_hardware(self):
        """Initialize the touch controller hardware"""
        # Hardware reset if pin available
        if self.rst_pin:
            from machine import Pin
            rst = Pin(self.rst_pin, Pin.OUT)
            rst.value(0)
            time.sleep_ms(10)
            rst.value(1)
            time.sleep_ms(200)

        # Configure interrupt if pin available
        if self.int_pin:
            from machine import Pin
            self.int = Pin(self.int_pin, Pin.IN, Pin.PULL_UP)

        # Check if device is present
        try:
            chip_id = self.read_reg(_REG_FOCALTECH_ID)
            if chip_id != 0x11:  # Expected FT3168 ID
                print(f"Warning: Unexpected chip ID: 0x{chip_id:02X}")
        except:
            print("FT3168 touch controller not found")

        # Configure touch controller
        self.configure()

    def configure(self):
        """Configure touch controller settings"""
        # Set to normal operating mode
        self.write_reg(_REG_DEV_MODE, 0x00)

        # Configure thresholds for better sensitivity
        self.write_reg(_REG_THGROUP, 0x16)  # Touch threshold
        self.write_reg(_REG_THPEAK, 0x3C)   # Peak threshold

        # Set active period (higher = more responsive)
        self.write_reg(_REG_PERIODACTIVE, 0x06)

        # Enable gesture recognition
        if self.gesture_enabled:
            self.write_reg(_REG_G_MODE, 0x01)

    def write_reg(self, reg, value):
        """Write to touch controller register"""
        self.i2c.writeto_mem(self.address, reg, bytes([value]))

    def read_reg(self, reg, count=1):
        """Read from touch controller register"""
        data = self.i2c.readfrom_mem(self.address, reg, count)
        if count == 1:
            return data[0]
        return data

    def read_touches(self):
        """Read current touch points"""
        # Read touch status
        data = self.read_reg(_REG_DEV_MODE, 16)

        # Extract gesture
        self.gesture = data[1]

        # Extract touch count
        self.touch_count = data[2] & 0x0F
        if self.touch_count > 5:
            self.touch_count = 0

        # Clear previous touches
        self.touches = []

        # Read touch points
        for i in range(min(self.touch_count, 2)):  # Support up to 2 touches for now
            base = 3 + i * 6

            # Extract touch data
            xh = data[base]
            xl = data[base + 1]
            yh = data[base + 2]
            yl = data[base + 3]

            # Parse coordinates
            event = (xh >> 6) & 0x03
            x = ((xh & 0x0F) << 8) | xl
            y = ((yh & 0x0F) << 8) | yl

            # Create touch point
            touch = TouchPoint(x, y, event, i)
            if base + 5 < len(data):
                touch.weight = data[base + 4]
                touch.area = data[base + 5]

            self.touches.append(touch)

        return self.touches

    def get_touch(self):
        """Get primary touch point (simplified interface)"""
        self.read_touches()
        if self.touches:
            return (self.touches[0].x, self.touches[0].y, True)
        return (0, 0, False)

    def check_button(self, button_name):
        """Check if virtual button is pressed"""
        if button_name not in self.button_zones:
            return False

        zone = self.button_zones[button_name]

        for touch in self.touches:
            if (zone['x'] <= touch.x < zone['x'] + zone['w'] and
                zone['y'] <= touch.y < zone['y'] + zone['h']):
                if not zone['pressed']:
                    zone['pressed'] = True
                    return True

        # Button released
        if zone['pressed']:
            zone['pressed'] = False

        return False

    def get_gesture(self):
        """Get detected gesture"""
        gesture_map = {
            _GEST_ID_MOVE_UP: "SWIPE_UP",
            _GEST_ID_MOVE_DOWN: "SWIPE_DOWN",
            _GEST_ID_MOVE_LEFT: "SWIPE_LEFT",
            _GEST_ID_MOVE_RIGHT: "SWIPE_RIGHT",
            _GEST_ID_ZOOM_IN: "ZOOM_IN",
            _GEST_ID_ZOOM_OUT: "ZOOM_OUT"
        }
        return gesture_map.get(self.gesture, None)

    def detect_custom_gestures(self):
        """Detect custom gestures like long press and double tap"""
        current_time = time.ticks_ms()

        if self.touches:
            touch = self.touches[0]

            # Start of touch
            if touch.event == _EVENT_PRESS_DOWN:
                # Check for double tap
                if (self.last_touch_time and
                    time.ticks_diff(current_time, self.last_touch_time) < self.double_tap_time):
                    return "DOUBLE_TAP"

                self.touch_start_pos = (touch.x, touch.y)
                self.touch_start_time = current_time

            # During touch
            elif touch.event == _EVENT_CONTACT:
                if self.touch_start_time:
                    # Check for long press
                    if time.ticks_diff(current_time, self.touch_start_time) > self.long_press_time:
                        if self.touch_start_pos:
                            dx = abs(touch.x - self.touch_start_pos[0])
                            dy = abs(touch.y - self.touch_start_pos[1])
                            if dx < 10 and dy < 10:  # Minimal movement
                                return "LONG_PRESS"

            # End of touch
            elif touch.event == _EVENT_LIFT_UP:
                if self.touch_start_pos:
                    dx = touch.x - self.touch_start_pos[0]
                    dy = touch.y - self.touch_start_pos[1]

                    # Detect swipe
                    if abs(dx) > self.swipe_threshold or abs(dy) > self.swipe_threshold:
                        if abs(dx) > abs(dy):
                            return "SWIPE_RIGHT" if dx > 0 else "SWIPE_LEFT"
                        else:
                            return "SWIPE_DOWN" if dy > 0 else "SWIPE_UP"
                    else:
                        # Simple tap
                        self.last_touch_time = current_time
                        return "TAP"

                self.touch_start_pos = None
                self.touch_start_time = 0

        return None

    def emulate_joystick(self):
        """Emulate joystick input using touch swipes"""
        gesture = self.get_gesture() or self.detect_custom_gestures()

        joystick_map = {
            "SWIPE_UP": "UP",
            "SWIPE_DOWN": "DOWN",
            "SWIPE_LEFT": "LEFT",
            "SWIPE_RIGHT": "RIGHT",
            "TAP": "CENTER"
        }

        return joystick_map.get(gesture, None)

    def calibrate(self):
        """Run touch calibration routine"""
        print("Touch calibration started...")
        # Calibration would involve touching specific points
        # and adjusting offset registers
        pass

    def sleep(self):
        """Put touch controller to sleep"""
        self.write_reg(_REG_PWR_MODE, 0x03)  # Deep sleep mode

    def wake(self):
        """Wake touch controller from sleep"""
        self.write_reg(_REG_PWR_MODE, 0x00)  # Normal mode

class TouchButtons:
    """Virtual button handler for touch screen"""

    def __init__(self, touch_controller):
        self.touch = touch_controller
        self.button_states = {
            'A': {'pressed': False, 'held': False, 'hold_start': 0},
            'B': {'pressed': False, 'held': False, 'hold_start': 0},
            'X': {'pressed': False, 'held': False, 'hold_start': 0},
            'Y': {'pressed': False, 'held': False, 'hold_start': 0}
        }
        self.hold_threshold = 500  # ms for hold detection

    def update(self):
        """Update button states"""
        self.touch.read_touches()
        current_time = time.ticks_ms()

        for button in ['A', 'B', 'X', 'Y']:
            was_pressed = self.button_states[button]['pressed']
            is_pressed = self.touch.check_button(button)

            # Detect press edge
            if is_pressed and not was_pressed:
                self.button_states[button]['pressed'] = True
                self.button_states[button]['hold_start'] = current_time

            # Detect release edge
            elif not is_pressed and was_pressed:
                self.button_states[button]['pressed'] = False
                self.button_states[button]['held'] = False
                self.button_states[button]['hold_start'] = 0

            # Check for hold
            if is_pressed:
                hold_time = time.ticks_diff(current_time, self.button_states[button]['hold_start'])
                if hold_time > self.hold_threshold:
                    self.button_states[button]['held'] = True

    def is_pressed(self, button):
        """Check if button was just pressed"""
        return self.button_states.get(button, {}).get('pressed', False)

    def is_held(self, button):
        """Check if button is being held"""
        return self.button_states.get(button, {}).get('held', False)

    def clear(self):
        """Clear all button states"""
        for button in self.button_states:
            self.button_states[button] = {'pressed': False, 'held': False, 'hold_start': 0}