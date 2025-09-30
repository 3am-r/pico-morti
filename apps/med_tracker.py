"""
MedTracker - Medication Tracking App
Track daily medication intake with weekly calendar view
Stores progress in JSON format for long-term tracking
"""

import time
import json
import gc
from lib.st7789 import Color

class MedTracker:
    def __init__(self, display, joystick, buttons):
        """Initialize MedTracker app"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        # App state
        self.running = True
        self.view_mode = "weekly"  # weekly, settings, stats
        
        # Calendar navigation
        self.selected_day = 0  # 0-6 (Monday to Sunday)
        self.current_week_offset = 0  # Weeks from current week
        
        # Settings
        self.med_name = "Medication"
        self.daily_doses = 1
        self.reminder_enabled = True
        
        # Data storage
        self.data_file = "/stores/med_tracker_data.json"
        self.med_data = self.load_data()
        
        # Week days for display
        self.weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        self.weekdays_full = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
    def init(self):
        """Initialize the app when opened"""
        self.running = True
        self.view_mode = "weekly"
        self.selected_day = self.get_current_weekday()
        self.current_week_offset = 0
        self.draw_screen()
        
    def cleanup(self):
        """Cleanup when app closes"""
        self.save_data()
        gc.collect()
        
    def load_data(self):
        """Load medication data from JSON file"""
        try:
            with open(self.data_file, "r") as f:
                data = json.load(f)
                return data
        except (OSError, ValueError):
            # File doesn't exist or is corrupted, create new structure
            return {
                "medication_name": "Medication",
                "daily_doses": 1,
                "records": {},  # Format: "YYYY-MM-DD": {"taken": True/False, "doses": 1, "time": "HH:MM"}
                "streak": 0,
                "total_days": 0,
                "compliance_rate": 0.0
            }
    
    def save_data(self):
        """Save medication data to JSON file"""
        try:
            # Update statistics before saving
            self.calculate_stats()
            
            with open(self.data_file, "w") as f:
                json.dump(self.med_data, f)
                print("MedTracker: Data saved successfully")
        except Exception as e:
            print(f"MedTracker: Save error - {e}")
    
    def get_current_weekday(self):
        """Get current day of week (0=Monday, 6=Sunday)"""
        # time.localtime() returns (year, month, day, hour, min, sec, weekday, yearday)
        # weekday: 0=Monday, 6=Sunday
        return time.localtime()[6]
    
    def get_date_string(self, day_offset=0):
        """Get date string in YYYY-MM-DD format"""
        # Get current time and add day offset
        current_time = time.time()
        target_time = current_time + (day_offset * 24 * 60 * 60)
        target_tm = time.localtime(target_time)
        
        return f"{target_tm[0]:04d}-{target_tm[1]:02d}-{target_tm[2]:02d}"
    
    def get_week_dates(self):
        """Get dates for current week view"""
        # Calculate offset to get to Monday of target week
        current_weekday = self.get_current_weekday()
        days_to_monday = -current_weekday  # Monday is 0
        week_start_offset = days_to_monday + (self.current_week_offset * 7)
        
        week_dates = []
        for i in range(7):
            date_str = self.get_date_string(week_start_offset + i)
            week_dates.append(date_str)
        
        return week_dates
    
    def is_med_taken(self, date_str):
        """Check if medication was taken on given date"""
        return self.med_data["records"].get(date_str, {}).get("taken", False)
    
    def toggle_med_status(self, date_str):
        """Toggle medication status for given date"""
        if date_str not in self.med_data["records"]:
            self.med_data["records"][date_str] = {}
        
        current_status = self.med_data["records"][date_str].get("taken", False)
        new_status = not current_status
        
        # Get current time for timestamp
        now = time.localtime()
        time_str = f"{now[3]:02d}:{now[4]:02d}"
        
        self.med_data["records"][date_str] = {
            "taken": new_status,
            "doses": self.daily_doses if new_status else 0,
            "time": time_str if new_status else None
        }
        
        # Auto-save after changes
        self.save_data()
    
    def calculate_stats(self):
        """Calculate medication compliance statistics"""
        if not self.med_data["records"]:
            self.med_data.update({
                "streak": 0,
                "total_days": 0,
                "compliance_rate": 0.0
            })
            return
        
        # Calculate current streak (consecutive days taken)
        current_date = self.get_date_string()
        streak = 0
        check_date = current_date
        
        # Count backwards from today
        for i in range(365):  # Limit to avoid infinite loop
            if self.is_med_taken(check_date):
                streak += 1
                # Move to previous day
                yesterday_time = time.time() - ((i + 1) * 24 * 60 * 60)
                yesterday_tm = time.localtime(yesterday_time)
                check_date = f"{yesterday_tm[0]:04d}-{yesterday_tm[1]:02d}-{yesterday_tm[2]:02d}"
            else:
                break
        
        # Calculate total compliance
        total_days = len(self.med_data["records"])
        taken_days = sum(1 for record in self.med_data["records"].values() if record.get("taken", False))
        compliance_rate = (taken_days / total_days * 100) if total_days > 0 else 0.0
        
        self.med_data.update({
            "streak": streak,
            "total_days": total_days,
            "compliance_rate": compliance_rate
        })
    
    def draw_screen(self):
        """Draw the main screen based on current mode"""
        self.display.fill(Color.BLACK)
        
        if self.view_mode == "weekly":
            self.draw_weekly_view()
        elif self.view_mode == "settings":
            self.draw_settings_view()
        elif self.view_mode == "stats":
            self.draw_stats_view()
        
        self.display.display()
    
    def draw_weekly_view(self):
        """Draw weekly medication tracking calendar"""
        # Header
        header_y = 8
        title = "MedTracker"
        title_x = (self.display.width - len(title) * 8) // 2
        self.display.text(title, title_x, header_y, Color.WHITE)
        
        # Week navigation info
        week_info = f"Week {self.current_week_offset:+d}" if self.current_week_offset != 0 else "This Week"
        info_x = (self.display.width - len(week_info) * 8) // 2
        self.display.text(week_info, info_x, header_y + 20, Color.CYAN)
        
        # Get dates for current week
        week_dates = self.get_week_dates()
        
        # Calendar grid
        grid_start_y = header_y + 50
        day_width = (self.display.width - 20) // 7
        day_height = 60
        
        for i, (day_abbr, date_str) in enumerate(zip(self.weekdays, week_dates)):
            x = 10 + i * day_width
            y = grid_start_y
            
            # Highlight selected day
            if i == self.selected_day:
                self.display.fill_rect(x, y, day_width, day_height, Color.rgb565(40, 60, 80))
                self.display.rect(x, y, day_width, day_height, Color.WHITE)
                day_color = Color.WHITE
                status_color = Color.YELLOW
            else:
                day_color = Color.LIGHT_GRAY
                status_color = Color.GRAY
            
            # Day abbreviation
            day_x = x + (day_width - len(day_abbr) * 8) // 2
            self.display.text(day_abbr, day_x, y + 5, day_color)
            
            # Day number (extract from date)
            day_num = date_str.split("-")[2]
            num_x = x + (day_width - len(day_num) * 8) // 2
            self.display.text(day_num, num_x, y + 18, day_color)
            
            # Medication status indicator
            is_taken = self.is_med_taken(date_str)
            if is_taken:
                # Green checkmark area
                self.display.fill_rect(x + 2, y + 32, day_width - 4, 20, Color.rgb565(0, 100, 0))
                self.display.text("✓", x + day_width//2 - 4, y + 36, Color.WHITE)
            else:
                # Red X or empty area
                is_future = date_str > self.get_date_string()
                if not is_future:
                    self.display.fill_rect(x + 2, y + 32, day_width - 4, 20, Color.rgb565(100, 0, 0))
                    self.display.text("✗", x + day_width//2 - 4, y + 36, Color.WHITE)
                else:
                    # Future day - gray
                    self.display.fill_rect(x + 2, y + 32, day_width - 4, 20, Color.rgb565(30, 30, 30))
                    self.display.text("—", x + day_width//2 - 4, y + 36, Color.DARK_GRAY)
        
        # Current medication info
        med_y = grid_start_y + day_height + 20
        med_name = self.med_data.get("medication_name", "Medication")
        med_text = f"Med: {med_name}"
        if len(med_text) > 20:
            med_text = med_text[:17] + "..."
        self.display.text(med_text, 10, med_y, Color.CYAN)
        
        # Quick stats
        self.calculate_stats()
        streak = self.med_data.get("streak", 0)
        compliance = self.med_data.get("compliance_rate", 0)
        
        streak_text = f"Streak: {streak}d"
        self.display.text(streak_text, 10, med_y + 15, Color.GREEN if streak > 0 else Color.GRAY)
        
        compliance_text = f"Rate: {compliance:.0f}%"
        comp_color = Color.GREEN if compliance >= 80 else Color.ORANGE if compliance >= 60 else Color.RED
        self.display.text(compliance_text, 10, med_y + 30, comp_color)
        
        # Instructions
        footer_y = self.display.height - 35
        self.display.text("L/R:Day U/D:Week A:Toggle", 5, footer_y, Color.DARK_GRAY)
        self.display.text("X:Stats Y:Settings B:Exit", 5, footer_y + 12, Color.DARK_GRAY)
    
    def draw_settings_view(self):
        """Draw settings configuration screen"""
        header_y = 8
        title = "MedTracker Settings"
        title_x = (self.display.width - len(title) * 8) // 2
        self.display.text(title, title_x, header_y, Color.WHITE)
        
        # Settings options
        options_y = header_y + 40
        
        self.display.text("Coming soon:", 10, options_y, Color.CYAN)
        self.display.text("- Medication name", 10, options_y + 20, Color.LIGHT_GRAY)
        self.display.text("- Daily dose count", 10, options_y + 35, Color.LIGHT_GRAY)
        self.display.text("- Reminder settings", 10, options_y + 50, Color.LIGHT_GRAY)
        self.display.text("- Export data", 10, options_y + 65, Color.LIGHT_GRAY)
        
        # Instructions
        footer_y = self.display.height - 20
        instructions = "B:Back to Calendar"
        inst_x = (self.display.width - len(instructions) * 8) // 2
        self.display.text(instructions, inst_x, footer_y, Color.GRAY)
    
    def draw_stats_view(self):
        """Draw statistics and compliance view"""
        header_y = 8
        title = "Medication Stats"
        title_x = (self.display.width - len(title) * 8) // 2
        self.display.text(title, title_x, header_y, Color.WHITE)
        
        # Calculate and display detailed stats
        self.calculate_stats()
        
        stats_y = header_y + 35
        
        # Current streak
        streak = self.med_data.get("streak", 0)
        streak_text = f"Current Streak: {streak} days"
        self.display.text(streak_text, 10, stats_y, Color.GREEN if streak > 0 else Color.GRAY)
        
        # Total tracking days
        total_days = self.med_data.get("total_days", 0)
        total_text = f"Total Days Tracked: {total_days}"
        self.display.text(total_text, 10, stats_y + 20, Color.CYAN)
        
        # Compliance rate
        compliance = self.med_data.get("compliance_rate", 0)
        comp_text = f"Compliance Rate: {compliance:.1f}%"
        comp_color = Color.GREEN if compliance >= 80 else Color.ORANGE if compliance >= 60 else Color.RED
        self.display.text(comp_text, 10, stats_y + 40, comp_color)
        
        # Visual compliance bar
        bar_y = stats_y + 65
        bar_width = self.display.width - 20
        bar_height = 12
        
        self.display.rect(10, bar_y, bar_width, bar_height, Color.WHITE)
        fill_width = int((bar_width - 2) * compliance / 100)
        if fill_width > 0:
            self.display.fill_rect(11, bar_y + 1, fill_width, bar_height - 2, comp_color)
        
        # Recent activity summary
        recent_y = bar_y + 30
        self.display.text("Last 7 days:", 10, recent_y, Color.CYAN)
        
        # Show last 7 days status
        status_y = recent_y + 20
        for i in range(7):
            date_str = self.get_date_string(-i)
            is_taken = self.is_med_taken(date_str)
            x_pos = 10 + i * 30
            
            if is_taken:
                self.display.text("✓", x_pos, status_y, Color.GREEN)
            else:
                self.display.text("✗", x_pos, status_y, Color.RED)
        
        # Instructions
        footer_y = self.display.height - 20
        instructions = "B:Back to Calendar"
        inst_x = (self.display.width - len(instructions) * 8) // 2
        self.display.text(instructions, inst_x, footer_y, Color.GRAY)
    
    def handle_input(self):
        """Handle user input"""
        self.buttons.update()
        
        if self.view_mode == "weekly":
            return self.handle_weekly_input()
        elif self.view_mode == "settings":
            return self.handle_settings_input()
        elif self.view_mode == "stats":
            return self.handle_stats_input()
        
        return True
    
    def handle_weekly_input(self):
        """Handle input in weekly view"""
        # Navigate days (left/right)
        if not self.joystick.left_pin.value():
            self.selected_day = max(0, self.selected_day - 1)
            self.draw_screen()
            time.sleep_ms(150)
        elif not self.joystick.right_pin.value():
            self.selected_day = min(6, self.selected_day + 1)
            self.draw_screen()
            time.sleep_ms(150)
        
        # Navigate weeks (up/down)
        elif not self.joystick.up_pin.value():
            self.current_week_offset -= 1
            self.draw_screen()
            time.sleep_ms(200)
        elif not self.joystick.down_pin.value():
            self.current_week_offset += 1
            self.draw_screen()
            time.sleep_ms(200)
        
        # Toggle medication status (A button)
        elif self.buttons.is_pressed('A'):
            week_dates = self.get_week_dates()
            selected_date = week_dates[self.selected_day]
            
            # Don't allow toggling future dates
            if selected_date <= self.get_date_string():
                self.toggle_med_status(selected_date)
                self.draw_screen()
            time.sleep_ms(200)
        
        # View statistics (X button)
        elif self.buttons.is_pressed('X'):
            self.view_mode = "stats"
            self.draw_screen()
            time.sleep_ms(200)
        
        # Settings (Y button)
        elif self.buttons.is_pressed('Y'):
            self.view_mode = "settings"
            self.draw_screen()
            time.sleep_ms(200)
        
        # Exit app (B button)
        elif self.buttons.is_pressed('B'):
            return False
        
        return True
    
    def handle_settings_input(self):
        """Handle input in settings view"""
        # Go back to weekly view
        if self.buttons.is_pressed('B'):
            self.view_mode = "weekly"
            self.draw_screen()
            time.sleep_ms(200)
        
        return True
    
    def handle_stats_input(self):
        """Handle input in stats view"""
        # Go back to weekly view
        if self.buttons.is_pressed('B'):
            self.view_mode = "weekly"
            self.draw_screen()
            time.sleep_ms(200)
        
        return True
    
    def update(self):
        """Main update loop"""
        return self.handle_input()