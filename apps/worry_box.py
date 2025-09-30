"""
Worry Box - Capture and Contain Anxious Thoughts
Quick worry logging, scheduled worry time, worry categorization, release ritual
"""

import time
import random
from lib.st7789 import Color

class WorryBox:
    def __init__(self, display, joystick, buttons):
        """Initialize Worry Box app"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        # Worry storage
        self.current_worries = []  # Active worries in the box
        self.released_count = 0  # Total worries released
        self.current_date = self.get_date_string()
        
        # Worry categories for quick logging
        self.worry_categories = [
            {"name": "Work", "color": Color.BLUE, "icon": "W"},
            {"name": "Health", "color": Color.RED, "icon": "H"},
            {"name": "Money", "color": Color.GREEN, "icon": "$"},
            {"name": "Social", "color": Color.ORANGE, "icon": "S"},
            {"name": "Future", "color": Color.PURPLE, "icon": "F"},
            {"name": "Other", "color": Color.GRAY, "icon": "?"}
        ]
        
        # Current state
        self.selected_category = 0
        self.view_mode = "main"  # "main", "add", "review", "release", "stats"
        self.selected_worry_index = 0
        
        # Worry time scheduling
        self.worry_time_enabled = False
        self.worry_time_hour = 18  # Default: 6 PM
        self.last_worry_time_check = 0
        
        # Calming messages
        self.calming_messages = [
            "You are safe now",
            "This too shall pass",
            "One step at a time",
            "Breathe deeply",
            "You've got this",
            "It's okay to worry",
            "You are stronger",
            "Tomorrow is new",
            "Be gentle with yourself",
            "This feeling will pass"
        ]
        
        # Release affirmations
        self.release_affirmations = [
            "I release this worry",
            "I let this go",
            "This no longer serves me",
            "I choose peace",
            "I am free from this",
            "I trust the process",
            "I embrace calm",
            "I release control"
        ]
        
        # Load saved data
        self.load_data()
        
    def init(self):
        """Initialize app when opened"""
        self.check_new_day()
        self.view_mode = "main"
        self.draw_screen()
        
    def get_date_string(self):
        """Get current date as string"""
        try:
            import machine
            rtc = machine.RTC()
            dt = rtc.datetime()
            return f"{dt[0]}-{dt[1]:02d}-{dt[2]:02d}"
        except:
            # Fallback: use ticks as day counter
            days = time.ticks_ms() // (24 * 60 * 60 * 1000)
            return f"day-{days}"
            
    def check_new_day(self):
        """Check if it's a new day and archive old worries"""
        today = self.get_date_string()
        if today != self.current_date:
            # Auto-release old worries (new day = fresh start)
            old_worry_count = len(self.current_worries)
            if old_worry_count > 0:
                self.released_count += old_worry_count
                self.current_worries = []
                
            self.current_date = today
            self.save_data()
            
    def load_data(self):
        """Load saved worry data"""
        try:
            import json
            with open("/stores/worry_box.json", "r") as f:
                data = json.load(f)
                self.current_worries = data.get("current_worries", [])
                self.released_count = data.get("released_count", 0)
                self.current_date = data.get("current_date", self.current_date)
                self.worry_time_enabled = data.get("worry_time_enabled", False)
                self.worry_time_hour = data.get("worry_time_hour", 18)
        except:
            # New user or no data
            pass
            
    def save_data(self):
        """Save worry data to JSON"""
        try:
            import json
            data = {
                "current_worries": self.current_worries,
                "released_count": self.released_count,
                "current_date": self.current_date,
                "worry_time_enabled": self.worry_time_enabled,
                "worry_time_hour": self.worry_time_hour,
                "last_save": time.ticks_ms()
            }
            with open("/stores/worry_box.json", "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Save error: {e}")
            
    def draw_screen(self):
        """Draw the appropriate screen based on view mode"""
        self.display.fill(Color.BLACK)
        
        if self.view_mode == "main":
            self.draw_main_view()
        elif self.view_mode == "add":
            self.draw_add_worry_view()
        elif self.view_mode == "review":
            self.draw_review_worries_view()
        elif self.view_mode == "release":
            self.draw_release_ritual_view()
        elif self.view_mode == "stats":
            self.draw_stats_view()
            
        self.display.display()
        
    def draw_main_view(self):
        """Draw the main worry box view"""
        # Title with box icon
        self.display.text("WORRY BOX", 75, 10, Color.DARK_GRAY)
        self.draw_box_icon(190, 8, Color.DARK_GRAY)
        
        # Draw the worry box visualization
        self.draw_worry_box_visual()
        
        # Current worry count
        worry_count = len(self.current_worries)
        if worry_count == 0:
            status_text = "Box is empty"
            status_color = Color.GREEN
        elif worry_count <= 3:
            status_text = f"{worry_count} worries stored"
            status_color = Color.YELLOW
        else:
            status_text = f"{worry_count} worries stored"
            status_color = Color.ORANGE
            
        status_x = (240 - len(status_text) * 8) // 2
        self.display.text(status_text, status_x, 140, status_color)
        
        # Calming message
        msg_index = (time.ticks_ms() // 5000) % len(self.calming_messages)
        calming_msg = self.calming_messages[msg_index]
        msg_x = (240 - len(calming_msg) * 8) // 2
        self.display.text(calming_msg, msg_x, 160, Color.CYAN)
        
        # Worry time indicator
        if self.worry_time_enabled:
            time_text = f"Worry time: {self.worry_time_hour}:00"
            time_x = (240 - len(time_text) * 8) // 2
            self.display.text(time_text, time_x, 175, Color.GRAY)
        
        # Instructions
        self.display.text("A:Add Y:Review X:Release", 20, 195, Color.GRAY)
        self.display.text("B:Home", 95, 210, Color.GRAY)
        
    def draw_worry_box_visual(self):
        """Draw a visual representation of the worry box"""
        # Box dimensions
        box_x = 60
        box_y = 50
        box_width = 120
        box_height = 80
        
        # Draw 3D box effect
        # Back face (darker)
        self.display.fill_rect(box_x + 5, box_y + 5, box_width, box_height, Color.DARK_GRAY)
        
        # Front face
        self.display.rect(box_x, box_y, box_width, box_height, Color.WHITE)
        self.display.fill_rect(box_x + 1, box_y + 1, box_width - 2, box_height - 2, Color.BLACK)
        
        # Box lid (partially open if worries present)
        if len(self.current_worries) > 0:
            # Open lid
            lid_y = box_y - 10
            self.display.fill_rect(box_x, lid_y, box_width, 8, Color.GRAY)
            self.display.rect(box_x, lid_y, box_width, 8, Color.WHITE)
        else:
            # Closed lid
            self.display.fill_rect(box_x, box_y, box_width, 8, Color.GRAY)
            self.display.rect(box_x, box_y, box_width, 8, Color.WHITE)
            
        # Draw worry particles inside box (if any)
        if self.current_worries:
            for i, worry in enumerate(self.current_worries[:5]):  # Show max 5 particles
                # Create floating worry particles
                particle_x = box_x + 20 + (i * 20) + random.randint(-5, 5)
                particle_y = box_y + 30 + (i * 8) + random.randint(-3, 3)
                
                # Get category color
                cat_idx = worry.get("category", 5)
                particle_color = self.worry_categories[cat_idx]["color"]
                
                # Draw particle
                self.display.fill_circle(particle_x, particle_y, 3, particle_color)
                
        # Box label
        label = "WORRIES"
        label_x = box_x + (box_width - len(label) * 8) // 2
        self.display.text(label, label_x, box_y + 40, Color.GRAY)
        
    def draw_add_worry_view(self):
        """Draw the add worry view with categories"""
        # Title
        self.display.text("ADD WORRY", 80, 10, Color.DARK_GRAY)
        
        # Instructions
        self.display.text("What type of worry?", 45, 30, Color.WHITE)
        
        # Draw category grid (2x3)
        grid_start_x = 30
        grid_start_y = 50
        grid_width = 85
        grid_height = 28
        grid_padding = 10
        
        for i, category in enumerate(self.worry_categories):
            row = i // 2
            col = i % 2
            x = grid_start_x + col * (grid_width + grid_padding)
            y = grid_start_y + row * (grid_height + grid_padding)
            
            # Highlight selected category
            if i == self.selected_category:
                self.display.fill_rect(x - 2, y - 2, grid_width + 4, grid_height + 4, Color.WHITE)
                self.display.fill_rect(x, y, grid_width, grid_height, Color.BLACK)
                text_color = Color.WHITE
            else:
                text_color = category["color"]
                
            # Category rectangle
            self.display.rect(x, y, grid_width, grid_height, category["color"])
            
            # Category icon and name
            icon_text = f"{category['icon']} {category['name']}"
            name_x = x + (grid_width - len(icon_text) * 8) // 2
            name_y = y + (grid_height - 8) // 2
            self.display.text(icon_text, name_x, name_y, text_color)
            
        # Reassurance message
        reassurance = "It's safe to put it here"
        reass_x = (240 - len(reassurance) * 8) // 2
        self.display.text(reassurance, reass_x, 180, Color.CYAN)
        
        # Instructions
        self.display.text("Joy:Select A:Add B:Back", 25, 205, Color.GRAY)
        
    def draw_review_worries_view(self):
        """Draw the review worries view"""
        # Title
        self.display.text("REVIEW WORRIES", 55, 10, Color.DARK_GRAY)
        
        if not self.current_worries:
            # No worries to review
            empty_msg = "No worries in box"
            msg_x = (240 - len(empty_msg) * 8) // 2
            self.display.text(empty_msg, msg_x, 100, Color.GREEN)
            
            peace_msg = "Enjoy this peace"
            peace_x = (240 - len(peace_msg) * 8) // 2
            self.display.text(peace_msg, peace_x, 120, Color.CYAN)
        else:
            # List worries
            y_pos = 35
            for i, worry in enumerate(self.current_worries[:8]):  # Show max 8
                # Get category info
                cat_idx = worry.get("category", 5)
                category = self.worry_categories[cat_idx]
                
                # Highlight selected worry
                if i == self.selected_worry_index:
                    self.display.fill_rect(10, y_pos - 2, 220, 20, Color.DARK_GRAY)
                    text_color = Color.WHITE
                else:
                    text_color = Color.GRAY
                    
                # Category indicator
                self.display.fill_rect(15, y_pos + 2, 10, 10, category["color"])
                
                # Worry text (category name and time)
                time_str = self.format_worry_time(worry.get("timestamp", 0))
                worry_text = f"{category['name']} - {time_str}"
                self.display.text(worry_text, 30, y_pos + 2, text_color)
                
                y_pos += 20
                
            # Selected worry detail
            if self.selected_worry_index < len(self.current_worries):
                selected = self.current_worries[self.selected_worry_index]
                cat = self.worry_categories[selected.get("category", 5)]
                detail_text = f"Type: {cat['name']}"
                self.display.text(detail_text, 20, 190, cat["color"])
                
        # Instructions
        if self.current_worries:
            self.display.text("Joy:Nav A:Release B:Back", 20, 210, Color.GRAY)
        else:
            self.display.text("B:Back", 95, 210, Color.GRAY)
            
    def draw_release_ritual_view(self):
        """Draw the release ritual animation"""
        # This is called multiple times for animation
        self.display.fill(Color.BLACK)
        
        # Title
        self.display.text("RELEASE RITUAL", 60, 20, Color.WHITE)
        
        # Draw floating away animation
        box_y = 100
        for i in range(5):
            # Particles floating up
            particle_y = box_y - (i * 15)
            particle_x = 120 + random.randint(-30, 30)
            opacity = 5 - i  # Fade as they go up
            
            if opacity > 0:
                color = Color.GRAY if opacity < 3 else Color.WHITE
                self.display.fill_circle(particle_x, particle_y, opacity, color)
                
        # Release affirmation
        affirmation_idx = (time.ticks_ms() // 2000) % len(self.release_affirmations)
        affirmation = self.release_affirmations[affirmation_idx]
        aff_x = (240 - len(affirmation) * 8) // 2
        self.display.text(affirmation, aff_x, 140, Color.CYAN)
        
        # Breathing guide
        breath_phase = (time.ticks_ms() // 1000) % 8
        if breath_phase < 4:
            breath_text = "Breathe in..."
            circle_size = 10 + breath_phase * 3
        else:
            breath_text = "Breathe out..."
            circle_size = 22 - (breath_phase - 4) * 3
            
        breath_x = (240 - len(breath_text) * 8) // 2
        self.display.text(breath_text, breath_x, 170, Color.GREEN)
        
        # Breathing circle
        self.display.circle(120, 100, circle_size, Color.GREEN)
        
        # Instructions
        self.display.text("A:Complete B:Cancel", 45, 210, Color.GRAY)
        
        self.display.display()
        
    def draw_stats_view(self):
        """Draw statistics and insights"""
        # Title
        self.display.text("WORRY STATS", 70, 10, Color.DARK_GRAY)
        
        # Calculate category breakdown
        category_counts = {}
        for worry in self.current_worries:
            cat_idx = worry.get("category", 5)
            cat_name = self.worry_categories[cat_idx]["name"]
            category_counts[cat_name] = category_counts.get(cat_name, 0) + 1
            
        # Stats display
        stats = [
            (f"Current worries: {len(self.current_worries)}", Color.YELLOW),
            (f"Released total: {self.released_count}", Color.GREEN),
            (f"Peace score: {self.calculate_peace_score()}%", Color.CYAN)
        ]
        
        y_pos = 40
        for stat, color in stats:
            stat_x = (240 - len(stat) * 8) // 2
            self.display.text(stat, stat_x, y_pos, color)
            y_pos += 20
            
        # Top worry category
        if category_counts:
            top_category = max(category_counts.items(), key=lambda x: x[1])
            top_text = f"Most common: {top_category[0]}"
            top_x = (240 - len(top_text) * 8) // 2
            self.display.text(top_text, top_x, y_pos + 10, Color.ORANGE)
            y_pos += 30
            
        # Worry pattern visualization (simple bar chart)
        if category_counts:
            self.display.text("Worry Types:", 20, y_pos + 10, Color.WHITE)
            bar_y = y_pos + 30
            bar_x = 30
            
            for cat_name, count in list(category_counts.items())[:3]:  # Show top 3
                # Find category color
                cat_color = Color.GRAY
                for cat in self.worry_categories:
                    if cat["name"] == cat_name:
                        cat_color = cat["color"]
                        break
                        
                # Draw bar
                bar_width = count * 30
                self.display.fill_rect(bar_x, bar_y, bar_width, 10, cat_color)
                self.display.text(cat_name[:4], bar_x + bar_width + 5, bar_y, Color.WHITE)
                bar_y += 15
                
        # Insight based on worry levels
        insight = self.get_worry_insight()
        insight_x = (240 - len(insight) * 8) // 2
        self.display.text(insight, insight_x, 185, Color.CYAN)
        
        # Instructions
        self.display.text("B:Back", 95, 210, Color.GRAY)
        
    def draw_box_icon(self, x, y, color):
        """Draw a small box icon"""
        # Box body
        self.display.rect(x, y + 2, 10, 8, color)
        # Box lid
        self.display.fill_rect(x, y, 10, 3, color)
        # Box opening
        self.display.pixel(x + 5, y + 5, color)
        
    def format_worry_time(self, timestamp):
        """Format timestamp to readable time"""
        # Simple time ago format
        current = time.ticks_ms()
        diff = time.ticks_diff(current, timestamp) // 60000  # Minutes
        
        if diff < 60:
            return f"{diff}m ago"
        elif diff < 1440:  # Less than a day
            return f"{diff // 60}h ago"
        else:
            return "old"
            
    def calculate_peace_score(self):
        """Calculate a peace score based on worry management"""
        if len(self.current_worries) == 0:
            return 100
        elif len(self.current_worries) <= 2:
            return 80
        elif len(self.current_worries) <= 4:
            return 60
        elif len(self.current_worries) <= 6:
            return 40
        else:
            return 20
            
    def get_worry_insight(self):
        """Get insight message based on worry patterns"""
        worry_count = len(self.current_worries)
        
        if worry_count == 0:
            return "Clear mind space"
        elif worry_count <= 2:
            return "Well managed"
        elif worry_count <= 4:
            return "Consider releasing"
        elif worry_count <= 6:
            return "Time to let go"
        else:
            return "Release recommended"
            
    def add_worry(self):
        """Add a worry to the box"""
        worry = {
            "category": self.selected_category,
            "timestamp": time.ticks_ms(),
            "date": self.current_date
        }
        
        self.current_worries.append(worry)
        self.save_data()
        
        # Show containment message
        self.display.fill(Color.BLACK)
        
        # Draw box animation
        self.draw_worry_box_visual()
        
        # Confirmation message
        msg = "Worry contained safely"
        msg_x = (240 - len(msg) * 8) // 2
        self.display.text(msg, msg_x, 150, Color.GREEN)
        
        # Calming message
        calm_msg = random.choice(self.calming_messages)
        calm_x = (240 - len(calm_msg) * 8) // 2
        self.display.text(calm_msg, calm_x, 170, Color.CYAN)
        
        self.display.display()
        time.sleep_ms(1500)
        
    def release_worry(self, index):
        """Release a specific worry"""
        if 0 <= index < len(self.current_worries):
            self.current_worries.pop(index)
            self.released_count += 1
            self.save_data()
            
            # Show release animation
            for _ in range(3):
                self.draw_release_ritual_view()
                time.sleep_ms(500)
                
            # Completion message
            self.display.fill(Color.BLACK)
            complete_msg = "Worry released"
            msg_x = (240 - len(complete_msg) * 8) // 2
            self.display.text(complete_msg, msg_x, 100, Color.GREEN)
            
            peace_msg = "You are free"
            peace_x = (240 - len(peace_msg) * 8) // 2
            self.display.text(peace_msg, peace_x, 120, Color.CYAN)
            
            self.display.display()
            time.sleep_ms(1000)
            
    def release_all_worries(self):
        """Release all worries at once"""
        worry_count = len(self.current_worries)
        if worry_count > 0:
            self.released_count += worry_count
            self.current_worries = []
            self.save_data()
            
            # Extended release animation
            for _ in range(5):
                self.draw_release_ritual_view()
                time.sleep_ms(400)
                
            # Completion message
            self.display.fill(Color.BLACK)
            msg = f"Released {worry_count} worries"
            msg_x = (240 - len(msg) * 8) // 2
            self.display.text(msg, msg_x, 100, Color.GREEN)
            
            free_msg = "Mind is clear"
            free_x = (240 - len(free_msg) * 8) // 2
            self.display.text(free_msg, free_x, 120, Color.CYAN)
            
            self.display.display()
            time.sleep_ms(1500)
            
    def update(self):
        """Update Worry Box app"""
        self.check_new_day()
        
        if self.view_mode == "main":
            # Add worry
            if self.buttons.is_pressed('A'):
                self.view_mode = "add"
                self.selected_category = 0
                self.draw_screen()
                time.sleep_ms(200)
                
            # Review worries
            elif self.buttons.is_pressed('Y'):
                self.view_mode = "review"
                self.selected_worry_index = 0
                self.draw_screen()
                time.sleep_ms(200)
                
            # Release all worries
            elif self.buttons.is_pressed('X'):
                if len(self.current_worries) > 0:
                    self.view_mode = "release"
                    self.draw_screen()
                    time.sleep_ms(200)
                else:
                    # Show stats if no worries to release
                    self.view_mode = "stats"
                    self.draw_screen()
                    time.sleep_ms(200)
                    
        elif self.view_mode == "add":
            # Navigate categories
            direction = self.joystick.get_direction_slow()
            if direction == 'UP':
                if self.selected_category >= 2:
                    self.selected_category -= 2
                    self.draw_screen()
            elif direction == 'DOWN':
                if self.selected_category < 4:
                    self.selected_category += 2
                    self.draw_screen()
            elif direction == 'LEFT':
                if self.selected_category % 2 == 1:
                    self.selected_category -= 1
                    self.draw_screen()
            elif direction == 'RIGHT':
                if self.selected_category % 2 == 0 and self.selected_category < 5:
                    self.selected_category += 1
                    self.draw_screen()
                    
            # Add worry
            if self.buttons.is_pressed('A'):
                self.add_worry()
                self.view_mode = "main"
                self.draw_screen()
                time.sleep_ms(200)
                
            # Back
            if self.buttons.is_pressed('B'):
                self.view_mode = "main"
                self.draw_screen()
                time.sleep_ms(200)
                
        elif self.view_mode == "review":
            if self.current_worries:
                # Navigate worries
                direction = self.joystick.get_direction_slow()
                if direction == 'UP':
                    if self.selected_worry_index > 0:
                        self.selected_worry_index -= 1
                        self.draw_screen()
                elif direction == 'DOWN':
                    if self.selected_worry_index < len(self.current_worries) - 1:
                        self.selected_worry_index += 1
                        self.draw_screen()
                        
                # Release selected worry
                if self.buttons.is_pressed('A'):
                    self.release_worry(self.selected_worry_index)
                    if self.selected_worry_index >= len(self.current_worries):
                        self.selected_worry_index = max(0, len(self.current_worries) - 1)
                    if not self.current_worries:
                        self.view_mode = "main"
                    self.draw_screen()
                    time.sleep_ms(200)
                    
            # Back
            if self.buttons.is_pressed('B'):
                self.view_mode = "main"
                self.draw_screen()
                time.sleep_ms(200)
                
        elif self.view_mode == "release":
            # Complete release ritual
            if self.buttons.is_pressed('A'):
                self.release_all_worries()
                self.view_mode = "main"
                self.draw_screen()
                time.sleep_ms(200)
                
            # Cancel
            if self.buttons.is_pressed('B'):
                self.view_mode = "main"
                self.draw_screen()
                time.sleep_ms(200)
                
        elif self.view_mode == "stats":
            # Back
            if self.buttons.is_pressed('B'):
                self.view_mode = "main"
                self.draw_screen()
                time.sleep_ms(200)
                
        # Check for exit (only from main)
        if self.buttons.is_pressed('B') and self.view_mode == "main":
            return False
            
        return True
        
    def cleanup(self):
        """Cleanup when exiting app"""
        self.save_data()