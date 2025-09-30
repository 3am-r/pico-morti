"""
Fidget-First Launcher - The home screen itself is a toy
Morti responds to joystick movements, A opens last app, B toggles screen-off fidget mode
"""

import time
import math
import random
from lib.st7789 import Color
from lib.haptics import get_haptics
from apps.fidget_core import FidgetCore
from launcher_utils import LauncherUtils

class FidgetLauncher:
    def __init__(self, apps, display, joystick, buttons):
        """Initialize fidget-first launcher"""
        self.apps = apps
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        self.utils = LauncherUtils(display, apps)

        self.haptics = get_haptics()

        self.morti = {
            "x": display.width // 2,
            "y": display.height // 2,
            "vx": 0,
            "vy": 0,
            "size": 20,
            "mood": "happy",
            "wiggle": 0,
            "energy": 50,
            "last_interaction": time.ticks_ms()
        }

        self.particles = []
        self.trails = []
        self.max_trails = 20

        self.last_app = None
        self.last_app_index = 0
        self.screen_off_mode = False
        self.fidget_core = None

        self.animation_frame = 0
        self.last_update = time.ticks_ms()

        self.physics_enabled = True
        self.gravity = 0.3
        self.friction = 0.95
        self.bounce_damping = 0.7

        self.background_elements = []
        self.init_background()

        self.load_preferences()

    def init(self):
        """Initialize launcher when activated"""
        self.draw_screen()
        if self.haptics:
            self.haptics.tap(0.3)

    def init_background(self):
        """Initialize background animated elements"""
        for _ in range(5):
            self.background_elements.append({
                "x": random.randint(0, self.display.width),
                "y": random.randint(0, self.display.height),
                "vx": random.uniform(-0.5, 0.5),
                "vy": random.uniform(-0.5, 0.5),
                "size": random.randint(2, 5),
                "color": random.choice([Color.DARK_GRAY, Color.GRAY])
            })

    def handle_input(self):
        """Handle user input"""
        current_time = time.ticks_ms()

        if self.screen_off_mode:
            if self.fidget_core:
                if self.buttons.is_pressed('B'):
                    time.sleep_ms(200)
                    self.exit_screen_off_mode()
                    return "continue"
                if self.buttons.is_pressed('X'):
                    self.fidget_core.stop()
                    return "exit"
            return "continue"

        joy_moved = False
        if self.joystick.up_pin.value() == 0:
            self.morti["vy"] -= 2
            joy_moved = True
        if self.joystick.down_pin.value() == 0:
            self.morti["vy"] += 2
            joy_moved = True
        if self.joystick.left_pin.value() == 0:
            self.morti["vx"] -= 2
            joy_moved = True
        if self.joystick.right_pin.value() == 0:
            self.morti["vx"] += 2
            joy_moved = True

        if joy_moved:
            self.morti["energy"] = min(100, self.morti["energy"] + 3)
            self.morti["last_interaction"] = current_time
            self.morti["wiggle"] = 10

            if self.haptics:
                self.haptics.tap(0.2)

            self.create_movement_particles()

        if self.joystick.center_pin.value() == 0:
            self.morti_jump()
            time.sleep_ms(200)

        if self.buttons.is_pressed('A'):
            time.sleep_ms(200)
            return self.open_last_app()

        if self.buttons.is_pressed('B'):
            time.sleep_ms(200)
            self.enter_screen_off_mode()
            return "continue"

        if self.buttons.is_pressed('X'):
            time.sleep_ms(200)
            return self.show_quick_menu()

        if self.buttons.is_pressed('Y'):
            self.cycle_morti_mood()
            time.sleep_ms(200)

        self.update_physics()
        self.update_particles()
        self.update_background()
        self.draw_screen()

        return "continue"

    def morti_jump(self):
        """Make Morti jump"""
        self.morti["vy"] = -8
        self.morti["energy"] = min(100, self.morti["energy"] + 10)
        self.morti["mood"] = "excited"

        if self.haptics:
            self.haptics.bounce(0.8)

        for _ in range(10):
            self.particles.append({
                "x": self.morti["x"],
                "y": self.morti["y"] + self.morti["size"],
                "vx": random.uniform(-3, 3),
                "vy": random.uniform(0, 3),
                "life": 20,
                "color": Color.YELLOW
            })

    def cycle_morti_mood(self):
        """Cycle through Morti moods"""
        moods = ["happy", "excited", "calm", "sleepy", "playful"]
        current_index = moods.index(self.morti["mood"]) if self.morti["mood"] in moods else 0
        self.morti["mood"] = moods[(current_index + 1) % len(moods)]

        if self.haptics:
            self.haptics.tap(0.4)

    def create_movement_particles(self):
        """Create particles when Morti moves"""
        for _ in range(3):
            self.particles.append({
                "x": self.morti["x"],
                "y": self.morti["y"],
                "vx": -self.morti["vx"] * 0.3 + random.uniform(-1, 1),
                "vy": -self.morti["vy"] * 0.3 + random.uniform(-1, 1),
                "life": 15,
                "color": self.get_mood_color()
            })

    def update_physics(self):
        """Update Morti physics"""
        if not self.physics_enabled:
            return

        self.morti["vy"] += self.gravity

        self.morti["vx"] *= self.friction
        self.morti["vy"] *= self.friction

        self.morti["x"] += self.morti["vx"]
        self.morti["y"] += self.morti["vy"]

        margin = self.morti["size"] // 2
        if self.morti["x"] < margin:
            self.morti["x"] = margin
            self.morti["vx"] = abs(self.morti["vx"]) * self.bounce_damping
            self.create_bounce_effect()
        elif self.morti["x"] > self.display.width - margin:
            self.morti["x"] = self.display.width - margin
            self.morti["vx"] = -abs(self.morti["vx"]) * self.bounce_damping
            self.create_bounce_effect()

        if self.morti["y"] < margin:
            self.morti["y"] = margin
            self.morti["vy"] = abs(self.morti["vy"]) * self.bounce_damping
        elif self.morti["y"] > self.display.height - margin:
            self.morti["y"] = self.display.height - margin
            self.morti["vy"] = -abs(self.morti["vy"]) * self.bounce_damping
            self.create_bounce_effect()

        self.morti["energy"] *= 0.99

        if self.morti["wiggle"] > 0:
            self.morti["wiggle"] -= 1

        self.trails.append({
            "x": self.morti["x"],
            "y": self.morti["y"],
            "size": self.morti["size"] * 0.8
        })
        if len(self.trails) > self.max_trails:
            self.trails.pop(0)

    def create_bounce_effect(self):
        """Create visual effect when Morti bounces"""
        if self.haptics:
            self.haptics.tap(0.5)

        for _ in range(5):
            self.particles.append({
                "x": self.morti["x"],
                "y": self.morti["y"],
                "vx": random.uniform(-2, 2),
                "vy": random.uniform(-2, 2),
                "life": 10,
                "color": Color.WHITE
            })

    def update_particles(self):
        """Update particle system"""
        for particle in self.particles[:]:
            particle["x"] += particle["vx"]
            particle["y"] += particle["vy"]
            particle["life"] -= 1

            if particle["life"] <= 0:
                self.particles.remove(particle)

    def update_background(self):
        """Update background elements"""
        for elem in self.background_elements:
            elem["x"] += elem["vx"]
            elem["y"] += elem["vy"]

            if elem["x"] < 0 or elem["x"] > self.display.width:
                elem["vx"] = -elem["vx"]
            if elem["y"] < 0 or elem["y"] > self.display.height:
                elem["vy"] = -elem["vy"]

    def draw_screen(self):
        """Draw the launcher screen"""
        self.display.fill(Color.BLACK)

        for elem in self.background_elements:
            self.display.fill_rect(
                int(elem["x"]) - elem["size"] // 2,
                int(elem["y"]) - elem["size"] // 2,
                elem["size"], elem["size"],
                elem["color"]
            )

        for i, trail in enumerate(self.trails):
            fade = i / len(self.trails) if self.trails else 1
            size = int(trail["size"] * fade)
            if size > 0:
                color = self.fade_color(self.get_mood_color(), fade * 0.3)
                self.display.fill_rect(
                    int(trail["x"]) - size // 2,
                    int(trail["y"]) - size // 2,
                    size, size, color
                )

        for particle in self.particles:
            fade = particle["life"] / 20
            self.display.fill_rect(
                int(particle["x"]) - 1,
                int(particle["y"]) - 1,
                2, 2,
                self.fade_color(particle["color"], fade)
            )

        self.draw_morti()

        self.draw_status_indicators()

        self.display.display()

    def draw_morti(self):
        """Draw Morti character"""
        x, y = int(self.morti["x"]), int(self.morti["y"])
        size = self.morti["size"]

        if self.morti["wiggle"] > 0:
            x += random.randint(-2, 2)
            y += random.randint(-2, 2)

        mood_color = self.get_mood_color()

        body_size = size
        self.display.fill_rect(
            x - body_size // 2,
            y - body_size // 2,
            body_size, body_size,
            mood_color
        )

        glow_size = body_size + 4
        for i in range(2, glow_size, 2):
            fade = 1 - (i / glow_size)
            self.display.rect(
                x - i // 2,
                y - i // 2,
                i, i,
                self.fade_color(mood_color, fade * 0.3)
            )

        eye_offset = size // 4
        eye_size = 3

        if self.morti["mood"] == "sleepy":
            self.display.line(
                x - eye_offset - 2, y - 2,
                x - eye_offset + 2, y - 2,
                Color.WHITE
            )
            self.display.line(
                x + eye_offset - 2, y - 2,
                x + eye_offset + 2, y - 2,
                Color.WHITE
            )
        else:
            self.display.fill_rect(
                x - eye_offset - eye_size // 2,
                y - 3,
                eye_size, eye_size,
                Color.WHITE
            )
            self.display.fill_rect(
                x + eye_offset - eye_size // 2,
                y - 3,
                eye_size, eye_size,
                Color.WHITE
            )

            if self.morti["mood"] == "excited":
                sparkle_offset = 2
                self.display.pixel(x - eye_offset + sparkle_offset, y - 3, Color.YELLOW)
                self.display.pixel(x + eye_offset + sparkle_offset, y - 3, Color.YELLOW)

        if self.morti["mood"] in ["happy", "excited", "playful"]:
            mouth_width = size // 3
            self.display.line(
                x - mouth_width, y + 3,
                x + mouth_width, y + 3,
                Color.WHITE
            )
            self.display.pixel(x - mouth_width, y + 2, Color.WHITE)
            self.display.pixel(x + mouth_width, y + 2, Color.WHITE)
        elif self.morti["mood"] == "calm":
            self.display.line(
                x - 2, y + 3,
                x + 2, y + 3,
                Color.WHITE
            )

        if self.morti["energy"] > 70:
            energy_radius = 15
            points = 8
            for i in range(points):
                angle = (time.ticks_ms() / 50 + i * 360 / points) % 360
                px = x + int(math.cos(math.radians(angle)) * energy_radius)
                py = y + int(math.sin(math.radians(angle)) * energy_radius)
                if 0 <= px < self.display.width and 0 <= py < self.display.height:
                    self.display.pixel(px, py, Color.YELLOW)

    def draw_status_indicators(self):
        """Draw minimal status indicators"""
        if self.last_app:
            self.display.text("A: Last App", 5, 5, Color.DARK_GRAY)

        self.display.text("B: Fidget", self.display.width - 70, 5, Color.DARK_GRAY)

        energy_width = 30
        energy_fill = int(energy_width * self.morti["energy"] / 100)
        self.display.rect(5, self.display.height - 10, energy_width, 5, Color.DARK_GRAY)
        if energy_fill > 0:
            self.display.fill_rect(5, self.display.height - 10, energy_fill, 5, self.get_mood_color())

    def get_mood_color(self):
        """Get color based on Morti's mood"""
        mood_colors = {
            "happy": Color.GREEN,
            "excited": Color.YELLOW,
            "calm": Color.BLUE,
            "sleepy": Color.PURPLE,
            "playful": Color.ORANGE
        }
        return mood_colors.get(self.morti["mood"], Color.WHITE)

    def fade_color(self, color, fade):
        """Fade a color by factor"""
        r = ((color >> 11) & 0x1F) * fade
        g = ((color >> 5) & 0x3F) * fade
        b = (color & 0x1F) * fade
        return ((int(r) & 0x1F) << 11) | ((int(g) & 0x3F) << 5) | (int(b) & 0x1F)

    def open_last_app(self):
        """Open the last used app"""
        if self.last_app:
            if self.haptics:
                self.haptics.success()
            return ("app", self.last_app)
        else:
            return self.show_app_list()

    def show_quick_menu(self):
        """Show quick menu for app selection"""
        return self.show_app_list()

    def show_app_list(self):
        """Show scrollable app list"""
        selected = 0
        scroll_offset = 0
        items_per_page = 8

        while True:
            self.display.fill(Color.BLACK)

            self.display.text("Select App", 10, 10, Color.WHITE)
            self.display.line(10, 25, self.display.width - 10, 25, Color.GRAY)

            visible_start = scroll_offset
            visible_end = min(scroll_offset + items_per_page, len(self.apps))

            for i in range(visible_start, visible_end):
                y_pos = 35 + (i - visible_start) * 20
                app = self.apps[i]
                app_info = self.utils.get_app_info(app)

                if i == selected:
                    self.display.fill_rect(5, y_pos - 2, self.display.width - 10, 18, Color.DARK_GRAY)
                    text_color = Color.WHITE
                else:
                    text_color = Color.GRAY

                self.display.text(app_info["display_name"], 10, y_pos, text_color)

            if scroll_offset > 0:
                self.display.text("^", self.display.width - 15, 35, Color.GRAY)
            if visible_end < len(self.apps):
                self.display.text("v", self.display.width - 15, self.display.height - 20, Color.GRAY)

            self.display.display()

            if self.joystick.up_pin.value() == 0:
                if selected > 0:
                    selected -= 1
                    if selected < scroll_offset:
                        scroll_offset = selected
                time.sleep_ms(150)

            elif self.joystick.down_pin.value() == 0:
                if selected < len(self.apps) - 1:
                    selected += 1
                    if selected >= scroll_offset + items_per_page:
                        scroll_offset = selected - items_per_page + 1
                time.sleep_ms(150)

            elif self.buttons.is_pressed('A') or self.joystick.center.value() == 0:
                self.last_app = self.apps[selected]
                self.last_app_index = selected
                self.save_preferences()
                time.sleep_ms(200)
                if self.haptics:
                    self.haptics.success()
                return ("app", self.apps[selected])

            elif self.buttons.is_pressed('B') or self.buttons.is_pressed('X'):
                time.sleep_ms(200)
                return "continue"

    def enter_screen_off_mode(self):
        """Enter screen-off fidget mode"""
        self.screen_off_mode = True
        self.display.fill(Color.BLACK)
        self.display.text("Screen Off", self.display.width // 2 - 40, self.display.height // 2 - 10, Color.DARK_GRAY)
        self.display.text("B to wake", self.display.width // 2 - 35, self.display.height // 2 + 10, Color.DARK_GRAY)
        self.display.display()

        time.sleep(1)

        self.display.fill(Color.BLACK)
        self.display.display()

        if self.haptics:
            self.haptics.pulse(100, 0.5)

        self.fidget_core = FidgetCore(self.display, self.joystick, self.buttons, self.haptics)
        self.fidget_core.screen_optional = True
        self.fidget_core.start()

    def exit_screen_off_mode(self):
        """Exit screen-off mode"""
        self.screen_off_mode = False
        if self.fidget_core:
            self.fidget_core.stop()
            self.fidget_core = None

        if self.haptics:
            self.haptics.tap(0.5)

        self.draw_screen()

    def save_preferences(self):
        """Save launcher preferences"""
        try:
            import json
            prefs = {
                "last_app_index": self.last_app_index,
                "morti_mood": self.morti["mood"]
            }
            with open("/stores/fidget_prefs.json", "w") as f:
                json.dump(prefs, f)
        except:
            pass

    def load_preferences(self):
        """Load launcher preferences"""
        try:
            import json
            with open("/stores/fidget_prefs.json", "r") as f:
                prefs = json.load(f)
                self.last_app_index = prefs.get("last_app_index", 0)
                if 0 <= self.last_app_index < len(self.apps):
                    self.last_app = self.apps[self.last_app_index]
                self.morti["mood"] = prefs.get("morti_mood", "happy")
        except:
            pass