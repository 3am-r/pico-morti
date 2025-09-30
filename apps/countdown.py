"""
Enhanced Countdown & Timer Hub
Features: Multiple countdowns, stopwatch, timer alerts, visual countdown bars
"""

import time
import json
from lib.st7789 import Color

class CountdownHub:
    def __init__(self, display, joystick, buttons):
        """Initialize enhanced countdown hub"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        # App state
        self.view_mode = "main"  # "main", "countdown_list", "edit", "stopwatch", "quick_timer"
        self.selected_index = 0
        self.menu_items = ["Countdowns", "Stopwatch", "Quick Timer", "Add New"]
        
        # Countdown data
        self.countdowns = []
        self.load_countdowns()
        
        # Stopwatch state
        self.stopwatch_start = 0
        self.stopwatch_running = False
        self.stopwatch_elapsed = 0
        self.stopwatch_laps = []
        
        # Quick timer state
        self.quick_timer_start = 0
        self.quick_timer_duration = 300000  # 5 minutes default
        self.quick_timer_running = False
        
        # Edit state
        self.edit_countdown = None
        self.edit_field = 0
        
    def init(self):
        """Initialize app when opened"""
        self.view_mode = "main"
        self.selected_index = 0
        self.draw_screen()
        
    def load_countdowns(self):
        """Load saved countdowns from JSON file"""
        try:
            with open("/stores/countdowns.json", "r") as f:
                data = json.load(f)
                self.countdowns = data.get("countdowns", [])
        except:
            self.countdowns = []
            
    def save_countdowns(self):
        """Save countdowns to JSON file"""
        try:
            data = {"countdowns": self.countdowns}
            with open("/stores/countdowns.json", "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Save error: {e}")
            
    def draw_screen(self):
        """Draw the appropriate screen"""
        self.display.fill(Color.BLACK)
        
        if self.view_mode == "main":
            self.draw_main_menu()
        elif self.view_mode == "countdown_list":
            self.draw_countdown_list()
        elif self.view_mode == "edit":
            self.draw_edit_screen()
        elif self.view_mode == "stopwatch":
            self.draw_stopwatch()
        elif self.view_mode == "quick_timer":
            self.draw_quick_timer()
            
        self.display.display()
        
    def draw_main_menu(self):
        """Draw main menu"""
        # Title with dynamic info
        self.display.text("TIMER HUB", 80, 10, Color.CYAN)
        
        # Show quick stats
        active_count = sum(1 for cd in self.countdowns if cd.get("target_ms", 0) > time.ticks_ms())
        expired_count = len(self.countdowns) - active_count
        
        stats = f"{active_count} active, {expired_count} expired"
        stats_x = (240 - len(stats) * 8) // 2
        self.display.text(stats, stats_x, 30, Color.GRAY)
        
        # Menu items
        y_pos = 60
        for i, item in enumerate(self.menu_items):
            color = Color.WHITE if i == self.selected_index else Color.GRAY
            
            # Highlight selected
            if i == self.selected_index:
                self.display.fill_rect(30, y_pos - 2, 180, 20, Color.DARK_GRAY)
                
            # Icons
            if item == "Countdowns":
                icon = f"[{len(self.countdowns)}]"
                self.display.text(icon, 35, y_pos, Color.YELLOW)
                self.display.text(item, 75, y_pos, color)
            elif item == "Stopwatch":
                icon = "[SW]"
                status = "RUN" if self.stopwatch_running else "STP"
                self.display.text(icon, 35, y_pos, Color.GREEN)
                self.display.text(item, 75, y_pos, color)
                self.display.text(status, 150, y_pos, Color.GREEN if self.stopwatch_running else Color.RED)
            elif item == "Quick Timer":
                icon = "[QT]"
                mins = self.quick_timer_duration // 60000
                self.display.text(icon, 35, y_pos, Color.BLUE)
                self.display.text(item, 75, y_pos, color)
                self.display.text(f"{mins}m", 170, y_pos, Color.BLUE)
            else:  # Add New
                icon = "[+]"
                self.display.text(icon, 35, y_pos, Color.MAGENTA)
                self.display.text(item, 75, y_pos, color)
                
            y_pos += 25
            
        # Show next countdown if any
        next_countdown = self.get_next_countdown()
        if next_countdown:
            self.display.text("Next Event:", 20, 170, Color.WHITE)
            self.display.text(next_countdown["name"], 20, 185, Color.YELLOW)
            
            # Time remaining
            remaining_ms = next_countdown["target_ms"] - time.ticks_ms()
            if remaining_ms > 0:
                time_str = self.format_time_remaining(remaining_ms)
                self.display.text(time_str, 20, 200, Color.GREEN)
            else:
                self.display.text("EXPIRED!", 20, 200, Color.RED)
                
        # Instructions
        self.display.text("Joy:Select A:Open B:Home", 30, 225, Color.GRAY)
        
    def draw_countdown_list(self):
        """Draw list of all countdowns"""
        self.display.text("COUNTDOWNS", 70, 10, Color.CYAN)
        
        if not self.countdowns:
            self.display.text("No countdowns", 65, 100, Color.GRAY)
            self.display.text("Press A to add", 70, 120, Color.YELLOW)
        else:
            # List countdowns
            y_pos = 35
            for i, cd in enumerate(self.countdowns[:6]):  # Max 6 visible
                if i == self.selected_index:
                    self.display.fill_rect(5, y_pos - 2, 230, 30, Color.DARK_GRAY)
                    
                # Name
                name = cd["name"][:15]  # Truncate if too long
                self.display.text(name, 10, y_pos, Color.WHITE)
                
                # Time remaining
                remaining_ms = cd["target_ms"] - time.ticks_ms()
                if remaining_ms > 0:
                    time_str = self.format_time_remaining(remaining_ms, short=True)
                    color = cd.get("color", Color.GREEN)
                    
                    # Progress bar
                    if "created_ms" in cd:
                        total_duration = cd["target_ms"] - cd["created_ms"]
                        progress = max(0, 1 - (remaining_ms / total_duration))
                        bar_width = int(100 * progress)
                        self.display.rect(10, y_pos + 15, 100, 5, Color.GRAY)
                        if bar_width > 0:
                            self.display.fill_rect(10, y_pos + 15, bar_width, 5, color)
                else:
                    time_str = "EXPIRED"
                    color = Color.RED
                    
                self.display.text(time_str, 130, y_pos, color)
                y_pos += 32
                
        # Instructions
        if self.countdowns:
            self.display.text("Joy:Select A:Edit X:Del", 30, 210, Color.GRAY)
        self.display.text("Y:Add New B:Back", 65, 225, Color.GRAY)
        
    def draw_stopwatch(self):
        """Draw stopwatch interface"""
        self.display.text("STOPWATCH", 75, 10, Color.GREEN)
        
        # Calculate elapsed time
        if self.stopwatch_running:
            current_elapsed = time.ticks_diff(time.ticks_ms(), self.stopwatch_start)
            total_elapsed = self.stopwatch_elapsed + current_elapsed
        else:
            total_elapsed = self.stopwatch_elapsed
            
        # Large time display
        time_str = self.format_elapsed_time(total_elapsed)
        time_x = (240 - len(time_str) * 12) // 2  # Larger font simulation
        self.draw_large_text(time_str, time_x, 50, Color.WHITE)
        
        # Status
        status = "RUNNING" if self.stopwatch_running else "STOPPED"
        status_color = Color.GREEN if self.stopwatch_running else Color.RED
        status_x = (240 - len(status) * 8) // 2
        self.display.text(status, status_x, 85, status_color)
        
        # Lap times (last 4)
        if self.stopwatch_laps:
            self.display.text("Laps:", 20, 110, Color.CYAN)
            y_pos = 125
            for lap_time in self.stopwatch_laps[-4:]:
                lap_str = self.format_elapsed_time(lap_time)
                self.display.text(lap_str, 20, y_pos, Color.YELLOW)
                y_pos += 15
                
        # Controls
        if self.stopwatch_running:
            self.display.text("A:Stop Y:Lap", 75, 200, Color.WHITE)
        else:
            if self.stopwatch_elapsed > 0:
                self.display.text("A:Resume X:Reset", 60, 200, Color.WHITE)
            else:
                self.display.text("A:Start", 90, 200, Color.WHITE)
                
        self.display.text("B:Back", 95, 220, Color.GRAY)
        
    def draw_quick_timer(self):
        """Draw quick timer interface"""
        self.display.text("QUICK TIMER", 70, 10, Color.BLUE)
        
        if self.quick_timer_running:
            # Timer is running - show countdown
            elapsed = time.ticks_diff(time.ticks_ms(), self.quick_timer_start)
            remaining = max(0, self.quick_timer_duration - elapsed)
            
            # Large countdown display
            time_str = self.format_time_remaining(remaining, include_seconds=True)
            time_x = (240 - len(time_str) * 10) // 2
            self.draw_large_text(time_str, time_x, 50, Color.WHITE)
            
            # Progress bar
            progress = 1 - (remaining / self.quick_timer_duration)
            bar_width = int(200 * progress)
            self.display.rect(20, 90, 200, 10, Color.GRAY)
            if bar_width > 0:
                bar_color = Color.RED if remaining < 30000 else Color.BLUE
                self.display.fill_rect(20, 90, bar_width, 10, bar_color)
                
            # Status
            if remaining == 0:
                self.display.text("TIME'S UP!", 80, 110, Color.RED)
            else:
                self.display.text("RUNNING", 90, 110, Color.GREEN)
                
            self.display.text("A:Stop X:Reset", 75, 200, Color.WHITE)
        else:
            # Timer stopped - show duration setting
            mins = self.quick_timer_duration // 60000
            secs = (self.quick_timer_duration % 60000) // 1000
            
            self.display.text("Duration:", 85, 50, Color.WHITE)
            duration_str = f"{mins:02d}:{secs:02d}"
            duration_x = (240 - len(duration_str) * 12) // 2
            self.draw_large_text(duration_str, duration_x, 70, Color.CYAN)
            
            self.display.text("Left/Right: Adjust", 55, 120, Color.GRAY)
            self.display.text("A:Start", 90, 200, Color.WHITE)
            
        self.display.text("B:Back", 95, 220, Color.GRAY)
        
    def draw_edit_screen(self):
        """Draw countdown edit screen"""
        self.display.text("EDIT COUNTDOWN", 55, 10, Color.YELLOW)
        
        if not self.edit_countdown:
            self.edit_countdown = {
                "name": "Event",
                "days": 1,
                "hours": 0,
                "minutes": 0,
                "color": Color.GREEN
            }
            
        # Fields
        fields = [
            ("Name:", self.edit_countdown["name"]),
            ("Days:", str(self.edit_countdown["days"])),
            ("Hours:", str(self.edit_countdown["hours"])),
            ("Minutes:", str(self.edit_countdown["minutes"]))
        ]
        
        y_pos = 50
        for i, (label, value) in enumerate(fields):
            if i == self.edit_field:
                self.display.fill_rect(20, y_pos - 2, 200, 20, Color.DARK_GRAY)
                
            self.display.text(label, 25, y_pos, Color.WHITE)
            self.display.text(str(value), 100, y_pos, Color.CYAN)
            y_pos += 25
            
        # Preview
        total_ms = (self.edit_countdown["days"] * 24 * 60 * 60 * 1000 +
                   self.edit_countdown["hours"] * 60 * 60 * 1000 +
                   self.edit_countdown["minutes"] * 60 * 1000)
        preview = self.format_time_remaining(total_ms)
        self.display.text("Duration:", 25, 170, Color.WHITE)
        self.display.text(preview, 25, 185, Color.GREEN)
        
        self.display.text("Joy:Edit A:Save B:Cancel", 25, 220, Color.GRAY)
        
    def draw_large_text(self, text, x, y, color):
        """Draw larger text by overlaying"""
        for dx in range(2):
            for dy in range(2):
                self.display.text(text, x + dx, y + dy, color)
                
    def format_time_remaining(self, ms, short=False, include_seconds=False):
        """Format milliseconds into readable time"""
        if ms <= 0:
            return "00:00"
            
        days = ms // (24 * 60 * 60 * 1000)
        hours = (ms % (24 * 60 * 60 * 1000)) // (60 * 60 * 1000)
        minutes = (ms % (60 * 60 * 1000)) // (60 * 1000)
        seconds = (ms % (60 * 1000)) // 1000
        
        if short:
            if days > 0:
                return f"{days}d {hours}h"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        else:
            if include_seconds:
                if days > 0:
                    return f"{days}d {hours:02d}:{minutes:02d}:{seconds:02d}"
                elif hours > 0:
                    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                else:
                    return f"{minutes:02d}:{seconds:02d}"
            else:
                if days > 0:
                    return f"{days}d {hours:02d}:{minutes:02d}"
                else:
                    return f"{hours:02d}:{minutes:02d}"
                    
    def format_elapsed_time(self, ms):
        """Format elapsed time for stopwatch"""
        minutes = ms // (60 * 1000)
        seconds = (ms % (60 * 1000)) // 1000
        centiseconds = (ms % 1000) // 10
        return f"{minutes:02d}:{seconds:02d}.{centiseconds:02d}"
        
    def get_next_countdown(self):
        """Get the next upcoming countdown"""
        upcoming = [cd for cd in self.countdowns if cd.get("target_ms", 0) > time.ticks_ms()]
        if upcoming:
            return min(upcoming, key=lambda x: x["target_ms"])
        return None
        
    def update(self):
        """Update countdown app"""
        direction = self.joystick.get_direction_slow()
        
        if self.view_mode == "main":
            # Main menu navigation
            if direction == 'UP':
                self.selected_index = max(0, self.selected_index - 1)
                self.draw_screen()
            elif direction == 'DOWN':
                self.selected_index = min(len(self.menu_items) - 1, self.selected_index + 1)
                self.draw_screen()
                
            if self.buttons.is_pressed('A'):
                item = self.menu_items[self.selected_index]
                if item == "Countdowns":
                    self.view_mode = "countdown_list"
                    self.selected_index = 0
                elif item == "Stopwatch":
                    self.view_mode = "stopwatch"
                elif item == "Quick Timer":
                    self.view_mode = "quick_timer"
                elif item == "Add New":
                    self.view_mode = "edit"
                    self.edit_countdown = None
                    self.edit_field = 0
                self.draw_screen()
                time.sleep_ms(200)
                
        elif self.view_mode == "countdown_list":
            if direction == 'UP' and self.countdowns:
                self.selected_index = max(0, self.selected_index - 1)
                self.draw_screen()
            elif direction == 'DOWN' and self.countdowns:
                self.selected_index = min(len(self.countdowns) - 1, self.selected_index + 1)
                self.draw_screen()
                
            if self.buttons.is_pressed('A') and self.countdowns:
                # Edit selected countdown
                cd = self.countdowns[self.selected_index]
                remaining_ms = cd["target_ms"] - time.ticks_ms()
                
                self.edit_countdown = {
                    "name": cd["name"],
                    "days": max(0, remaining_ms // (24 * 60 * 60 * 1000)),
                    "hours": max(0, (remaining_ms % (24 * 60 * 60 * 1000)) // (60 * 60 * 1000)),
                    "minutes": max(0, (remaining_ms % (60 * 60 * 1000)) // (60 * 1000)),
                    "color": cd.get("color", Color.GREEN),
                    "edit_index": self.selected_index
                }
                self.view_mode = "edit"
                self.edit_field = 0
                self.draw_screen()
                time.sleep_ms(200)
                
            elif self.buttons.is_pressed('X') and self.countdowns:
                # Delete countdown
                del self.countdowns[self.selected_index]
                self.save_countdowns()
                self.selected_index = max(0, min(self.selected_index, len(self.countdowns) - 1))
                self.draw_screen()
                time.sleep_ms(200)
                
            elif self.buttons.is_pressed('Y'):
                # Add new countdown
                self.view_mode = "edit"
                self.edit_countdown = None
                self.edit_field = 0
                self.draw_screen()
                time.sleep_ms(200)
                
        elif self.view_mode == "stopwatch":
            if self.buttons.is_pressed('A'):
                if self.stopwatch_running:
                    # Stop
                    self.stopwatch_running = False
                    self.stopwatch_elapsed += time.ticks_diff(time.ticks_ms(), self.stopwatch_start)
                else:
                    # Start/Resume
                    self.stopwatch_running = True
                    self.stopwatch_start = time.ticks_ms()
                self.draw_screen()
                time.sleep_ms(200)
                
            elif self.buttons.is_pressed('Y') and self.stopwatch_running:
                # Lap time
                lap_time = self.stopwatch_elapsed + time.ticks_diff(time.ticks_ms(), self.stopwatch_start)
                self.stopwatch_laps.append(lap_time)
                if len(self.stopwatch_laps) > 10:  # Keep last 10 laps
                    self.stopwatch_laps = self.stopwatch_laps[-10:]
                self.draw_screen()
                time.sleep_ms(200)
                
            elif self.buttons.is_pressed('X') and not self.stopwatch_running:
                # Reset
                self.stopwatch_elapsed = 0
                self.stopwatch_laps = []
                self.draw_screen()
                time.sleep_ms(200)
                
        elif self.view_mode == "quick_timer":
            if not self.quick_timer_running:
                # Adjust duration
                if direction == 'LEFT':
                    self.quick_timer_duration = max(60000, self.quick_timer_duration - 60000)  # Min 1 minute
                    self.draw_screen()
                elif direction == 'RIGHT':
                    self.quick_timer_duration = min(3600000, self.quick_timer_duration + 60000)  # Max 60 minutes
                    self.draw_screen()
                    
            if self.buttons.is_pressed('A'):
                if self.quick_timer_running:
                    # Stop timer
                    self.quick_timer_running = False
                else:
                    # Start timer
                    self.quick_timer_running = True
                    self.quick_timer_start = time.ticks_ms()
                self.draw_screen()
                time.sleep_ms(200)
                
            elif self.buttons.is_pressed('X'):
                # Reset timer
                self.quick_timer_running = False
                self.draw_screen()
                time.sleep_ms(200)
                
        elif self.view_mode == "edit":
            # Edit countdown fields
            if direction == 'UP':
                self.edit_field = max(0, self.edit_field - 1)
                self.draw_screen()
            elif direction == 'DOWN':
                self.edit_field = min(3, self.edit_field + 1)
                self.draw_screen()
            elif direction in ['LEFT', 'RIGHT']:
                delta = 1 if direction == 'RIGHT' else -1
                
                if self.edit_field == 0:  # Name
                    names = ["Event", "Deadline", "Exam", "Meeting", "Birthday", "Project", "Trip", "Holiday"]
                    current_idx = names.index(self.edit_countdown["name"]) if self.edit_countdown["name"] in names else 0
                    self.edit_countdown["name"] = names[(current_idx + delta) % len(names)]
                elif self.edit_field == 1:  # Days
                    self.edit_countdown["days"] = max(0, min(365, self.edit_countdown["days"] + delta))
                elif self.edit_field == 2:  # Hours
                    self.edit_countdown["hours"] = max(0, min(23, self.edit_countdown["hours"] + delta))
                elif self.edit_field == 3:  # Minutes
                    self.edit_countdown["minutes"] = max(0, min(59, self.edit_countdown["minutes"] + delta * 5))
                    
                self.draw_screen()
                
            if self.buttons.is_pressed('A'):
                # Save countdown
                total_ms = (self.edit_countdown["days"] * 24 * 60 * 60 * 1000 +
                           self.edit_countdown["hours"] * 60 * 60 * 1000 +
                           self.edit_countdown["minutes"] * 60 * 1000)
                           
                countdown = {
                    "name": self.edit_countdown["name"],
                    "target_ms": time.ticks_ms() + total_ms,
                    "created_ms": time.ticks_ms(),
                    "color": Color.GREEN
                }
                
                if "edit_index" in self.edit_countdown:
                    # Update existing
                    self.countdowns[self.edit_countdown["edit_index"]] = countdown
                else:
                    # Add new
                    self.countdowns.append(countdown)
                    
                self.save_countdowns()
                self.view_mode = "countdown_list"
                self.edit_countdown = None
                self.draw_screen()
                time.sleep_ms(200)
                
        # Auto-update running timers
        if (self.stopwatch_running or self.quick_timer_running) and time.ticks_ms() % 100 == 0:
            self.draw_screen()
            
        # Check for exit
        if self.buttons.is_pressed('B'):
            if self.view_mode == "main":
                return False
            else:
                if self.view_mode in ["countdown_list", "stopwatch", "quick_timer"]:
                    self.view_mode = "main"
                    self.selected_index = 0
                elif self.view_mode == "edit":
                    self.view_mode = "countdown_list" if self.countdowns else "main"
                    self.edit_countdown = None
                self.draw_screen()
                time.sleep_ms(200)
                
        return True
        
    def cleanup(self):
        """Cleanup when exiting app"""
        self.edit_countdown = None