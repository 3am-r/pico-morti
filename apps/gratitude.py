"""
Gratitude Proxy - Manual Gratitude Counter
Press A to count gratitudes with daily estimates and weekly progress bars
"""

import time
from lib.st7789 import Color

class GratitudeProxy:
    def __init__(self, display, joystick, buttons):
        """Initialize Gratitude Proxy app"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        # Gratitude tracking
        self.daily_count = 0
        self.total_count = 0
        self.current_date = self.get_date_string()
        self.weekly_data = {}  # date -> count
        
        # Load saved data
        self.load_data()
        
        # View modes
        self.view_mode = "counter"  # "counter", "weekly", "stats"
        
    def init(self):
        """Initialize app when opened"""
        self.check_new_day()
        self.view_mode = "counter"
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
        """Check if it's a new day and reset daily count"""
        today = self.get_date_string()
        if today != self.current_date:
            # Save yesterday's count to weekly data
            if self.daily_count > 0:
                self.weekly_data[self.current_date] = self.daily_count
                
            # Reset for new day
            self.current_date = today
            self.daily_count = 0
            self.save_data()
            
    def load_data(self):
        """Load saved gratitude data"""
        try:
            with open("/stores/gratitude.dat", "r") as f:
                lines = f.readlines()
                for line in lines:
                    parts = line.strip().split(",")
                    if len(parts) == 3:
                        if parts[0] == "current":
                            self.current_date = parts[1]
                            self.daily_count = int(parts[2])
                        elif parts[0] == "total":
                            self.total_count = int(parts[2])
                        else:
                            # Weekly data entry
                            self.weekly_data[parts[0]] = int(parts[1])
        except:
            # New user - initialize defaults
            pass
            
    def save_data(self):
        """Save gratitude data"""
        try:
            with open("/stores/gratitude.dat", "w") as f:
                # Save current day data
                f.write(f"current,{self.current_date},{self.daily_count}\n")
                f.write(f"total,count,{self.total_count}\n")
                
                # Save weekly data (last 7 days)
                sorted_dates = sorted(self.weekly_data.keys(), reverse=True)
                for date in sorted_dates[:7]:  # Keep only last 7 days
                    f.write(f"{date},{self.weekly_data[date]},weekly\n")
        except Exception as e:
            print(f"Save error: {e}")
            
    def draw_screen(self):
        """Draw the appropriate screen based on view mode"""
        self.display.fill(Color.BLACK)
        
        if self.view_mode == "counter":
            self.draw_counter_view()
        elif self.view_mode == "weekly":
            self.draw_weekly_view()
        elif self.view_mode == "stats":
            self.draw_stats_view()
            
        self.display.display()
        
    def draw_counter_view(self):
        """Draw the main counter view"""
        # Title
        title = "GRATITUDE"
        title_x = (240 - len(title) * 8) // 2
        self.display.text(title, title_x, 10, Color.YELLOW)
        
        # Today's date
        date_text = f"Today: {self.current_date[-5:]}"  # Show last 5 chars (MM-DD)
        date_x = (240 - len(date_text) * 8) // 2
        self.display.text(date_text, date_x, 30, Color.GRAY)
        
        # Daily count - large display
        count_str = str(self.daily_count)
        self.draw_large_counter(count_str, 120, 70, Color.GREEN)
        
        # Progress toward daily goal
        daily_goal = 5  # Aim for 5 gratitudes per day
        progress_text = f"Goal: {self.daily_count}/{daily_goal}"
        prog_x = (240 - len(progress_text) * 8) // 2
        self.display.text(progress_text, prog_x, 130, Color.WHITE)
        
        # Progress bar
        self.draw_progress_bar(self.daily_count, daily_goal, 50, 145, 140, 10)
        
        # Encouraging message based on count
        message = self.get_daily_message()
        msg_x = (240 - len(message) * 8) // 2
        self.display.text(message, msg_x, 170, Color.CYAN)
        
        # Instructions
        self.display.text("A:Count Y:Weekly B:Home", 25, 200, Color.GRAY)
        self.display.text("X:Stats", 90, 215, Color.GRAY)
        
    def draw_weekly_view(self):
        """Draw weekly progress bars"""
        # Title
        self.display.text("WEEKLY VIEW", 70, 10, Color.YELLOW)
        
        # Get last 7 days of data including today
        all_dates = list(self.weekly_data.keys())
        if self.current_date not in all_dates:
            all_dates.append(self.current_date)
            
        # Sort and take last 7 days
        sorted_dates = sorted(all_dates, reverse=True)[:7]
        sorted_dates.reverse()  # Oldest first for display
        
        # Draw bars for each day
        y_start = 40
        bar_height = 15
        max_count = max([self.weekly_data.get(date, 0) for date in sorted_dates] + [self.daily_count, 1])
        
        for i, date in enumerate(sorted_dates):
            y = y_start + (i * 22)
            
            # Date label (show day name or MM-DD)
            day_label = date[-5:] if len(date) > 5 else date
            if date == self.current_date:
                day_label += "*"  # Mark today
                count = self.daily_count
                bar_color = Color.GREEN
            else:
                count = self.weekly_data.get(date, 0)
                bar_color = Color.BLUE if count > 0 else Color.DARK_GRAY
                
            self.display.text(day_label, 10, y, Color.WHITE)
            
            # Count number
            count_text = str(count)
            self.display.text(count_text, 70, y, Color.WHITE)
            
            # Progress bar
            bar_width = int((count / max_count) * 100) if max_count > 0 else 0
            self.display.rect(90, y, 100, bar_height, Color.GRAY)
            if bar_width > 0:
                self.display.fill_rect(91, y + 1, bar_width, bar_height - 2, bar_color)
                
        # Weekly total
        week_total = sum([self.weekly_data.get(date, 0) for date in sorted_dates[:-1]]) + self.daily_count
        total_text = f"Week Total: {week_total}"
        total_x = (240 - len(total_text) * 8) // 2
        self.display.text(total_text, total_x, 200, Color.MAGENTA)
        
        # Instructions
        self.display.text("Y:Counter X:Stats B:Home", 20, 220, Color.GRAY)
        
    def draw_stats_view(self):
        """Draw statistics and insights"""
        # Title
        self.display.text("STATS & INSIGHTS", 45, 10, Color.YELLOW)
        
        # Calculate stats
        total_days = len(self.weekly_data) + (1 if self.daily_count > 0 else 0)
        week_total = sum([self.weekly_data.get(date, 0) for date in list(self.weekly_data.keys())[-7:]]) + self.daily_count
        week_avg = week_total / 7 if week_total > 0 else 0
        
        # All-time total
        all_time_total = self.total_count + sum(self.weekly_data.values()) + self.daily_count
        
        stats = [
            (f"Today: {self.daily_count}", Color.GREEN),
            (f"This Week: {week_total}", Color.BLUE), 
            (f"Daily Avg: {week_avg:.1f}", Color.CYAN),
            (f"All Time: {all_time_total}", Color.MAGENTA),
            (f"Days Tracked: {total_days}", Color.WHITE)
        ]
        
        # Draw stats
        y_pos = 45
        for stat, color in stats:
            stat_x = (240 - len(stat) * 8) // 2
            self.display.text(stat, stat_x, y_pos, color)
            y_pos += 20
            
        # Insights based on data
        if week_avg >= 5:
            insight = "Excellent habit!"
        elif week_avg >= 3:
            insight = "Great progress!"
        elif week_avg >= 1:
            insight = "Building the habit"
        else:
            insight = "Start small, stay consistent"
            
        # Draw insight
        insight_y = y_pos + 15
        insight_x = (240 - len(insight) * 8) // 2
        self.display.text(insight, insight_x, insight_y, Color.YELLOW)
        
        # Streak calculation (consecutive days with at least 1 gratitude)
        streak = self.calculate_streak()
        if streak > 0:
            streak_text = f"Streak: {streak} days"
            streak_x = (240 - len(streak_text) * 8) // 2
            self.display.text(streak_text, streak_x, insight_y + 20, Color.ORANGE)
        
        # Instructions
        self.display.text("Y:Counter X:Weekly B:Home", 15, 220, Color.GRAY)
        
    def draw_large_counter(self, number, x, y, color):
        """Draw large number for daily count"""
        # Center the number
        digit_width = 20
        total_width = len(number) * digit_width
        start_x = x - (total_width // 2)
        
        for i, digit in enumerate(number):
            digit_x = start_x + (i * digit_width)
            self.draw_large_digit(digit, digit_x, y, color)
            
    def draw_large_digit(self, digit, x, y, color):
        """Draw a large digit (5x7 blocks)"""
        # 5x7 patterns for digits 0-9
        patterns = {
            '0': [
                "11111",
                "10001", 
                "10001",
                "10001",
                "10001",
                "10001",
                "11111"
            ],
            '1': [
                "00100",
                "01100",
                "00100",
                "00100", 
                "00100",
                "00100",
                "11111"
            ],
            '2': [
                "11111",
                "00001",
                "00001", 
                "11111",
                "10000",
                "10000",
                "11111"
            ],
            '3': [
                "11111",
                "00001",
                "00001",
                "11111", 
                "00001",
                "00001",
                "11111"
            ],
            '4': [
                "10001",
                "10001",
                "10001",
                "11111",
                "00001",
                "00001", 
                "00001"
            ],
            '5': [
                "11111",
                "10000",
                "10000",
                "11111",
                "00001",
                "00001",
                "11111"
            ],
            '6': [
                "11111", 
                "10000",
                "10000",
                "11111",
                "10001",
                "10001",
                "11111"
            ],
            '7': [
                "11111",
                "00001",
                "00001",
                "00010",
                "00100",
                "01000",
                "10000"
            ],
            '8': [
                "11111",
                "10001",
                "10001", 
                "11111",
                "10001",
                "10001",
                "11111"
            ],
            '9': [
                "11111",
                "10001",
                "10001",
                "11111",
                "00001",
                "00001",
                "11111"
            ]
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
    
    def draw_progress_bar(self, current, maximum, x, y, width, height):
        """Draw a progress bar"""
        # Background
        self.display.rect(x, y, width, height, Color.GRAY)
        
        # Fill based on progress
        if maximum > 0:
            fill_width = int((current / maximum) * (width - 2))
            fill_width = min(fill_width, width - 2)  # Don't exceed bar
            
            if fill_width > 0:
                fill_color = Color.GREEN if current >= maximum else Color.BLUE
                self.display.fill_rect(x + 1, y + 1, fill_width, height - 2, fill_color)
                
    def get_daily_message(self):
        """Get encouraging message based on daily count"""
        if self.daily_count >= 10:
            return "Amazing gratitude!"
        elif self.daily_count >= 5:
            return "Wonderful day!"
        elif self.daily_count >= 3:
            return "Great progress!"
        elif self.daily_count >= 1:
            return "Good start!"
        else:
            return "Press A to count!"
            
    def calculate_streak(self):
        """Calculate consecutive days with at least 1 gratitude"""
        # Get recent dates in chronological order
        all_dates = list(self.weekly_data.keys())
        if self.daily_count > 0:
            all_dates.append(self.current_date)
            
        sorted_dates = sorted(all_dates, reverse=True)
        
        streak = 0
        for date in sorted_dates:
            if date == self.current_date:
                count = self.daily_count
            else:
                count = self.weekly_data.get(date, 0)
                
            if count > 0:
                streak += 1
            else:
                break
                
        return streak
        
    def update(self):
        """Update Gratitude Proxy app"""
        self.check_new_day()
        
        # Count gratitude
        if self.buttons.is_pressed('A'):
            if self.view_mode == "counter":
                self.daily_count += 1
                self.total_count += 1
                
                # Show feedback
                self.display.fill_rect(70, 90, 100, 25, Color.GREEN)
                self.display.text("Gratitude +1!", 80, 100, Color.BLACK)
                self.display.display()
                time.sleep_ms(600)
                
                self.draw_screen()
                time.sleep_ms(200)
                
        # Switch between views
        if self.buttons.is_pressed('Y'):
            if self.view_mode == "counter":
                self.view_mode = "weekly"
            elif self.view_mode == "weekly":
                self.view_mode = "counter"
            elif self.view_mode == "stats":
                self.view_mode = "counter"
            self.draw_screen()
            time.sleep_ms(200)
            
        if self.buttons.is_pressed('X'):
            if self.view_mode == "counter":
                self.view_mode = "stats"
            elif self.view_mode == "weekly":
                self.view_mode = "stats"
            elif self.view_mode == "stats":
                self.view_mode = "weekly"
            self.draw_screen()
            time.sleep_ms(200)
            
        # Check for exit
        if self.buttons.is_pressed('B'):
            return False
            
        return True
        
    def cleanup(self):
        """Cleanup when exiting app"""
        self.save_data()