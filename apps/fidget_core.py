"""
Fidget Core - High-frequency input event loop for kinetic interactions
60Hz input processing with visual and haptic feedback
"""

import time
from machine import Pin, Timer
from lib.st7789 import Color
import math
import random

class FidgetCore:
    def __init__(self, display, joystick, buttons, haptics=None):
        """Initialize fidget core with high-frequency input handling"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        self.haptics = haptics

        self.running = False
        self.screen_optional = False
        self.target_fps = 60
        self.frame_time = 1000 // self.target_fps

        self.interactions = {
            "bounce": BounceInteraction(display),
            "ripple": RippleInteraction(display),
            "pulse": PulseInteraction(display),
            "swirl": SwirlInteraction(display),
            "shake": ShakeInteraction(display)
        }
        self.current_interaction = "bounce"

        self.input_buffer = []
        self.input_history = []
        self.max_history = 30

        self.fidget_profile = "neutral"
        self.profiles = {
            "calm": {"speed": 0.5, "haptic_strength": 0.3, "colors": [Color.BLUE, Color.CYAN, Color.WHITE]},
            "neutral": {"speed": 1.0, "haptic_strength": 0.6, "colors": [Color.GREEN, Color.YELLOW, Color.ORANGE]},
            "zesty": {"speed": 1.5, "haptic_strength": 1.0, "colors": [Color.RED, Color.MAGENTA, Color.YELLOW]}
        }

        self.morti_state = {
            "x": display.width // 2,
            "y": display.height // 2,
            "vx": 0,
            "vy": 0,
            "energy": 0,
            "mood": "neutral"
        }

        self.last_input_time = time.ticks_ms()
        self.combo_detector = ComboDetector()

    def start(self):
        """Start the high-frequency event loop"""
        self.running = True
        last_frame = time.ticks_ms()

        while self.running:
            current_time = time.ticks_ms()
            delta_time = time.ticks_diff(current_time, last_frame)

            if delta_time >= self.frame_time:
                self.process_frame(delta_time)
                last_frame = current_time

            time.sleep_ms(1)

    def process_frame(self, delta_time):
        """Process a single frame at 60Hz"""
        self.read_inputs()

        self.update_physics(delta_time)

        if not self.screen_optional:
            self.render_frame()

        self.process_haptic_feedback()

        self.detect_patterns()

    def read_inputs(self):
        """Read all inputs at high frequency"""
        current_time = time.ticks_ms()

        joy_state = {
            "up": self.joystick.up_pin.value() == 0,
            "down": self.joystick.down_pin.value() == 0,
            "left": self.joystick.left_pin.value() == 0,
            "right": self.joystick.right_pin.value() == 0,
            "center": self.joystick.center_pin.value() == 0
        }

        btn_state = {
            "a": self.buttons.is_held('A'),
            "b": self.buttons.is_held('B'),
            "x": self.buttons.is_held('X'),
            "y": self.buttons.is_held('Y')
        }

        input_event = {
            "time": current_time,
            "joystick": joy_state,
            "buttons": btn_state
        }

        self.input_buffer.append(input_event)
        if len(self.input_buffer) > 10:
            self.input_buffer.pop(0)

        self.input_history.append(input_event)
        if len(self.input_history) > self.max_history:
            self.input_history.pop(0)

        if any(joy_state.values()) or any(btn_state.values()):
            self.last_input_time = current_time
            self.morti_state["energy"] = min(100, self.morti_state["energy"] + 2)

    def update_physics(self, delta_time):
        """Update physics simulations"""
        profile = self.profiles[self.fidget_profile]
        speed_mult = profile["speed"]

        if self.input_buffer:
            latest = self.input_buffer[-1]
            joy = latest["joystick"]

            if joy["left"]:
                self.morti_state["vx"] -= 0.5 * speed_mult
            if joy["right"]:
                self.morti_state["vx"] += 0.5 * speed_mult
            if joy["up"]:
                self.morti_state["vy"] -= 0.5 * speed_mult
            if joy["down"]:
                self.morti_state["vy"] += 0.5 * speed_mult

        self.morti_state["vx"] *= 0.95
        self.morti_state["vy"] *= 0.95

        self.morti_state["x"] += self.morti_state["vx"]
        self.morti_state["y"] += self.morti_state["vy"]

        if self.morti_state["x"] < 20:
            self.morti_state["x"] = 20
            self.morti_state["vx"] = abs(self.morti_state["vx"]) * 0.8
        elif self.morti_state["x"] > self.display.width - 20:
            self.morti_state["x"] = self.display.width - 20
            self.morti_state["vx"] = -abs(self.morti_state["vx"]) * 0.8

        if self.morti_state["y"] < 20:
            self.morti_state["y"] = 20
            self.morti_state["vy"] = abs(self.morti_state["vy"]) * 0.8
        elif self.morti_state["y"] > self.display.height - 20:
            self.morti_state["y"] = self.display.height - 20
            self.morti_state["vy"] = -abs(self.morti_state["vy"]) * 0.8

        self.morti_state["energy"] *= 0.98

        interaction = self.interactions.get(self.current_interaction)
        if interaction:
            interaction.update(self.morti_state, self.input_buffer, delta_time)

    def render_frame(self):
        """Render visual feedback"""
        if self.screen_optional:
            return

        self.display.fill(Color.BLACK)

        interaction = self.interactions.get(self.current_interaction)
        if interaction:
            interaction.render(self.display, self.profiles[self.fidget_profile])

        self.draw_morti()

        if self.morti_state["energy"] > 80:
            self.draw_energy_particles()

        self.display.display()

    def draw_morti(self):
        """Draw Morti character"""
        x, y = int(self.morti_state["x"]), int(self.morti_state["y"])
        energy = self.morti_state["energy"]

        size = 8 + int(energy / 20)

        profile_colors = self.profiles[self.fidget_profile]["colors"]
        color = profile_colors[int(time.ticks_ms() / 500) % len(profile_colors)]

        for i in range(size, 0, -2):
            fade = i / size
            self.display.fill_rect(x - i, y - i, i * 2, i * 2,
                                  self.fade_color(color, fade))

        eye_offset = 3
        self.display.fill_rect(x - eye_offset - 2, y - 2, 2, 2, Color.WHITE)
        self.display.fill_rect(x + eye_offset, y - 2, 2, 2, Color.WHITE)

        if energy > 50:
            self.display.fill_rect(x - 3, y + 3, 6, 2, Color.WHITE)

    def draw_energy_particles(self):
        """Draw energy particles around Morti"""
        x, y = int(self.morti_state["x"]), int(self.morti_state["y"])
        energy = self.morti_state["energy"]

        particle_count = int(energy / 10)
        for i in range(particle_count):
            angle = (time.ticks_ms() / 50 + i * 360 / particle_count) % 360
            radius = 15 + (i % 3) * 5
            px = x + int(math.cos(math.radians(angle)) * radius)
            py = y + int(math.sin(math.radians(angle)) * radius)

            if 0 <= px < self.display.width and 0 <= py < self.display.height:
                self.display.pixel(px, py, Color.YELLOW)

    def process_haptic_feedback(self):
        """Generate haptic feedback based on interactions"""
        if not self.haptics:
            return

        profile = self.profiles[self.fidget_profile]
        strength = profile["haptic_strength"]

        if self.morti_state["energy"] > 90:
            self.haptics.pulse(int(10 * strength))

        if abs(self.morti_state["vx"]) > 5 or abs(self.morti_state["vy"]) > 5:
            self.haptics.tap(strength)

    def detect_patterns(self):
        """Detect input patterns and combos"""
        combo = self.combo_detector.check(self.input_history)
        if combo:
            self.handle_combo(combo)

    def handle_combo(self, combo):
        """Handle detected input combos"""
        if combo == "circle":
            self.current_interaction = "swirl"
            if self.haptics:
                self.haptics.celebrate()
        elif combo == "shake":
            self.current_interaction = "shake"
            self.morti_state["energy"] = 100
        elif combo == "tap_tap":
            self.current_interaction = "pulse"

    def fade_color(self, color, fade):
        """Fade a color by a factor"""
        r = ((color >> 11) & 0x1F) * fade
        g = ((color >> 5) & 0x3F) * fade
        b = (color & 0x1F) * fade
        return ((int(r) & 0x1F) << 11) | ((int(g) & 0x3F) << 5) | (int(b) & 0x1F)

    def toggle_screen(self):
        """Toggle screen-optional mode"""
        self.screen_optional = not self.screen_optional
        if self.screen_optional:
            self.display.fill(Color.BLACK)
            self.display.display()

    def set_profile(self, profile_name):
        """Set fidget profile"""
        if profile_name in self.profiles:
            self.fidget_profile = profile_name

    def stop(self):
        """Stop the event loop"""
        self.running = False


class BounceInteraction:
    def __init__(self, display):
        self.display = display
        self.particles = []

    def update(self, morti_state, input_buffer, delta_time):
        if morti_state["energy"] > 30:
            self.particles.append({
                "x": morti_state["x"],
                "y": morti_state["y"],
                "vx": random.uniform(-2, 2),
                "vy": random.uniform(-2, 2),
                "life": 30
            })

        for p in self.particles[:]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vy"] += 0.2
            p["life"] -= 1

            if p["life"] <= 0:
                self.particles.remove(p)

    def render(self, display, profile):
        for p in self.particles:
            if 0 <= p["x"] < display.width and 0 <= p["y"] < display.height:
                color = profile["colors"][0]
                display.pixel(int(p["x"]), int(p["y"]), color)


class RippleInteraction:
    def __init__(self, display):
        self.display = display
        self.ripples = []

    def update(self, morti_state, input_buffer, delta_time):
        if morti_state["energy"] > 20 and random.random() < 0.1:
            self.ripples.append({
                "x": morti_state["x"],
                "y": morti_state["y"],
                "radius": 0,
                "max_radius": 30
            })

        for r in self.ripples[:]:
            r["radius"] += 1
            if r["radius"] > r["max_radius"]:
                self.ripples.remove(r)

    def render(self, display, profile):
        for r in self.ripples:
            radius = int(r["radius"])
            fade = 1.0 - (r["radius"] / r["max_radius"])
            color = profile["colors"][1]

            for angle in range(0, 360, 30):
                x = r["x"] + int(math.cos(math.radians(angle)) * radius)
                y = r["y"] + int(math.sin(math.radians(angle)) * radius)

                if 0 <= x < display.width and 0 <= y < display.height:
                    display.pixel(x, y, color)


class PulseInteraction:
    def __init__(self, display):
        self.display = display
        self.pulse_phase = 0

    def update(self, morti_state, input_buffer, delta_time):
        self.pulse_phase += 0.1

    def render(self, display, profile):
        intensity = (math.sin(self.pulse_phase) + 1) / 2
        color = profile["colors"][2]

        for x in range(0, display.width, 20):
            for y in range(0, display.height, 20):
                if random.random() < intensity * 0.3:
                    display.pixel(x, y, color)


class SwirlInteraction:
    def __init__(self, display):
        self.display = display
        self.angle = 0

    def update(self, morti_state, input_buffer, delta_time):
        self.angle += 5

    def render(self, display, profile):
        cx, cy = display.width // 2, display.height // 2

        for i in range(8):
            angle = self.angle + i * 45
            radius = 20 + i * 5
            x = cx + int(math.cos(math.radians(angle)) * radius)
            y = cy + int(math.sin(math.radians(angle)) * radius)

            color = profile["colors"][i % len(profile["colors"])]
            if 0 <= x < display.width and 0 <= y < display.height:
                display.fill_rect(x - 2, y - 2, 4, 4, color)


class ShakeInteraction:
    def __init__(self, display):
        self.display = display
        self.shake_amount = 0

    def update(self, morti_state, input_buffer, delta_time):
        self.shake_amount = morti_state["energy"] / 10

    def render(self, display, profile):
        if self.shake_amount > 0:
            offset_x = random.uniform(-self.shake_amount, self.shake_amount)
            offset_y = random.uniform(-self.shake_amount, self.shake_amount)

            display.fill_rect(int(offset_x), int(offset_y),
                            display.width, display.height, Color.BLACK)


class ComboDetector:
    def __init__(self):
        self.patterns = {
            "circle": self.detect_circle,
            "shake": self.detect_shake,
            "tap_tap": self.detect_double_tap
        }

    def check(self, input_history):
        for pattern_name, detector in self.patterns.items():
            if detector(input_history):
                return pattern_name
        return None

    def detect_circle(self, history):
        if len(history) < 8:
            return False

        directions = []
        for event in history[-8:]:
            if event["joystick"]["up"]:
                directions.append("u")
            elif event["joystick"]["right"]:
                directions.append("r")
            elif event["joystick"]["down"]:
                directions.append("d")
            elif event["joystick"]["left"]:
                directions.append("l")

        pattern = "".join(directions)
        return "urdl" in pattern or "rdlu" in pattern or "dlur" in pattern or "lurd" in pattern

    def detect_shake(self, history):
        if len(history) < 6:
            return False

        changes = 0
        last_dir = None

        for event in history[-6:]:
            joy = event["joystick"]
            current_dir = None

            if joy["left"]:
                current_dir = "l"
            elif joy["right"]:
                current_dir = "r"

            if current_dir and current_dir != last_dir:
                changes += 1
                last_dir = current_dir

        return changes >= 4

    def detect_double_tap(self, history):
        if len(history) < 4:
            return False

        taps = 0
        last_tap_time = 0

        for event in history[-4:]:
            if event["buttons"]["a"]:
                if last_tap_time and (event["time"] - last_tap_time) < 300:
                    return True
                last_tap_time = event["time"]
                taps += 1

        return False