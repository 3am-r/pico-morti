"""
Breath - Guided breathing app with haptic feedback
Supports Box, 4-7-8, Resonant, and Custom breathing patterns
"""

import time
import math
import json
from lib.st7789 import Color
from lib.haptics import get_haptics

class Breath:
    def __init__(self, display, joystick, buttons):
        """Initialize Breath app"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons

        # Get haptics system
        self.haptics = get_haptics()

        # App state
        self.mode = "menu"  # "menu", "calibrate", "breathing", "help"
        self.selected_option = 0
        self.breathing_active = False
        self.paused = False
        self.screen_off = False

        # Breathing patterns (seconds)
        self.patterns = {
            "box": {
                "name": "Box 4-4-4-4",
                "phases": [4.0, 4.0, 4.0, 4.0],  # inhale, hold, exhale, hold
                "description": "Equal timing"
            },
            "478": {
                "name": "4-7-8 Relax",
                "phases": [4.0, 7.0, 8.0, 0.0],
                "description": "Sleep aid"
            },
            "resonant": {
                "name": "Resonant 5-0-5-0",
                "phases": [5.0, 0.0, 5.0, 0.0],
                "description": "Heart coherence"
            },
            "custom": {
                "name": "Custom",
                "phases": [6.0, 2.0, 6.0, 2.0],
                "description": "Your settings"
            }
        }

        # Current settings
        self.current_pattern = "resonant"
        self.intensity = 1.0  # 0.5 to 2.0
        self.calibrated_bpm = 6.0  # breaths per minute

        # Session tracking
        self.session_start = 0
        self.session_duration = 0
        self.total_cycles = 0

        # Breathing state
        self.current_phase = 0  # 0=inhale, 1=hold, 2=exhale, 3=hold
        self.phase_start = 0
        self.cycle_count = 0

        # Animation
        self.arc_segments = 64
        self.arc_lut = self._generate_arc_lut()
        self.current_progress = 0.0

        # Calibration
        self.calibrating = False
        self.tap_times = []
        self.calibration_start = 0

        # Menu options
        self.menu_options = [
            "Start Session",
            "Calibrate Breath",
            "Pattern Settings",
            "View Stats",
            "Help"
        ]

        # Load saved data
        self.load_data()

    def init(self):
        """Initialize app when opened"""
        self.mode = "menu"
        self.selected_option = 0
        self.breathing_active = False
        self.paused = False
        self.screen_off = False
        self.draw_screen()

        if self.haptics:
            self.haptics.tap(0.3)

    def load_data(self):
        """Load saved breathing data"""
        try:
            with open("/stores/breath.json", "r") as f:
                data = json.load(f)
                self.current_pattern = data.get("last_preset", "resonant")
                self.calibrated_bpm = data.get("calibrated_bpm", 6.0)
                if "custom_pattern" in data:
                    self.patterns["custom"]["phases"] = data["custom_pattern"]
        except:
            # Create default data file
            self.save_data()

    def save_data(self):
        """Save breathing data"""
        try:
            data = {
                "last_preset": self.current_pattern,
                "calibrated_bpm": self.calibrated_bpm,
                "custom_pattern": self.patterns["custom"]["phases"],
                "sessions": []
            }

            # Add current session if completed
            if self.session_duration > 0:
                session = {
                    "ts": int(time.time()),
                    "preset": self.current_pattern,
                    "dur_s": self.session_duration,
                    "cycles": self.total_cycles
                }
                data["sessions"] = [session]

            with open("/stores/breath.json", "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Failed to save breath data: {e}")

    def _generate_arc_lut(self):
        """Generate lookup table for arc drawing"""
        lut = []
        center_x = self.display.width // 2
        center_y = self.display.height // 2
        radius = 80

        for i in range(self.arc_segments + 1):
            angle = (i / self.arc_segments) * 2 * math.pi - math.pi / 2  # Start at top
            x = center_x + int(radius * math.cos(angle))
            y = center_y + int(radius * math.sin(angle))
            lut.append((x, y))

        return lut

    def handle_input(self):
        """Handle user input"""
        if self.mode == "menu":
            return self.handle_menu_input()
        elif self.mode == "calibrate":
            return self.handle_calibrate_input()
        elif self.mode == "breathing":
            return self.handle_breathing_input()
        elif self.mode == "help":
            return self.handle_help_input()
        elif self.mode == "settings":
            return self.handle_settings_input()
        elif self.mode == "stats":
            return self.handle_stats_input()

        return "continue"

    def handle_menu_input(self):
        """Handle menu navigation"""
        # Navigate menu
        if self.joystick.up_pin.value() == 0:
            self.selected_option = (self.selected_option - 1) % len(self.menu_options)
            self.draw_screen()
            time.sleep_ms(150)
        elif self.joystick.down_pin.value() == 0:
            self.selected_option = (self.selected_option + 1) % len(self.menu_options)
            self.draw_screen()
            time.sleep_ms(150)

        # Select option
        elif self.buttons.is_pressed('A'):
            if self.selected_option == 0:  # Start Session
                self.start_breathing_session()
            elif self.selected_option == 1:  # Calibrate
                self.start_calibration()
            elif self.selected_option == 2:  # Pattern Settings
                self.mode = "settings"
                self.selected_option = 0
                self.draw_screen()
            elif self.selected_option == 3:  # View Stats
                self.mode = "stats"
                self.draw_screen()
            elif self.selected_option == 4:  # Help
                self.mode = "help"
                self.draw_screen()
            time.sleep_ms(200)

        # Back/Exit
        elif self.buttons.is_pressed('B'):
            return "exit"

        # Pattern switching with joystick L/R
        elif self.joystick.left_pin.value() == 0:
            patterns = list(self.patterns.keys())
            current_idx = patterns.index(self.current_pattern)
            self.current_pattern = patterns[(current_idx - 1) % len(patterns)]
            self.draw_screen()
            time.sleep_ms(200)
        elif self.joystick.right_pin.value() == 0:
            patterns = list(self.patterns.keys())
            current_idx = patterns.index(self.current_pattern)
            self.current_pattern = patterns[(current_idx + 1) % len(patterns)]
            self.draw_screen()
            time.sleep_ms(200)

        return "continue"

    def handle_calibrate_input(self):
        """Handle calibration input"""
        current_time = time.ticks_ms()

        # Tap detection
        if self.buttons.is_pressed('A'):
            if not self.calibrating:
                # Start calibration
                self.calibrating = True
                self.tap_times = [current_time]
                self.calibration_start = current_time
                self.draw_screen()
                if self.haptics:
                    self.haptics.tap(0.5)
            else:
                # Record tap
                self.tap_times.append(current_time)
                if self.haptics:
                    self.haptics.tap(0.3)

                # Check if calibration is complete (10-15 seconds)
                elapsed = time.ticks_diff(current_time, self.calibration_start)
                if elapsed > 10000 and len(self.tap_times) >= 5:  # At least 10 seconds and 5 taps
                    self.finish_calibration()

        # Cancel calibration
        elif self.buttons.is_pressed('B'):
            self.calibrating = False
            self.mode = "menu"
            self.draw_screen()
            time.sleep_ms(200)

        # Auto-finish after 15 seconds
        if self.calibrating:
            elapsed = time.ticks_diff(current_time, self.calibration_start)
            if elapsed > 15000 and len(self.tap_times) >= 3:
                self.finish_calibration()

        return "continue"

    def handle_breathing_input(self):
        """Handle breathing session input"""
        # Pause/Resume
        if self.buttons.is_pressed('X'):
            self.paused = not self.paused
            if not self.paused:
                # Reset phase timing when resuming
                self.phase_start = time.ticks_ms()
            if self.haptics:
                self.haptics.tap(0.4)
            time.sleep_ms(200)

        # Stop session
        elif self.buttons.is_pressed('B'):
            self.stop_breathing_session()
            return "continue"

        # Toggle screen off mode
        elif self.buttons.is_pressed('Y'):
            self.screen_off = not self.screen_off
            if self.screen_off:
                self.display.fill(Color.BLACK)
                self.display.text("Screen Off Mode", 50, self.display.height // 2, Color.DARK_GRAY)
                self.display.text("Y: Screen On", 60, self.display.height // 2 + 20, Color.DARK_GRAY)
                self.display.display()
            else:
                self.draw_screen()
            time.sleep_ms(200)

        # Intensity adjustment
        elif self.joystick.up_pin.value() == 0:
            self.intensity = min(2.0, self.intensity + 0.1)
            time.sleep_ms(100)
        elif self.joystick.down_pin.value() == 0:
            self.intensity = max(0.5, self.intensity - 0.1)
            time.sleep_ms(100)

        return "continue"

    def handle_help_input(self):
        """Handle help screen input"""
        if self.buttons.is_pressed('A') or self.buttons.is_pressed('B'):
            self.mode = "menu"
            self.draw_screen()
            time.sleep_ms(200)

        return "continue"

    def handle_settings_input(self):
        """Handle pattern settings input"""
        if self.buttons.is_pressed('B'):
            self.mode = "menu"
            self.draw_screen()
            time.sleep_ms(200)

        return "continue"

    def handle_stats_input(self):
        """Handle stats screen input"""
        if self.buttons.is_pressed('A') or self.buttons.is_pressed('B'):
            self.mode = "menu"
            self.draw_screen()
            time.sleep_ms(200)

        return "continue"

    def start_calibration(self):
        """Start breath calibration"""
        self.mode = "calibrate"
        self.calibrating = False
        self.tap_times = []
        self.draw_screen()

    def finish_calibration(self):
        """Process calibration results"""
        if len(self.tap_times) < 3:
            self.calibrating = False
            return

        # Calculate intervals between taps
        intervals = []
        for i in range(1, len(self.tap_times)):
            interval = time.ticks_diff(self.tap_times[i], self.tap_times[i-1])
            intervals.append(interval)

        # Robust mean (trim 20% outliers)
        intervals.sort()
        trim_count = max(1, len(intervals) // 5)
        trimmed = intervals[trim_count:-trim_count] if len(intervals) > 2 else intervals

        if trimmed:
            avg_interval_ms = sum(trimmed) / len(trimmed)
            # Convert to breaths per minute
            self.calibrated_bpm = 60000.0 / (avg_interval_ms * 2)  # Full breath cycle
            # Clamp to reasonable range
            self.calibrated_bpm = max(4.0, min(8.0, self.calibrated_bpm))

        self.calibrating = False
        self.save_data()

        # Show results briefly
        self.display.fill(Color.BLACK)
        self.display.text("Calibrated!", 70, 90, Color.GREEN)
        self.display.text(f"Rate: {self.calibrated_bpm:.1f} BPM", 50, 110, Color.WHITE)
        self.display.display()
        time.sleep(2)

        self.mode = "menu"
        self.draw_screen()

    def start_breathing_session(self):
        """Start a breathing session"""
        self.mode = "breathing"
        self.breathing_active = True
        self.paused = False
        self.screen_off = False
        self.current_phase = 0
        self.phase_start = time.ticks_ms()
        self.cycle_count = 0
        self.session_start = time.ticks_ms()

        if self.haptics:
            self.haptics.success()

        self.draw_screen()

    def stop_breathing_session(self):
        """Stop breathing session"""
        self.breathing_active = False
        self.session_duration = time.ticks_diff(time.ticks_ms(), self.session_start) // 1000
        self.total_cycles = self.cycle_count

        # Show Morti cheer
        self.show_completion()

        self.save_data()
        self.mode = "menu"
        self.draw_screen()

    def show_completion(self):
        """Show session completion with Morti cheer"""
        self.display.fill(Color.BLACK)

        # Morti celebration
        center_x = self.display.width // 2
        center_y = 80

        # Draw happy Morti
        self.display.fill_rect(center_x - 15, center_y - 15, 30, 30, Color.GREEN)
        self.display.fill_rect(center_x - 8, center_y - 8, 3, 3, Color.WHITE)  # Eyes
        self.display.fill_rect(center_x + 5, center_y - 8, 3, 3, Color.WHITE)
        self.display.line(center_x - 6, center_y + 5, center_x + 6, center_y + 5, Color.WHITE)  # Smile

        # Celebration particles
        for i in range(8):
            angle = i * 45
            px = center_x + int(25 * math.cos(math.radians(angle)))
            py = center_y + int(25 * math.sin(math.radians(angle)))
            self.display.pixel(px, py, Color.YELLOW)

        # Stats
        self.display.text("Well Done!", 75, 130, Color.GREEN)
        self.display.text(f"Cycles: {self.cycle_count}", 80, 150, Color.WHITE)
        self.display.text(f"Time: {self.session_duration}s", 80, 170, Color.WHITE)

        if self.haptics:
            self.haptics.celebrate()

        self.display.display()
        time.sleep(2)

    def update_breathing_cycle(self):
        """Update breathing animation and haptics"""
        if not self.breathing_active or self.paused:
            return

        current_time = time.ticks_ms()
        pattern = self.patterns[self.current_pattern]

        # Get current phase duration (scaled by intensity and calibration)
        base_duration = pattern["phases"][self.current_phase]
        if base_duration == 0:
            # Skip zero-duration phases
            self.advance_phase()
            return

        # Scale duration based on calibrated BPM
        duration_scale = 6.0 / self.calibrated_bpm  # 6 BPM is baseline
        scaled_duration = base_duration * duration_scale / self.intensity
        phase_duration_ms = int(scaled_duration * 1000)

        # Check if phase is complete
        elapsed = time.ticks_diff(current_time, self.phase_start)
        if elapsed >= phase_duration_ms:
            self.advance_phase()
            return

        # Calculate progress within current phase
        progress = elapsed / phase_duration_ms
        self.current_progress = progress

        # Haptic feedback based on phase
        if self.current_phase == 0:  # Inhale
            # Gentle pulse ramping up
            if elapsed % 500 < 50:  # Every 500ms
                intensity = 0.3 + (progress * 0.3 * self.intensity)
                if self.haptics:
                    self.haptics.pulse(30, intensity)
        elif self.current_phase == 2:  # Exhale
            # Gentle pulse ramping down
            if elapsed % 600 < 50:  # Every 600ms
                intensity = 0.6 - (progress * 0.4 * self.intensity)
                if self.haptics:
                    self.haptics.pulse(40, intensity)

    def advance_phase(self):
        """Move to next breathing phase"""
        self.current_phase = (self.current_phase + 1) % 4
        self.phase_start = time.ticks_ms()

        # Complete cycle when returning to inhale
        if self.current_phase == 0:
            self.cycle_count += 1

        # Phase transition haptic
        if self.haptics:
            if self.current_phase == 0:  # Start inhale
                self.haptics.tap(0.4)
            elif self.current_phase == 2:  # Start exhale
                self.haptics.tap(0.3)

    def draw_screen(self):
        """Draw current screen"""
        self.display.fill(Color.BLACK)

        if self.mode == "menu":
            self.draw_menu()
        elif self.mode == "calibrate":
            self.draw_calibration()
        elif self.mode == "breathing" and not self.screen_off:
            self.draw_breathing()
        elif self.mode == "help":
            self.draw_help()
        elif self.mode == "settings":
            self.draw_settings()
        elif self.mode == "stats":
            self.draw_stats()

        self.display.display()

    def draw_menu(self):
        """Draw main menu"""
        # Title
        self.display.text("BREATH", 85, 10, Color.CYAN)

        # Current pattern
        pattern = self.patterns[self.current_pattern]
        self.display.text(pattern["name"], 60, 30, Color.YELLOW)

        # Menu options
        y_start = 60
        for i, option in enumerate(self.menu_options):
            y = y_start + i * 20
            color = Color.WHITE if i == self.selected_option else Color.GRAY

            if i == self.selected_option:
                self.display.text(">", 40, y, Color.WHITE)

            self.display.text(option, 55, y, color)

        # Instructions
        self.display.text("L/R:Pattern A:Select", 30, 200, Color.DARK_GRAY)
        self.display.text(f"Rate: {self.calibrated_bpm:.1f} BPM", 70, 220, Color.DARK_GRAY)

    def draw_calibration(self):
        """Draw calibration screen"""
        self.display.text("CALIBRATE BREATH", 50, 20, Color.CYAN)

        if not self.calibrating:
            self.display.text("Tap A to your", 70, 60, Color.WHITE)
            self.display.text("natural slow", 75, 80, Color.WHITE)
            self.display.text("breathing rhythm", 60, 100, Color.WHITE)
            self.display.text("for 10-15 seconds", 55, 120, Color.WHITE)

            self.display.text("A:Start B:Back", 75, 180, Color.GRAY)
        else:
            elapsed = time.ticks_diff(time.ticks_ms(), self.calibration_start)
            seconds = elapsed // 1000

            self.display.text("Keep tapping A", 70, 60, Color.GREEN)
            self.display.text("to your breath...", 65, 80, Color.GREEN)

            self.display.text(f"Time: {seconds}s", 85, 110, Color.WHITE)
            self.display.text(f"Taps: {len(self.tap_times)}", 85, 130, Color.WHITE)

            # Progress bar
            progress = min(1.0, elapsed / 15000)
            bar_width = int(160 * progress)
            self.display.rect(40, 160, 160, 8, Color.GRAY)
            if bar_width > 0:
                self.display.fill_rect(40, 160, bar_width, 8, Color.GREEN)

            self.display.text("B:Cancel", 85, 190, Color.GRAY)

    def draw_breathing(self):
        """Draw breathing session"""
        pattern = self.patterns[self.current_pattern]

        # Title and pattern
        self.display.text("BREATHE", 80, 10, Color.CYAN)
        self.display.text(pattern["name"], 70, 25, Color.YELLOW)

        # Phase indicator
        phase_names = ["INHALE", "HOLD", "EXHALE", "HOLD"]
        phase_colors = [Color.GREEN, Color.BLUE, Color.ORANGE, Color.PURPLE]

        current_phase_name = phase_names[self.current_phase]
        current_phase_color = phase_colors[self.current_phase]

        # Center the phase text
        text_x = (self.display.width - len(current_phase_name) * 8) // 2
        self.display.text(current_phase_name, text_x, 50, current_phase_color)

        # Draw breathing arc
        self.draw_breathing_arc()

        # Cycle counter
        self.display.text(f"Cycle: {self.cycle_count}", 10, 200, Color.WHITE)

        # Session time
        if self.breathing_active and not self.paused:
            session_time = time.ticks_diff(time.ticks_ms(), self.session_start) // 1000
        else:
            session_time = self.session_duration

        self.display.text(f"Time: {session_time}s", 10, 215, Color.WHITE)

        # Controls
        controls = "X:Pause B:Stop Y:Screen"
        self.display.text(controls, 120, 205, Color.DARK_GRAY)

        # Intensity indicator
        intensity_bars = int(self.intensity * 5)
        for i in range(5):
            color = Color.GREEN if i < intensity_bars else Color.DARK_GRAY
            self.display.fill_rect(200 + i * 8, 215, 6, 10, color)

        # Pause indicator
        if self.paused:
            self.display.text("PAUSED", 85, 170, Color.RED)

    def draw_breathing_arc(self):
        """Draw animated breathing arc"""
        center_x = self.display.width // 2
        center_y = self.display.height // 2 + 10

        # Calculate arc progress
        total_progress = (self.current_phase + self.current_progress) / 4
        arc_end = int(total_progress * self.arc_segments)

        # Draw completed arc
        for i in range(arc_end):
            if i < len(self.arc_lut) - 1:
                x1, y1 = self.arc_lut[i]
                x2, y2 = self.arc_lut[i + 1]

                # Color based on phase
                if self.current_phase == 0:  # Inhale
                    color = Color.GREEN
                elif self.current_phase == 1:  # Hold in
                    color = Color.BLUE
                elif self.current_phase == 2:  # Exhale
                    color = Color.ORANGE
                else:  # Hold out
                    color = Color.PURPLE

                self.display.line(x1, y1, x2, y2, color)

        # Draw current position marker
        if arc_end < len(self.arc_lut):
            x, y = self.arc_lut[arc_end]
            self.display.fill_rect(x - 2, y - 2, 4, 4, Color.WHITE)

        # Draw center dot that pulses
        pulse_size = 3 + int(self.current_progress * 3)
        self.display.fill_rect(center_x - pulse_size, center_y - pulse_size,
                              pulse_size * 2, pulse_size * 2, Color.WHITE)

    def draw_help(self):
        """Draw help screen"""
        self.display.text("BREATH HELP", 65, 10, Color.CYAN)

        help_text = [
            "Patterns:",
            "Box: Equal 4-4-4-4",
            "4-7-8: Sleep aid",
            "Resonant: Heart sync",
            "",
            "Controls:",
            "A: Select/Next",
            "B: Back/Stop",
            "X: Pause/Resume",
            "Y: Help/Screen off",
            "",
            "L/R: Switch pattern",
            "U/D: Intensity"
        ]

        y = 35
        for line in help_text:
            if line:
                self.display.text(line, 15, y, Color.WHITE)
            y += 15

        self.display.text("A/B:Back", 85, 220, Color.GRAY)

    def draw_settings(self):
        """Draw pattern settings"""
        self.display.text("SETTINGS", 80, 10, Color.CYAN)

        pattern = self.patterns[self.current_pattern]
        self.display.text(f"Pattern: {pattern['name']}", 15, 40, Color.WHITE)
        self.display.text(pattern["description"], 15, 60, Color.GRAY)

        # Show timing
        phases = pattern["phases"]
        self.display.text("Timing:", 15, 90, Color.WHITE)
        self.display.text(f"In: {phases[0]}s", 15, 110, Color.GREEN)
        self.display.text(f"Hold: {phases[1]}s", 15, 130, Color.BLUE)
        self.display.text(f"Out: {phases[2]}s", 15, 150, Color.ORANGE)
        self.display.text(f"Hold: {phases[3]}s", 15, 170, Color.PURPLE)

        self.display.text("B:Back", 90, 220, Color.GRAY)

    def draw_stats(self):
        """Draw session statistics"""
        self.display.text("STATISTICS", 75, 10, Color.CYAN)

        # Load recent sessions
        try:
            with open("/stores/breath.json", "r") as f:
                data = json.load(f)
                sessions = data.get("sessions", [])
        except:
            sessions = []

        if sessions:
            recent = sessions[-1]
            self.display.text("Last Session:", 15, 40, Color.WHITE)
            self.display.text(f"Pattern: {recent.get('preset', 'Unknown')}", 15, 60, Color.GRAY)
            self.display.text(f"Duration: {recent.get('dur_s', 0)}s", 15, 80, Color.GRAY)
            self.display.text(f"Cycles: {recent.get('cycles', 0)}", 15, 100, Color.GRAY)
        else:
            self.display.text("No sessions yet", 70, 80, Color.GRAY)
            self.display.text("Start breathing", 65, 100, Color.GRAY)
            self.display.text("to track stats!", 70, 120, Color.GRAY)

        # Current settings
        self.display.text(f"Calibrated: {self.calibrated_bpm:.1f} BPM", 15, 160, Color.WHITE)
        self.display.text(f"Intensity: {self.intensity:.1f}x", 15, 180, Color.WHITE)

        self.display.text("A/B:Back", 85, 220, Color.GRAY)

    def update(self):
        """Update app state"""
        if self.mode == "breathing" and self.breathing_active:
            self.update_breathing_cycle()
            if not self.screen_off:
                self.draw_screen()

        # Handle input
        result = self.handle_input()

        return result != "exit"

    def cleanup(self):
        """Clean up when app exits"""
        if self.breathing_active:
            self.stop_breathing_session()

        if self.haptics:
            self.haptics.cleanup()