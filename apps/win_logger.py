"""
Win Logger - Daily Wins and Achievements Tracker
Log small victories, categorize wins (work/personal), track win streaks
"""

import time
import random
from lib.st7789 import Color

class WinLogger:
    def __init__(self, display, joystick, buttons):
        """Initialize Win Logger app"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        # Win categories
        self.categories = [
            {"name": "Work", "color": Color.BLUE, "icon": "W"},
            {"name": "Personal", "color": Color.GREEN, "icon": "P"},
            {"name": "Health", "color": Color.RED, "icon": "H"},
            {"name": "Learning", "color": Color.PURPLE, "icon": "L"},
            {"name": "Social", "color": Color.ORANGE, "icon": "S"},
            {"name": "Creative", "color": Color.MAGENTA, "icon": "C"}
        ]
        
        # Current state
        self.daily_wins = []  # List of today's wins with categories
        self.total_wins = 0
        self.current_date = self.get_date_string()
        self.selected_category = 0
        
        # View modes
        self.view_mode = "main"  # "main", "add", "history", "stats"
        
        # Win streak data
        self.streak_data = {}  # date -> win_count
        
        # Celebration messages
        self.celebration_messages = [
            "Amazing work!",
            "Victory achieved!",
            "You're crushing it!",
            "Way to go!",
            "Fantastic job!",
            "Keep it up!",
            "Brilliant win!",
            "Outstanding!",
            "You did it!",
            "Epic achievement!"
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
        """Check if it's a new day and archive yesterday's wins"""
        today = self.get_date_string()
        if today != self.current_date:
            # Archive yesterday's wins
            if len(self.daily_wins) > 0:
                self.streak_data[self.current_date] = len(self.daily_wins)
                self.total_wins += len(self.daily_wins)
                
            # Reset for new day
            self.current_date = today
            self.daily_wins = []
            self.save_data()
            
    def load_data(self):
        """Load saved win data"""
        try:
            import json
            with open("/stores/win_logger.json", "r") as f:
                data = json.load(f)
                self.current_date = data.get("current_date", self.current_date)
                self.daily_wins = data.get("daily_wins", [])
                self.total_wins = data.get("total_wins", 0)
                self.streak_data = data.get("streak_data", {})
        except:
            # Try old format or new user
            self.try_migrate_old_data()
            
    def try_migrate_old_data(self):
        """Try to migrate from simple text format"""
        try:
            with open("/stores/win_logger.dat", "r") as f:
                lines = f.readlines()
                for line in lines:
                    parts = line.strip().split(",")
                    if len(parts) >= 3:
                        if parts[0] == "current":
                            self.current_date = parts[1]
                            # Could parse old daily wins here
                        elif parts[0] == "total":
                            self.total_wins = int(parts[1])
        except:
            pass
            
    def save_data(self):
        """Save win data to JSON"""
        try:
            import json
            data = {
                "current_date": self.current_date,
                "daily_wins": self.daily_wins,
                "total_wins": self.total_wins,
                "streak_data": self.streak_data,
                "last_save": time.ticks_ms()
            }
            with open("/stores/win_logger.json", "w") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Save error: {e}")
            
    def draw_screen(self):
        """Draw the appropriate screen based on view mode"""
        self.display.fill(Color.BLACK)
        
        if self.view_mode == "main":
            self.draw_main_view()
        elif self.view_mode == "add":
            self.draw_add_win_view()
        elif self.view_mode == "history":
            self.draw_history_view()
        elif self.view_mode == "stats":
            self.draw_stats_view()
            
        self.display.display()
        
    def draw_main_view(self):
        """Draw the main win logger view"""
        # Title with trophy
        self.display.text("WIN LOGGER", 70, 10, Color.YELLOW)
        self.draw_trophy(200, 8, Color.YELLOW)
        
        # Today's date
        date_text = f"Today: {self.current_date[-5:]}"  # Show MM-DD
        date_x = (240 - len(date_text) * 8) // 2
        self.display.text(date_text, date_x, 30, Color.GRAY)
        
        # Today's win count - large display
        win_count = len(self.daily_wins)
        count_str = str(win_count)
        self.draw_large_number(count_str, 120, 55, Color.GREEN)
        
        # "Wins Today" label
        label = "Wins Today"
        label_x = (240 - len(label) * 8) // 2
        self.display.text(label, label_x, 95, Color.WHITE)
        
        # Show recent wins (last 3)
        if self.daily_wins:
            self.display.text("Recent Wins:", 20, 115, Color.CYAN)
            y_pos = 135
            recent_wins = self.daily_wins[-3:]  # Last 3 wins
            
            for win in recent_wins:
                # Find category info
                category_info = self.categories[win.get("category", 0)]
                category_color = category_info["color"]
                
                # Draw category indicator
                self.display.fill_rect(25, y_pos, 8, 8, category_color)
                
                # Win text (truncated if too long)
                win_text = win.get("text", "Win")
                if len(win_text) > 20:
                    win_text = win_text[:17] + "..."
                    
                self.display.text(win_text, 40, y_pos, Color.WHITE)
                y_pos += 15
        else:
            # No wins yet today
            no_wins_text = "No wins yet today!"
            no_wins_x = (240 - len(no_wins_text) * 8) // 2
            self.display.text(no_wins_text, no_wins_x, 130, Color.GRAY)
            
            encouragement = "Press A to add one!"
            enc_x = (240 - len(encouragement) * 8) // 2
            self.display.text(encouragement, enc_x, 150, Color.CYAN)
        
        # Instructions
        self.display.text("A:Add Win Y:History", 40, 190, Color.GRAY)
        self.display.text("X:Stats B:Home", 70, 205, Color.GRAY)
        
    def draw_add_win_view(self):
        """Draw the add win view with category selection"""
        # Title
        self.display.text("ADD WIN", 85, 10, Color.YELLOW)
        self.draw_trophy(150, 8, Color.YELLOW)
        
        # Instructions
        self.display.text("Choose Category:", 55, 35, Color.WHITE)
        
        # Draw category grid (2x3)
        grid_start_x = 30
        grid_start_y = 55
        grid_width = 85
        grid_height = 25
        grid_padding = 10
        
        for i, category in enumerate(self.categories):
            row = i // 2
            col = i % 2
            x = grid_start_x + col * (grid_width + grid_padding)
            y = grid_start_y + row * (grid_height + grid_padding)
            
            # Highlight selected category
            if i == self.selected_category:
                self.display.fill_rect(x - 2, y - 2, grid_width + 4, grid_height + 4, Color.WHITE)
                self.display.fill_rect(x, y, grid_width, grid_height, Color.BLACK)
                text_color = Color.WHITE
                border_color = Color.WHITE
            else:
                text_color = category["color"]
                border_color = category["color"]
            
            # Category rectangle
            self.display.rect(x, y, grid_width, grid_height, border_color)
            
            # Category name
            name_x = x + (grid_width - len(category["name"]) * 8) // 2
            name_y = y + (grid_height - 8) // 2
            self.display.text(category["name"], name_x, name_y, text_color)
            
        # Quick win suggestions based on category
        suggestions = self.get_category_suggestions()
        if suggestions:
            self.display.text("Quick Ideas:", 20, 175, Color.CYAN)
            suggestion = suggestions[time.ticks_ms() // 2000 % len(suggestions)]
            if len(suggestion) > 25:
                suggestion = suggestion[:22] + "..."
            sugg_x = (240 - len(suggestion) * 8) // 2
            self.display.text(suggestion, sugg_x, 190, Color.WHITE)
        
        # Instructions
        self.display.text("Joy:Select A:Quick Win", 30, 210, Color.GRAY)
        self.display.text("Y:Custom B:Back", 55, 225, Color.GRAY)
        
    def draw_history_view(self):
        """Draw win history over the past week"""
        # Title
        self.display.text("WIN HISTORY", 65, 10, Color.YELLOW)
        
        # Get last 7 days including today
        all_dates = list(self.streak_data.keys())
        if self.current_date not in all_dates and len(self.daily_wins) > 0:
            all_dates.append(self.current_date)
            
        # Sort and take last 7 days
        sorted_dates = sorted(all_dates, reverse=True)[:7]
        sorted_dates.reverse()  # Oldest first
        
        # Draw history bars
        y_start = 40
        bar_height = 15
        max_wins = max([self.streak_data.get(date, 0) for date in sorted_dates] + [len(self.daily_wins), 1])
        
        for i, date in enumerate(sorted_dates):
            y = y_start + (i * 20)
            
            # Date label
            day_label = date[-5:] if len(date) > 5 else date
            if date == self.current_date:
                day_label += "*"
                win_count = len(self.daily_wins)
            else:
                win_count = self.streak_data.get(date, 0)
                
            self.display.text(day_label, 10, y, Color.WHITE)
            
            # Win count
            self.display.text(str(win_count), 70, y, Color.WHITE)
            
            # Progress bar
            bar_width = int((win_count / max_wins) * 120) if max_wins > 0 else 0
            bar_color = Color.GREEN if win_count >= 3 else Color.BLUE if win_count > 0 else Color.DARK_GRAY
            
            self.display.rect(90, y, 120, bar_height, Color.GRAY)
            if bar_width > 0:
                self.display.fill_rect(91, y + 1, bar_width, bar_height - 2, bar_color)
        
        # Current streak
        streak = self.calculate_win_streak()
        if streak > 0:
            streak_text = f"Win Streak: {streak} days"
            streak_x = (240 - len(streak_text) * 8) // 2
            self.display.text(streak_text, streak_x, 190, Color.ORANGE)
        
        # Instructions
        self.display.text("Y:Main X:Stats B:Home", 40, 210, Color.GRAY)
        
    def draw_stats_view(self):
        """Draw statistics and achievements"""
        # Title
        self.display.text("WIN STATS", 80, 10, Color.YELLOW)
        
        # Calculate stats
        total_wins_all_time = self.total_wins + sum(self.streak_data.values()) + len(self.daily_wins)
        week_wins = sum([self.streak_data.get(date, 0) for date in list(self.streak_data.keys())[-7:]]) + len(self.daily_wins)
        days_tracked = len(self.streak_data) + (1 if len(self.daily_wins) > 0 else 0)
        avg_daily = week_wins / 7 if week_wins > 0 else 0
        
        # Category breakdown
        category_counts = {}
        for win in self.daily_wins:
            cat_idx = win.get("category", 0)
            cat_name = self.categories[cat_idx]["name"]
            category_counts[cat_name] = category_counts.get(cat_name, 0) + 1
        
        # Draw stats
        stats = [
            (f"Today: {len(self.daily_wins)}", Color.GREEN),
            (f"This Week: {week_wins}", Color.BLUE),
            (f"All Time: {total_wins_all_time}", Color.MAGENTA),
            (f"Daily Avg: {avg_daily:.1f}", Color.CYAN),
            (f"Best Streak: {self.get_best_streak()}", Color.ORANGE)
        ]
        
        y_pos = 35
        for stat, color in stats:
            stat_x = (240 - len(stat) * 8) // 2
            self.display.text(stat, stat_x, y_pos, color)
            y_pos += 18
            
        # Top category today
        if category_counts:
            top_cat = max(category_counts.items(), key=lambda x: x[1])
            top_text = f"Top Today: {top_cat[0]} ({top_cat[1]})"
            top_x = (240 - len(top_text) * 8) // 2
            self.display.text(top_text, top_x, y_pos + 10, Color.YELLOW)
        
        # Achievement badges
        badges = []
        if len(self.daily_wins) >= 5:
            badges.append("Daily Champion!")
        if week_wins >= 20:
            badges.append("Weekly Warrior!")
        if self.calculate_win_streak() >= 7:
            badges.append("Week Streak!")
            
        if badges:
            badge_y = 165
            for badge in badges[:2]:  # Show max 2 badges
                badge_x = (240 - len(badge) * 8) // 2
                self.display.text(badge, badge_x, badge_y, Color.YELLOW)
                badge_y += 15
        
        # Instructions  
        self.display.text("Y:Main X:History B:Home", 25, 210, Color.GRAY)
        
    def get_category_suggestions(self):
        """Get quick win suggestions for selected category"""
        suggestions_by_category = {
            0: ["Completed task", "Sent email", "Made progress", "Solved problem"],  # Work
            1: ["Did chores", "Organized space", "Self-care time", "Called family"],  # Personal
            2: ["Drank water", "Took walk", "Ate healthy", "Got good sleep"],        # Health
            3: ["Read article", "Watched tutorial", "Practiced skill", "Asked question"], # Learning
            4: ["Helped someone", "Good conversation", "Made plans", "Sent message"],   # Social
            5: ["Created something", "Tried new idea", "Drew/wrote", "Experimented"]    # Creative
        }
        return suggestions_by_category.get(self.selected_category, ["Great achievement!"])
        
    def draw_large_number(self, number, x, y, color):
        """Draw large number for win count"""
        digit_width = 18
        total_width = len(number) * digit_width
        start_x = x - (total_width // 2)
        
        for i, digit in enumerate(number):
            digit_x = start_x + (i * digit_width)
            self.draw_large_digit(digit, digit_x, y, color)
            
    def draw_large_digit(self, digit, x, y, color):
        """Draw large digit using block pattern"""
        # 5x7 patterns for digits
        patterns = {
            '0': ["11111", "10001", "10001", "10001", "10001", "10001", "11111"],
            '1': ["00100", "01100", "00100", "00100", "00100", "00100", "11111"],
            '2': ["11111", "00001", "00001", "11111", "10000", "10000", "11111"],
            '3': ["11111", "00001", "00001", "11111", "00001", "00001", "11111"],
            '4': ["10001", "10001", "10001", "11111", "00001", "00001", "00001"],
            '5': ["11111", "10000", "10000", "11111", "00001", "00001", "11111"],
            '6': ["11111", "10000", "10000", "11111", "10001", "10001", "11111"],
            '7': ["11111", "00001", "00001", "00010", "00100", "01000", "10000"],
            '8': ["11111", "10001", "10001", "11111", "10001", "10001", "11111"],
            '9': ["11111", "10001", "10001", "11111", "00001", "00001", "11111"]
        }
        
        if digit in patterns:
            pattern = patterns[digit]
            block_size = 2
            for row in range(7):
                for col in range(5):
                    if pattern[row][col] == '1':
                        self.display.fill_rect(
                            x + col * block_size,
                            y + row * block_size,
                            block_size,
                            block_size,
                            color
                        )
    
    def draw_trophy(self, x, y, color):
        """Draw a small trophy icon"""
        # Trophy base
        self.display.fill_rect(x, y + 8, 8, 3, color)
        # Trophy cup
        self.display.fill_rect(x + 1, y + 4, 6, 4, color)
        # Trophy handles
        self.display.pixel(x - 1, y + 5, color)
        self.display.pixel(x + 8, y + 5, color)
        # Trophy top
        self.display.fill_rect(x + 2, y + 1, 4, 3, color)
        self.display.pixel(x + 3, y, color)
        self.display.pixel(x + 4, y, color)
        
    def calculate_win_streak(self):
        """Calculate current win streak (consecutive days with wins)"""
        all_dates = list(self.streak_data.keys())
        if len(self.daily_wins) > 0:
            all_dates.append(self.current_date)
            
        sorted_dates = sorted(all_dates, reverse=True)
        
        streak = 0
        for date in sorted_dates:
            if date == self.current_date:
                count = len(self.daily_wins)
            else:
                count = self.streak_data.get(date, 0)
                
            if count > 0:
                streak += 1
            else:
                break
                
        return streak
        
    def get_best_streak(self):
        """Get the best win streak ever"""
        # This is a simplified calculation - could be enhanced
        current_streak = self.calculate_win_streak()
        # For now, return current streak as best
        # In a full implementation, you'd track historical best streaks
        return current_streak
        
    def add_quick_win(self):
        """Add a quick win based on selected category"""
        suggestions = self.get_category_suggestions()
        win_text = random.choice(suggestions)
        
        win_entry = {
            "text": win_text,
            "category": self.selected_category,
            "timestamp": time.ticks_ms()
        }
        
        self.daily_wins.append(win_entry)
        self.save_data()
        
        # Show celebration
        celebration = random.choice(self.celebration_messages)
        self.show_celebration(celebration)
        
    def show_celebration(self, message):
        """Show celebration animation"""
        # Fill screen with celebration
        self.display.fill(Color.BLACK)
        
        # Draw celebration message
        msg_x = (240 - len(message) * 8) // 2
        self.display.text(message, msg_x, 100, Color.YELLOW)
        
        # Draw trophy
        self.draw_trophy(115, 120, Color.YELLOW)
        
        # Add some sparkles
        for _ in range(15):
            spark_x = random.randint(20, 220)
            spark_y = random.randint(40, 180)
            spark_color = random.choice([Color.YELLOW, Color.WHITE, Color.CYAN])
            self.display.pixel(spark_x, spark_y, spark_color)
            
        self.display.display()
        time.sleep_ms(1500)
        
    def update(self):
        """Update Win Logger app"""
        self.check_new_day()
        
        if self.view_mode == "main":
            # Add win
            if self.buttons.is_pressed('A'):
                self.view_mode = "add"
                self.selected_category = 0
                self.draw_screen()
                time.sleep_ms(200)
                
            # View history
            elif self.buttons.is_pressed('Y'):
                self.view_mode = "history"
                self.draw_screen()
                time.sleep_ms(200)
                
            # View stats
            elif self.buttons.is_pressed('X'):
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
                    
            # Add quick win
            if self.buttons.is_pressed('A'):
                self.add_quick_win()
                self.view_mode = "main"
                self.draw_screen()
                time.sleep_ms(200)
                
            # Back to main
            if self.buttons.is_pressed('B'):
                self.view_mode = "main"
                self.draw_screen()
                time.sleep_ms(200)
                
        elif self.view_mode in ["history", "stats"]:
            # Navigation between views
            if self.buttons.is_pressed('Y'):
                self.view_mode = "main"
                self.draw_screen()
                time.sleep_ms(200)
            elif self.buttons.is_pressed('X'):
                if self.view_mode == "history":
                    self.view_mode = "stats"
                else:
                    self.view_mode = "history"
                self.draw_screen()
                time.sleep_ms(200)
            elif self.buttons.is_pressed('B'):
                self.view_mode = "main"
                self.draw_screen()
                time.sleep_ms(200)
        
        # Check for exit (only from main view)
        if self.buttons.is_pressed('B') and self.view_mode == "main":
            return False
            
        return True
        
    def cleanup(self):
        """Cleanup when exiting app"""
        self.save_data()