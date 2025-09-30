"""
Scars & Stars - Relationship Compass
A gentle, private way to log interactions, process feelings, and heal
Turning tough moments (scars) and bright ones (stars) into constellation growth
"""

import time
import json
import math
import random
from lib.st7789 import Color

class ScarsStars:
    def __init__(self, display, joystick, buttons):
        """Initialize Scars & Stars app"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons

        # App state
        self.current_mode = "home"  # home, quick_log, deep_log, repair, constellation, values
        self.selected_index = 0
        self.log_step = 0
        self.current_log = {}
        self.stealth_mode = False
        self.pulse_active = False
        self.last_pulse = 0

        # UI state
        self.animation_frame = 0
        self.constellation_cursor = {"x": 120, "y": 120}

        # Data
        self.people = []
        self.entries = []
        self.values = ["Kindness", "Clarity", "Courage"]
        self.repair_queue = []

        # Load data
        self.load_data()

        # Tags for quick selection
        self.interaction_tags = [
            "heard", "ignored", "interrupted", "supported",
            "criticized", "connected", "misunderstood", "welcomed"
        ]

        # Emotions and needs for deep log
        self.emotions = ["anger", "sadness", "fear", "joy", "shame", "love"]
        self.needs = ["to be heard", "space", "clarity", "repair", "understanding", "validation"]

        # Repair types
        self.repair_types = [
            {"name": "Apology", "icon": "♡", "color": Color.GREEN},
            {"name": "Boundary", "icon": "◇", "color": Color.BLUE},
            {"name": "Self-soothe", "icon": "◉", "color": Color.PURPLE},
            {"name": "Release", "icon": "~", "color": Color.GRAY}
        ]

    def load_data(self):
        """Load all data from storage"""
        # Load people
        try:
            with open('/stores/people.json', 'r') as f:
                self.people = json.load(f)
        except:
            self.people = [{"id": "anon", "name": "Someone", "glyph": "?"}]

        # Load entries and values
        try:
            with open('/stores/scars_stars.json', 'r') as f:
                data = json.load(f)
                self.values = data.get("values", ["Kindness", "Clarity", "Courage"])
                self.entries = data.get("entries", [])
        except:
            self.entries = []

        # Load repair queue
        try:
            with open('/stores/repair_queue.json', 'r') as f:
                self.repair_queue = json.load(f)
        except:
            self.repair_queue = []

    def save_data(self):
        """Save all data to storage"""
        # Save people
        try:
            with open('/stores/people.json', 'w') as f:
                json.dump(self.people, f)
        except:
            pass

        # Save entries and values
        try:
            data = {"values": self.values, "entries": self.entries}
            with open('/stores/scars_stars.json', 'w') as f:
                json.dump(data, f)
        except:
            pass

        # Save repair queue
        try:
            with open('/stores/repair_queue.json', 'w') as f:
                json.dump(self.repair_queue, f)
        except:
            pass

    def start_quick_log(self):
        """Start quick log flow"""
        self.current_mode = "quick_log"
        self.log_step = 0
        self.selected_index = 0
        self.current_log = {
            "ts": int(time.time()),
            "pid": None,
            "valence": 0,
            "tag": None,
            "type": "quick"
        }

    def start_deep_log(self):
        """Start deep log flow"""
        self.current_mode = "deep_log"
        self.log_step = 0
        self.selected_index = 0
        self.current_log = {
            "ts": int(time.time()),
            "pid": None,
            "valence": 0,
            "tag": None,
            "feel": None,
            "need": None,
            "note": "",
            "type": "deep"
        }

    def complete_log(self):
        """Complete and save current log entry"""
        # Generate unique ID
        entry_id = f"e{len(self.entries) + 1}"
        self.current_log["id"] = entry_id

        # Add to entries
        self.entries.append(self.current_log.copy())

        # Save data
        self.save_data()

        # Show completion feedback
        self.show_log_completion()

        # Return to home
        self.current_mode = "home"
        self.selected_index = 0

    def show_log_completion(self):
        """Show Morti feedback for completed log"""
        self.display.fill(Color.BLACK)

        if self.current_log["valence"] > 0:
            # Star - positive interaction
            self.display.text("⭐ STAR LOGGED ⭐", 60, 80, Color.YELLOW)
            self.display.text("Morti: ◕‿◕", 80, 100, Color.GREEN)
            self.display.text("Brightness added!", 70, 120, Color.WHITE)
        else:
            # Scar - challenging interaction
            self.display.text("✚ SCAR LOGGED ✚", 60, 80, Color.GRAY)
            self.display.text("Morti: ◕◡◕", 80, 100, Color.BLUE)
            self.display.text("Growth begins here", 60, 120, Color.WHITE)

        self.display.text("A:Continue", 80, 200, Color.GRAY)
        self.display.display()

        # Wait for input
        while True:
            self.buttons.update()
            if self.buttons.is_pressed('A'):
                break
            time.sleep_ms(50)

    def draw_home_screen(self):
        """Draw main home screen"""
        self.display.fill(Color.BLACK)

        # Title
        if self.stealth_mode:
            self.display.text("S▫︎A▫S", 95, 5, Color.GRAY)
        else:
            self.display.text("SCARS & STARS", 65, 5, Color.CYAN)

        # Quick stats
        star_count = len([e for e in self.entries if e["valence"] > 0])
        scar_count = len([e for e in self.entries if e["valence"] <= 0])
        unresolved = len([r for r in self.repair_queue if r["status"] != "completed"])

        stats_text = f"⭐{star_count} ✚{scar_count}"
        if unresolved > 0 and not self.stealth_mode:
            stats_text += f" ⚠{unresolved}"
        self.display.text(stats_text, 10, 25, Color.GRAY)

        # Menu options
        menu_items = [
            "Quick Log (30s)",
            "Deep Log (2min)",
            "Repair Ritual",
            "Constellation",
            "Values & Anchors"
        ]

        if self.stealth_mode:
            menu_items = ["Log", "Deep", "Repair", "View", "Values"]

        y_start = 50
        for i, item in enumerate(menu_items):
            y = y_start + i * 25

            if i == self.selected_index:
                self.display.fill_rect(5, y - 5, 230, 20, Color.WHITE)
                text_color = Color.BLACK
            else:
                text_color = Color.WHITE

            self.display.text(item, 10, y, text_color)

        # Values reminder
        if not self.stealth_mode:
            values_text = " • ".join(self.values)
            if len(values_text) * 8 > 220:
                values_text = values_text[:25] + "..."
            self.display.text(values_text, 10, 190, Color.PURPLE)

        # Controls
        controls = "↑↓:Select A:Enter B:Stealth" if not self.stealth_mode else "↑↓ A:Go B:Exit"
        self.display.text(controls, 20, 220, Color.GRAY)

    def draw_quick_log_screen(self):
        """Draw quick log interaction screen"""
        self.display.fill(Color.BLACK)

        # Title with step indicator
        step_dots = "●" * (self.log_step + 1) + "○" * (2 - self.log_step)
        self.display.text(f"QUICK LOG {step_dots}", 60, 5, Color.CYAN)

        if self.log_step == 0:
            # Step 1: Who?
            self.display.text("Who was it?", 10, 30, Color.WHITE)

            y_start = 55
            for i, person in enumerate(self.people):
                y = y_start + i * 20
                if y > 180:  # Prevent overflow
                    break

                if i == self.selected_index:
                    self.display.fill_rect(5, y - 3, 230, 16, Color.WHITE)
                    text_color = Color.BLACK
                else:
                    text_color = Color.WHITE

                name = person["glyph"] if self.stealth_mode else person["name"]
                self.display.text(name, 10, y, text_color)

        elif self.log_step == 1:
            # Step 2: Vibe & intensity
            self.display.text("How was it?", 10, 30, Color.WHITE)

            # Vibe selection
            vibes = [("⭐ Star (positive)", 1), ("✚ Scar (challenging)", -1)]

            for i, (vibe_text, vibe_val) in enumerate(vibes):
                y = 55 + i * 25
                if i == (0 if self.selected_index >= 0 else 1):
                    self.display.fill_rect(5, y - 3, 230, 20, Color.WHITE)
                    text_color = Color.BLACK
                else:
                    text_color = Color.WHITE
                self.display.text(vibe_text, 10, y, text_color)

            # Intensity meter (-3 to +3)
            self.display.text("Intensity:", 10, 120, Color.WHITE)
            self.draw_intensity_meter(10, 140, self.current_log.get("valence", 0))

        elif self.log_step == 2:
            # Step 3: Tag
            self.display.text("What happened?", 10, 30, Color.WHITE)

            # Tags in 2x4 grid
            rows = 4
            cols = 2
            start_x = 10
            start_y = 55

            for i, tag in enumerate(self.interaction_tags):
                if i >= 8:  # Show only first 8 tags
                    break

                row = i // cols
                col = i % cols
                x = start_x + col * 110
                y = start_y + row * 25

                if i == self.selected_index:
                    self.display.fill_rect(x - 3, y - 3, 105, 20, Color.WHITE)
                    text_color = Color.BLACK
                else:
                    text_color = Color.WHITE

                self.display.text(tag, x, y, text_color)

        # Navigation instructions
        if self.log_step < 2:
            self.display.text("↑↓:Select A:Next B:Back", 30, 220, Color.GRAY)
        else:
            self.display.text("A:Save B:Back", 70, 220, Color.GRAY)

    def draw_intensity_meter(self, x, y, value):
        """Draw 7-dot intensity meter from -3 to +3"""
        dot_size = 8
        spacing = 20

        for i in range(7):
            dot_x = x + i * spacing
            intensity_val = i - 3  # Convert 0-6 to -3 to +3

            if intensity_val == value:
                # Selected dot - filled
                color = Color.RED if value < 0 else Color.YELLOW if value == 0 else Color.GREEN
                self.display.fill_rect(dot_x, y, dot_size, dot_size, color)
            else:
                # Unselected dot - outline
                color = Color.GRAY
                self.display.rect(dot_x, y, dot_size, dot_size, color)

        # Labels
        self.display.text("-3", x - 5, y + 15, Color.GRAY)
        self.display.text("0", x + 3 * spacing - 2, y + 15, Color.GRAY)
        self.display.text("+3", x + 6 * spacing - 5, y + 15, Color.GRAY)

    def draw_deep_log_screen(self):
        """Draw deep log screen with emotions and needs"""
        self.display.fill(Color.BLACK)

        # Title with step indicator (5 steps for deep log)
        step_dots = "●" * (self.log_step + 1) + "○" * (4 - self.log_step)
        self.display.text(f"DEEP LOG {step_dots}", 65, 5, Color.CYAN)

        if self.log_step == 0:
            # Step 1: Who? (same as quick log)
            self.display.text("Who was it?", 10, 30, Color.WHITE)

            y_start = 55
            for i, person in enumerate(self.people):
                y = y_start + i * 20
                if y > 180:
                    break

                if i == self.selected_index:
                    self.display.fill_rect(5, y - 3, 230, 16, Color.WHITE)
                    text_color = Color.BLACK
                else:
                    text_color = Color.WHITE

                name = person["glyph"] if self.stealth_mode else person["name"]
                self.display.text(name, 10, y, text_color)

        elif self.log_step == 1:
            # Step 2: Vibe & intensity (same as quick log)
            self.display.text("How was it?", 10, 30, Color.WHITE)

            vibes = [("⭐ Star (positive)", 1), ("✚ Scar (challenging)", -1)]

            for i, (vibe_text, vibe_val) in enumerate(vibes):
                y = 55 + i * 25
                if i == (0 if self.selected_index >= 0 else 1):
                    self.display.fill_rect(5, y - 3, 230, 20, Color.WHITE)
                    text_color = Color.BLACK
                else:
                    text_color = Color.WHITE
                self.display.text(vibe_text, 10, y, text_color)

            self.display.text("Intensity:", 10, 120, Color.WHITE)
            self.draw_intensity_meter(10, 140, self.current_log.get("valence", 0))

        elif self.log_step == 2:
            # Step 3: What I felt (emotions)
            self.display.text("What did you feel?", 10, 30, Color.WHITE)

            rows = 3
            cols = 2
            start_x = 10
            start_y = 55

            for i, emotion in enumerate(self.emotions):
                if i >= 6:
                    break

                row = i // cols
                col = i % cols
                x = start_x + col * 110
                y = start_y + row * 25

                if i == self.selected_index:
                    self.display.fill_rect(x - 3, y - 3, 105, 20, Color.WHITE)
                    text_color = Color.BLACK
                else:
                    text_color = Color.WHITE

                self.display.text(emotion, x, y, text_color)

        elif self.log_step == 3:
            # Step 4: What I needed
            self.display.text("What did you need?", 10, 30, Color.WHITE)

            for i, need in enumerate(self.needs):
                y = 55 + i * 20
                if y > 180:
                    break

                if i == self.selected_index:
                    self.display.fill_rect(5, y - 3, 230, 16, Color.WHITE)
                    text_color = Color.BLACK
                else:
                    text_color = Color.WHITE

                self.display.text(need, 10, y, text_color)

        elif self.log_step == 4:
            # Step 5: One line note (simplified for now)
            self.display.text("Quick note:", 10, 30, Color.WHITE)
            note_options = [
                "felt overwhelmed",
                "they really got it",
                "miscommunication",
                "felt supported",
                "boundary crossed",
                "great connection"
            ]

            for i, note in enumerate(note_options):
                y = 55 + i * 20
                if y > 180:
                    break

                if i == self.selected_index:
                    self.display.fill_rect(5, y - 3, 230, 16, Color.WHITE)
                    text_color = Color.BLACK
                else:
                    text_color = Color.WHITE

                self.display.text(note, 10, y, text_color)

        # Navigation instructions
        if self.log_step < 4:
            self.display.text("↑↓:Select A:Next B:Back", 30, 220, Color.GRAY)
        else:
            self.display.text("A:Save B:Back", 70, 220, Color.GRAY)

    def draw_repair_ritual_screen(self):
        """Draw repair ritual selection screen"""
        self.display.fill(Color.BLACK)

        # Title
        self.display.text("REPAIR RITUAL", 65, 5, Color.CYAN)

        # Show unresolved scars count
        unresolved_scars = [e for e in self.entries if e["valence"] < 0 and self.calculate_healing_score(e) > 0]
        self.display.text(f"Scars needing care: {len(unresolved_scars)}", 10, 25, Color.GRAY)

        if len(unresolved_scars) == 0:
            self.display.text("No active scars!", 60, 80, Color.GREEN)
            self.display.text("All relationships", 65, 100, Color.GREEN)
            self.display.text("are in harmony ◕‿◕", 55, 120, Color.GREEN)
            self.display.text("B:Back", 100, 200, Color.GRAY)
            return

        # Select repair type
        self.display.text("Choose repair path:", 10, 50, Color.WHITE)

        for i, repair_type in enumerate(self.repair_types):
            y = 75 + i * 25

            if i == self.selected_index:
                self.display.fill_rect(5, y - 3, 230, 20, Color.WHITE)
                text_color = Color.BLACK
            else:
                text_color = repair_type["color"]

            text = f"{repair_type['icon']} {repair_type['name']}"
            self.display.text(text, 10, y, text_color)

        self.display.text("A:Select B:Back", 70, 220, Color.GRAY)

    def start_repair_ritual(self, repair_type):
        """Start repair ritual flow"""
        # Find most recent unresolved scar
        unresolved_scars = [e for e in self.entries if e["valence"] < 0 and self.calculate_healing_score(e) > 0]
        if not unresolved_scars:
            return

        # Sort by timestamp, get most recent
        recent_scar = sorted(unresolved_scars, key=lambda x: x["ts"], reverse=True)[0]

        # Create repair action
        repair_action = {
            "eid": recent_scar["id"],
            "type": repair_type["name"].lower(),
            "status": "planned",
            "due": int(time.time()) + 3600,  # 1 hour from now
            "steps": self.get_repair_steps(repair_type["name"].lower(), recent_scar)
        }

        self.repair_queue.append(repair_action)
        self.save_data()

        # Show repair guidance
        self.show_repair_guidance(repair_action, recent_scar)

    def get_repair_steps(self, repair_type, scar_entry):
        """Get concrete repair steps based on type"""
        person_name = "them" if self.stealth_mode else self.get_person_name(scar_entry["pid"])

        if repair_type == "apology":
            return [
                f"Text {person_name}: 'I acted badly earlier. I'm sorry.'",
                "Take a deep breath before sending",
                "Wait for their response without defending"
            ]
        elif repair_type == "boundary":
            return [
                f"Plan what to say to {person_name} about your needs",
                "Choose a calm moment to speak",
                "Use 'I feel...' statements"
            ]
        elif repair_type == "self-soothe":
            return [
                "Take 5 deep breaths",
                "Remember: their reaction isn't about you",
                "Do something kind for yourself"
            ]
        elif repair_type == "release":
            return [
                "Write down what happened",
                "Acknowledge your feelings",
                "Choose to let go of control"
            ]

    def get_person_name(self, person_id):
        """Get person name by ID"""
        for person in self.people:
            if person["id"] == person_id:
                return person["name"]
        return "Someone"

    def show_repair_guidance(self, repair_action, scar_entry):
        """Show repair guidance screen"""
        self.display.fill(Color.BLACK)

        self.display.text("REPAIR RITUAL", 65, 5, Color.GREEN)

        person_name = self.get_person_name(scar_entry["pid"])
        if not self.stealth_mode:
            self.display.text(f"For: {person_name}", 10, 25, Color.WHITE)

        self.display.text("Your steps:", 10, 45, Color.CYAN)

        y = 65
        for i, step in enumerate(repair_action["steps"]):
            step_text = f"{i+1}. {step}"
            # Word wrap for long steps
            if len(step_text) > 28:
                step_text = step_text[:25] + "..."
            self.display.text(step_text, 10, y, Color.WHITE)
            y += 15

        self.display.text("Start when ready", 60, 190, Color.YELLOW)
        self.display.text("A:Understood", 75, 220, Color.GRAY)

        self.display.display()

        # Wait for acknowledgment
        while True:
            self.buttons.update()
            if self.buttons.is_pressed('A'):
                break
            time.sleep_ms(50)

        # Return to home
        self.current_mode = "home"
        self.selected_index = 0

    def draw_values_screen(self):
        """Draw values and anchors screen"""
        self.display.fill(Color.BLACK)

        self.display.text("VALUES & ANCHORS", 55, 5, Color.PURPLE)

        self.display.text("Your values:", 10, 30, Color.WHITE)
        for i, value in enumerate(self.values):
            y = 50 + i * 20
            self.display.text(f"• {value}", 15, y, Color.PURPLE)

        # Show most recent anchor
        if self.entries:
            recent_entry = self.entries[-1]
            self.display.text("Recent anchor:", 10, 130, Color.WHITE)

            # Simple alignment check
            anchor_text = f"Choose {self.values[0]}: breathe once, speak once"
            if len(anchor_text) > 28:
                anchor_text = anchor_text[:25] + "..."
            self.display.text(anchor_text, 10, 150, Color.YELLOW)

        self.display.text("B:Back", 100, 220, Color.GRAY)

    def draw_constellation_screen(self):
        """Draw constellation view with stars and scars"""
        self.display.fill(Color.BLACK)

        # Title
        self.display.text("CONSTELLATION", 70, 5, Color.CYAN)

        # Constellation area (160x160 centered)
        const_x = 40
        const_y = 40
        const_size = 160

        # Border
        self.display.rect(const_x, const_y, const_size, const_size, Color.GRAY)

        # Draw entries as constellation
        for i, entry in enumerate(self.entries):
            # Generate stable position based on person ID and timestamp
            pos = self.generate_constellation_position(entry, const_x, const_y, const_size)

            if entry["valence"] > 0:
                # Star
                self.draw_star(pos["x"], pos["y"], Color.YELLOW)
            else:
                # Scar/stitch
                healing_score = self.calculate_healing_score(entry)
                stitch_color = self.get_healing_color(healing_score)
                self.draw_stitch(pos["x"], pos["y"], stitch_color)

        # Cursor
        cursor_x = max(const_x, min(const_x + const_size - 5, self.constellation_cursor["x"]))
        cursor_y = max(const_y, min(const_y + const_size - 5, self.constellation_cursor["y"]))
        self.display.rect(cursor_x, cursor_y, 5, 5, Color.WHITE)

        # Stats
        self.display.text(f"Entries: {len(self.entries)}", 10, 210, Color.GRAY)
        self.display.text("Move:Joystick A:Details", 50, 225, Color.GRAY)

    def generate_constellation_position(self, entry, base_x, base_y, size):
        """Generate stable position for entry using deterministic spiral"""
        # Seed based on person ID and timestamp for stability
        seed_val = hash(entry["pid"] + str(entry["ts"])) % 10000
        random.seed(seed_val)

        # Spiral parameters
        angle = (seed_val % 360) * (math.pi / 180)
        radius = (seed_val % 70) + 10  # 10-80 pixel radius from center

        center_x = base_x + size // 2
        center_y = base_y + size // 2

        x = center_x + int(radius * math.cos(angle))
        y = center_y + int(radius * math.sin(angle))

        # Clamp to bounds
        x = max(base_x + 2, min(base_x + size - 2, x))
        y = max(base_y + 2, min(base_y + size - 2, y))

        return {"x": x, "y": y}

    def draw_star(self, x, y, color):
        """Draw a simple star"""
        # Simple 5-pixel cross star
        self.display.pixel(x, y, color)
        self.display.pixel(x-1, y, color)
        self.display.pixel(x+1, y, color)
        self.display.pixel(x, y-1, color)
        self.display.pixel(x, y+1, color)

    def draw_stitch(self, x, y, color):
        """Draw a stitch mark for scars"""
        # Simple line with knots on ends
        self.display.line(x-3, y, x+3, y, color)
        self.display.pixel(x-3, y, Color.WHITE)  # Left knot
        self.display.pixel(x+3, y, Color.WHITE)  # Right knot

    def calculate_healing_score(self, entry):
        """Calculate healing score for scar entry"""
        if entry["valence"] > 0:
            return 0  # Stars don't need healing

        base_score = abs(entry["valence"])

        # Reduce by completed repair actions
        completed_repairs = len([r for r in self.repair_queue
                               if r.get("eid") == entry["id"] and r["status"] == "completed"])

        # Time decay (weekly -0.25)
        weeks_passed = (time.time() - entry["ts"]) / (7 * 24 * 3600)
        time_decay = weeks_passed * 0.25

        healing_score = base_score - completed_repairs - time_decay
        return max(0, healing_score)

    def get_healing_color(self, score):
        """Get color based on healing score"""
        if score <= 0:
            return Color.GREEN  # Fully healed
        elif score <= 1:
            return Color.YELLOW  # Mostly healed
        elif score <= 2:
            return Color.ORANGE  # Healing
        else:
            return Color.RED  # Fresh scar

    def update_stealth_pulse(self):
        """Update stealth mode haptic pulse"""
        if self.pulse_active and time.ticks_ms() - self.last_pulse > 2000:  # 2 second pulse
            # Trigger haptic pulse (would connect to haptics system)
            self.last_pulse = time.ticks_ms()

    def draw_screen(self):
        """Draw current screen"""
        if self.current_mode == "home":
            self.draw_home_screen()
        elif self.current_mode == "quick_log":
            self.draw_quick_log_screen()
        elif self.current_mode == "deep_log":
            self.draw_deep_log_screen()
        elif self.current_mode == "repair":
            self.draw_repair_ritual_screen()
        elif self.current_mode == "constellation":
            self.draw_constellation_screen()
        elif self.current_mode == "values":
            self.draw_values_screen()

        self.display.display()

    def init(self):
        """Initialize app"""
        self.draw_screen()

    def update(self):
        """Update Scars & Stars app"""
        self.buttons.update()

        # Update stealth pulse
        self.update_stealth_pulse()

        if self.current_mode == "home":
            # Home navigation
            if self.buttons.is_pressed('UP'):
                self.selected_index = (self.selected_index - 1) % 5
                self.draw_screen()
                time.sleep_ms(150)

            elif self.buttons.is_pressed('DOWN'):
                self.selected_index = (self.selected_index + 1) % 5
                self.draw_screen()
                time.sleep_ms(150)

            elif self.buttons.is_pressed('A'):
                if self.selected_index == 0:
                    self.start_quick_log()
                elif self.selected_index == 1:
                    self.start_deep_log()
                elif self.selected_index == 2:
                    self.current_mode = "repair"
                    self.selected_index = 0
                elif self.selected_index == 3:
                    self.current_mode = "constellation"
                    self.selected_index = 0
                elif self.selected_index == 4:
                    self.current_mode = "values"
                    self.selected_index = 0
                self.draw_screen()
                time.sleep_ms(200)

            elif self.buttons.is_pressed('B'):
                # Toggle stealth mode
                self.stealth_mode = not self.stealth_mode
                if self.stealth_mode:
                    self.pulse_active = True
                    self.last_pulse = time.ticks_ms()
                else:
                    self.pulse_active = False
                self.draw_screen()
                time.sleep_ms(200)

        elif self.current_mode == "quick_log":
            self.handle_quick_log_input()

        elif self.current_mode == "deep_log":
            self.handle_deep_log_input()

        elif self.current_mode == "repair":
            self.handle_repair_input()

        elif self.current_mode == "values":
            if self.buttons.is_pressed('B'):
                self.current_mode = "home"
                self.selected_index = 0
                self.draw_screen()
                time.sleep_ms(200)

        elif self.current_mode == "constellation":
            if self.buttons.is_pressed('B'):
                self.current_mode = "home"
                self.selected_index = 0
                self.draw_screen()
                time.sleep_ms(200)

            # Constellation cursor movement
            if not self.joystick.left_pin.value():
                self.constellation_cursor["x"] = max(40, self.constellation_cursor["x"] - 5)
                self.draw_screen()
                time.sleep_ms(100)
            elif not self.joystick.right_pin.value():
                self.constellation_cursor["x"] = min(195, self.constellation_cursor["x"] + 5)
                self.draw_screen()
                time.sleep_ms(100)
            elif not self.joystick.up_pin.value():
                self.constellation_cursor["y"] = max(40, self.constellation_cursor["y"] - 5)
                self.draw_screen()
                time.sleep_ms(100)
            elif not self.joystick.down_pin.value():
                self.constellation_cursor["y"] = min(195, self.constellation_cursor["y"] + 5)
                self.draw_screen()
                time.sleep_ms(100)

        return True

    def handle_quick_log_input(self):
        """Handle input for quick log mode"""
        if self.buttons.is_pressed('B'):
            if self.log_step > 0:
                self.log_step -= 1
                self.draw_screen()
            else:
                self.current_mode = "home"
                self.selected_index = 0
                self.draw_screen()
            time.sleep_ms(200)

        elif self.buttons.is_pressed('A'):
            if self.log_step == 0:
                # Select person
                if self.selected_index < len(self.people):
                    self.current_log["pid"] = self.people[self.selected_index]["id"]
                    self.log_step += 1
                    self.selected_index = 0

            elif self.log_step == 1:
                # Select vibe and move to intensity if vibe is selected
                if self.selected_index >= 0:  # Star selected
                    self.current_log["valence"] = abs(self.current_log.get("valence", 1))
                else:  # Scar selected
                    self.current_log["valence"] = -abs(self.current_log.get("valence", 1))
                self.log_step += 1
                self.selected_index = 0

            elif self.log_step == 2:
                # Select tag and complete
                if self.selected_index < len(self.interaction_tags):
                    self.current_log["tag"] = self.interaction_tags[self.selected_index]
                    self.complete_log()

            self.draw_screen()
            time.sleep_ms(200)

        # Navigation within current step
        elif self.buttons.is_pressed('UP'):
            if self.log_step == 0:
                self.selected_index = (self.selected_index - 1) % len(self.people)
            elif self.log_step == 1:
                if self.selected_index >= 0:
                    # Adjust intensity for current vibe
                    current_val = self.current_log.get("valence", 0)
                    if current_val > 0:
                        self.current_log["valence"] = min(3, current_val + 1)
                    else:
                        self.current_log["valence"] = min(-1, current_val + 1)
            elif self.log_step == 2:
                self.selected_index = (self.selected_index - 1) % len(self.interaction_tags)
            self.draw_screen()
            time.sleep_ms(150)

        elif self.buttons.is_pressed('DOWN'):
            if self.log_step == 0:
                self.selected_index = (self.selected_index + 1) % len(self.people)
            elif self.log_step == 1:
                if self.selected_index >= 0:
                    # Adjust intensity for current vibe
                    current_val = self.current_log.get("valence", 0)
                    if current_val > 0:
                        self.current_log["valence"] = max(1, current_val - 1)
                    else:
                        self.current_log["valence"] = max(-3, current_val - 1)
            elif self.log_step == 2:
                self.selected_index = (self.selected_index + 1) % len(self.interaction_tags)
            self.draw_screen()
            time.sleep_ms(150)

    def handle_deep_log_input(self):
        """Handle input for deep log mode"""
        if self.buttons.is_pressed('B'):
            if self.log_step > 0:
                self.log_step -= 1
                self.draw_screen()
            else:
                self.current_mode = "home"
                self.selected_index = 0
                self.draw_screen()
            time.sleep_ms(200)

        elif self.buttons.is_pressed('A'):
            if self.log_step == 0:
                # Select person
                if self.selected_index < len(self.people):
                    self.current_log["pid"] = self.people[self.selected_index]["id"]
                    self.log_step += 1
                    self.selected_index = 0

            elif self.log_step == 1:
                # Select vibe and intensity
                if self.selected_index >= 0:
                    self.current_log["valence"] = abs(self.current_log.get("valence", 1))
                else:
                    self.current_log["valence"] = -abs(self.current_log.get("valence", 1))
                self.log_step += 1
                self.selected_index = 0

            elif self.log_step == 2:
                # Select emotion
                if self.selected_index < len(self.emotions):
                    self.current_log["feel"] = self.emotions[self.selected_index]
                    self.log_step += 1
                    self.selected_index = 0

            elif self.log_step == 3:
                # Select need
                if self.selected_index < len(self.needs):
                    self.current_log["need"] = self.needs[self.selected_index]
                    self.log_step += 1
                    self.selected_index = 0

            elif self.log_step == 4:
                # Select note and complete
                note_options = [
                    "felt overwhelmed", "they really got it", "miscommunication",
                    "felt supported", "boundary crossed", "great connection"
                ]
                if self.selected_index < len(note_options):
                    self.current_log["note"] = note_options[self.selected_index]
                    self.complete_log()

            self.draw_screen()
            time.sleep_ms(200)

        # Navigation
        elif self.buttons.is_pressed('UP'):
            if self.log_step == 0:
                self.selected_index = (self.selected_index - 1) % len(self.people)
            elif self.log_step == 1:
                # Adjust intensity
                current_val = self.current_log.get("valence", 0)
                if current_val > 0:
                    self.current_log["valence"] = min(3, current_val + 1)
                else:
                    self.current_log["valence"] = min(-1, current_val + 1)
            elif self.log_step == 2:
                self.selected_index = (self.selected_index - 1) % len(self.emotions)
            elif self.log_step == 3:
                self.selected_index = (self.selected_index - 1) % len(self.needs)
            elif self.log_step == 4:
                self.selected_index = (self.selected_index - 1) % 6
            self.draw_screen()
            time.sleep_ms(150)

        elif self.buttons.is_pressed('DOWN'):
            if self.log_step == 0:
                self.selected_index = (self.selected_index + 1) % len(self.people)
            elif self.log_step == 1:
                # Adjust intensity
                current_val = self.current_log.get("valence", 0)
                if current_val > 0:
                    self.current_log["valence"] = max(1, current_val - 1)
                else:
                    self.current_log["valence"] = max(-3, current_val - 1)
            elif self.log_step == 2:
                self.selected_index = (self.selected_index + 1) % len(self.emotions)
            elif self.log_step == 3:
                self.selected_index = (self.selected_index + 1) % len(self.needs)
            elif self.log_step == 4:
                self.selected_index = (self.selected_index + 1) % 6
            self.draw_screen()
            time.sleep_ms(150)

    def handle_repair_input(self):
        """Handle input for repair ritual mode"""
        if self.buttons.is_pressed('B'):
            self.current_mode = "home"
            self.selected_index = 0
            self.draw_screen()
            time.sleep_ms(200)

        elif self.buttons.is_pressed('A'):
            # Check if there are unresolved scars
            unresolved_scars = [e for e in self.entries if e["valence"] < 0 and self.calculate_healing_score(e) > 0]
            if unresolved_scars and self.selected_index < len(self.repair_types):
                repair_type = self.repair_types[self.selected_index]
                self.start_repair_ritual(repair_type)
            self.draw_screen()
            time.sleep_ms(200)

        elif self.buttons.is_pressed('UP'):
            self.selected_index = (self.selected_index - 1) % len(self.repair_types)
            self.draw_screen()
            time.sleep_ms(150)

        elif self.buttons.is_pressed('DOWN'):
            self.selected_index = (self.selected_index + 1) % len(self.repair_types)
            self.draw_screen()
            time.sleep_ms(150)

    def cleanup(self):
        """Cleanup when exiting app"""
        self.save_data()