"""
Touch-based Joystick Emulation
Converts touch gestures to joystick-like inputs for compatibility
"""

import time

class TouchJoystick:
    """Emulate joystick using touch screen gestures"""

    def __init__(self, touch_controller):
        """
        Initialize touch-based joystick

        Args:
            touch_controller: FT3168Touch instance
        """
        self.touch = touch_controller

        # Virtual pin states (emulating physical pins)
        self.pin_states = {
            'up': True,      # True = not pressed (pull-up)
            'down': True,
            'left': True,
            'right': True,
            'center': True
        }

        # Gesture tracking
        self.last_gesture_time = 0
        self.gesture_cooldown = 200  # ms between gestures

        # Create virtual pin objects for compatibility
        self.up_pin = VirtualPin(self, 'up')
        self.down_pin = VirtualPin(self, 'down')
        self.left_pin = VirtualPin(self, 'left')
        self.right_pin = VirtualPin(self, 'right')
        self.center_pin = VirtualPin(self, 'center')

    def update(self):
        """Update virtual joystick state from touch input"""
        current_time = time.ticks_ms()

        # Check cooldown
        if time.ticks_diff(current_time, self.last_gesture_time) < self.gesture_cooldown:
            return

        # Read touch and get gesture
        self.touch.read_touches()
        direction = self.touch.emulate_joystick()

        # Reset all states (pull-up = True = not pressed)
        for key in self.pin_states:
            self.pin_states[key] = True

        # Set state based on gesture
        if direction:
            direction_lower = direction.lower()
            if direction_lower in self.pin_states:
                self.pin_states[direction_lower] = False  # False = pressed (pull-down)
                self.last_gesture_time = current_time

    def is_pressed(self, direction):
        """Check if direction is currently pressed"""
        self.update()
        return not self.pin_states.get(direction, True)

    def get_state(self):
        """Get current joystick state"""
        self.update()
        return {
            'up': not self.pin_states['up'],
            'down': not self.pin_states['down'],
            'left': not self.pin_states['left'],
            'right': not self.pin_states['right'],
            'center': not self.pin_states['center']
        }

class VirtualPin:
    """Virtual pin object for compatibility with hardware pin interface"""

    def __init__(self, joystick, direction):
        """
        Initialize virtual pin

        Args:
            joystick: TouchJoystick instance
            direction: Pin direction (up, down, left, right, center)
        """
        self.joystick = joystick
        self.direction = direction

    def value(self):
        """Get pin value (0 = pressed, 1 = not pressed)"""
        self.joystick.update()
        return 1 if self.joystick.pin_states[self.direction] else 0

    def __call__(self):
        """Allow pin to be called as function"""
        return self.value()

class TouchDPad:
    """Alternative D-Pad style touch control using screen zones"""

    def __init__(self, touch_controller, display_width, display_height):
        """
        Initialize touch D-Pad with screen zones

        Args:
            touch_controller: FT3168Touch instance
            display_width: Screen width
            display_height: Screen height
        """
        self.touch = touch_controller
        self.width = display_width
        self.height = display_height

        # Define D-Pad zones (center of screen)
        pad_size = min(display_width, display_height) // 3
        center_x = display_width // 2
        center_y = display_height // 2

        self.zones = {
            'up': {
                'x1': center_x - pad_size // 2,
                'x2': center_x + pad_size // 2,
                'y1': center_y - pad_size,
                'y2': center_y - pad_size // 2
            },
            'down': {
                'x1': center_x - pad_size // 2,
                'x2': center_x + pad_size // 2,
                'y1': center_y + pad_size // 2,
                'y2': center_y + pad_size
            },
            'left': {
                'x1': center_x - pad_size,
                'x2': center_x - pad_size // 2,
                'y1': center_y - pad_size // 2,
                'y2': center_y + pad_size // 2
            },
            'right': {
                'x1': center_x + pad_size // 2,
                'x2': center_x + pad_size,
                'y1': center_y - pad_size // 2,
                'y2': center_y + pad_size // 2
            },
            'center': {
                'x1': center_x - pad_size // 2,
                'x2': center_x + pad_size // 2,
                'y1': center_y - pad_size // 2,
                'y2': center_y + pad_size // 2
            }
        }

    def get_direction(self, x, y):
        """Get direction based on touch coordinates"""
        for direction, zone in self.zones.items():
            if (zone['x1'] <= x <= zone['x2'] and
                zone['y1'] <= y <= zone['y2']):
                return direction
        return None

    def draw_overlay(self, display):
        """Draw D-Pad overlay on screen (for debugging/visualization)"""
        from lib.st7789 import Color

        for direction, zone in self.zones.items():
            # Draw zone outline
            display.rect(
                zone['x1'], zone['y1'],
                zone['x2'] - zone['x1'],
                zone['y2'] - zone['y1'],
                Color.GRAY
            )

            # Draw direction label
            label_x = (zone['x1'] + zone['x2']) // 2 - 4
            label_y = (zone['y1'] + zone['y2']) // 2 - 4
            if direction == 'up':
                display.text("↑", label_x, label_y, Color.WHITE)
            elif direction == 'down':
                display.text("↓", label_x, label_y, Color.WHITE)
            elif direction == 'left':
                display.text("←", label_x, label_y, Color.WHITE)
            elif direction == 'right':
                display.text("→", label_x, label_y, Color.WHITE)
            elif direction == 'center':
                display.text("●", label_x, label_y, Color.WHITE)