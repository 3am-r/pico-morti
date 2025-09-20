"""
Activity Tracker - Track daily activities
Did you read? Write? Get bored? Do something new?
"""

import time
from lib.st7789 import Color

class ActivityTracker:
    def __init__(self, display, joystick, buttons):
        """Initialize activity tracker"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        # Activities to track
        self.activities = [
            {"name": "Read", "icon": "R", "color": Color.CYAN, "question": "Did you read today?"},
            {"name": "Write", "icon": "W", "color": Color.GREEN, "question": "Did you write today?"},
            {"name": "Bored", "icon": "B", "color": Color.ORANGE, "question": "Did you get bored?"},
            {"name": "New", "icon": "N", "color": Color.MAGENTA, "question": "Try something new?"}
        ]
        
        # Daily tracking data
        self.today_data = {}
        self.selected_activity = 0
        self.view_mode = "track"  # "track" or "stats"
        
        # Load today's data
        self.load_today_data()
        
    def init(self):
        """Initialize app when opened"""
        self.selected_activity = 0
        self.view_mode = "track"
        self.load_today_data()
        self.draw_screen()
        
    def get_date_string(self):
        """Get current date as string"""
        try:
            import machine
            rtc = machine.RTC()
            dt = rtc.datetime()
            return f"{dt[0]}-{dt[1]:02d}-{dt[2]:02d}"
        except:
            return "today"
            
    def load_today_data(self):
        """Load today's tracking data"""
        date_str = self.get_date_string()
        self.today_data = {}
        
        try:
            with open("tracker.dat", "r") as f:
                lines = f.readlines()
                for line in lines:
                    parts = line.strip().split(",")
                    if len(parts) == 3 and parts[0] == date_str:
                        self.today_data[parts[1]] = parts[2] == "True"
        except:
            # Initialize empty data for today
            for activity in self.activities:
                self.today_data[activity['name']] = False
                
    def save_data(self):
        """Save tracking data"""
        date_str = self.get_date_string()
        
        # Read existing data
        all_data = []
        try:
            with open("tracker.dat", "r") as f:
                for line in f:
                    parts = line.strip().split(",")
                    # Skip today's data (we'll write new)
                    if len(parts) == 3 and parts[0] != date_str:
                        all_data.append(line.strip())
        except:
            pass
            
        # Add today's data
        for name, value in self.today_data.items():
            all_data.append(f"{date_str},{name},{value}")
            
        # Write all data
        try:
            with open("tracker.dat", "w") as f:
                for line in all_data:
                    f.write(line + "\n")
        except Exception as e:
            print(f"Save error: {e}")
            
    def draw_screen(self):
        """Draw the tracker screen"""
        self.display.fill(Color.BLACK)
        
        if self.view_mode == "track":
            self.draw_tracking_view()
        else:
            self.draw_stats_view()
            
        self.display.display()
        
    def draw_tracking_view(self):
        """Draw the main tracking view"""
        # Title with date
        date_str = self.get_date_string()
        title = "Daily Track"
        title_x = (240 - len(title) * 8) // 2
        self.display.text(title, title_x, 10, Color.YELLOW)
        self.display.text(date_str, 80, 25, Color.GRAY)
        
        # Draw activity grid (2x2) - rectangles with half height
        grid_width = 70   # Same width
        grid_height = 35  # Half height (70/2)
        padding_x = 20    # Horizontal padding
        padding_y = 12    # Reduced vertical padding
        start_x = (240 - (grid_width * 2 + padding_x)) // 2
        start_y = 55
        
        for i, activity in enumerate(self.activities):
            row = i // 2
            col = i % 2
            x = start_x + col * (grid_width + padding_x)
            y = start_y + row * (grid_height + padding_y)
            
            # Highlight selected
            if i == self.selected_activity:
                self.display.fill_rect(x - 3, y - 3, grid_width + 6, grid_height + 6, Color.WHITE)
                self.display.fill_rect(x - 1, y - 1, grid_width + 2, grid_height + 2, Color.BLACK)
                
            # Activity rectangle
            is_done = self.today_data.get(activity['name'], False)
            box_color = activity['color'] if is_done else Color.DARK_GRAY
            
            self.display.rect(x, y, grid_width, grid_height, box_color)
            
            if is_done:
                # Filled rectangle with checkmark
                self.display.fill_rect(x + 1, y + 1, grid_width - 2, grid_height - 2, box_color)
                # Draw checkmark (smaller for rectangle)
                self.draw_small_checkmark(x + grid_width // 2, y + grid_height // 2, Color.BLACK)
            else:
                # Empty rectangle
                pass
                
            # Activity name - centered in the rectangle
            name_x = x + (grid_width - len(activity['name']) * 8) // 2
            name_y = y + (grid_height - 8) // 2  # Center vertically in rectangle
            text_color = Color.WHITE if is_done else activity['color']
            self.display.text(activity['name'], name_x, name_y, text_color)
            
        # Current question - moved up to give more space
        current_activity = self.activities[self.selected_activity]
        question = current_activity['question']
        q_x = (240 - len(question) * 8) // 2
        self.display.text(question, q_x, 185, current_activity['color'])
        
        # Instructions - moved up accordingly
        self.display.text("Joy:Nav A:Toggle Y:Stats", 15, 205, Color.GRAY)
        self.display.text("B:Home", 90, 220, Color.GRAY)
        
    def draw_checkmark(self, x, y, color):
        """Draw a checkmark at position"""
        # Simple checkmark shape
        points = [
            (x - 10, y),
            (x - 5, y + 5),
            (x + 10, y - 10)
        ]
        
        for i in range(len(points) - 1):
            self.display.line(points[i][0], points[i][1], 
                            points[i+1][0], points[i+1][1], color)
        # Make it thicker
        for i in range(len(points) - 1):
            self.display.line(points[i][0], points[i][1] + 1, 
                            points[i+1][0], points[i+1][1] + 1, color)
            
    def draw_small_checkmark(self, x, y, color):
        """Draw a smaller checkmark for rectangles"""
        # Smaller checkmark shape for rectangle format
        points = [
            (x - 6, y),
            (x - 2, y + 3),
            (x + 6, y - 4)
        ]
        
        for i in range(len(points) - 1):
            self.display.line(points[i][0], points[i][1], 
                            points[i+1][0], points[i+1][1], color)
        # Make it thicker
        for i in range(len(points) - 1):
            self.display.line(points[i][0], points[i][1] + 1, 
                            points[i+1][0], points[i+1][1] + 1, color)
            
    def draw_stats_view(self):
        """Draw statistics view"""
        # Title
        title = "Activity Stats"
        title_x = (240 - len(title) * 8) // 2
        self.display.text(title, title_x, 10, Color.CYAN)
        
        # Calculate streaks and stats
        stats = self.calculate_stats()
        
        y_pos = 40
        for activity in self.activities:
            name = activity['name']
            streak = stats.get(name, {}).get('streak', 0)
            total = stats.get(name, {}).get('total', 0)
            
            # Activity name
            self.display.text(name, 20, y_pos, activity['color'])
            
            # Streak
            streak_text = f"Streak: {streak}"
            self.display.text(streak_text, 100, y_pos, Color.WHITE)
            
            # Total
            total_text = f"Total: {total}"
            self.display.text(total_text, 100, y_pos + 15, Color.GRAY)
            
            y_pos += 40
            
        # Instructions
        self.display.text("Y:Back B:Home", 65, 220, Color.GRAY)
        
    def calculate_stats(self):
        """Calculate activity statistics"""
        stats = {}
        
        try:
            with open("tracker.dat", "r") as f:
                data = {}
                for line in f:
                    parts = line.strip().split(",")
                    if len(parts) == 3:
                        date = parts[0]
                        activity = parts[1]
                        value = parts[2] == "True"
                        
                        if activity not in data:
                            data[activity] = {}
                        data[activity][date] = value
                        
            # Calculate streaks and totals
            for activity in self.activities:
                name = activity['name']
                if name in data:
                    dates = sorted(data[name].keys(), reverse=True)
                    
                    # Calculate streak
                    streak = 0
                    for date in dates:
                        if data[name][date]:
                            streak += 1
                        else:
                            break
                            
                    # Calculate total
                    total = sum(1 for v in data[name].values() if v)
                    
                    stats[name] = {'streak': streak, 'total': total}
                else:
                    stats[name] = {'streak': 0, 'total': 0}
                    
        except:
            pass
            
        return stats
        
    def update(self):
        """Update tracker app"""
        if self.view_mode == "track":
            # Navigation - use slow response like tamagotchi menu
            direction = self.joystick.get_direction_slow()
            
            if direction == 'UP':
                if self.selected_activity >= 2:
                    self.selected_activity -= 2
                    self.draw_screen()
            elif direction == 'DOWN':
                if self.selected_activity < 2:
                    self.selected_activity += 2
                    self.draw_screen()
            elif direction == 'LEFT':
                if self.selected_activity % 2 == 1:
                    self.selected_activity -= 1
                    self.draw_screen()
            elif direction == 'RIGHT':
                if self.selected_activity % 2 == 0 and self.selected_activity < 3:
                    self.selected_activity += 1
                    self.draw_screen()
                    
            # Toggle activity
            if self.buttons.is_pressed('A'):
                activity_name = self.activities[self.selected_activity]['name']
                self.today_data[activity_name] = not self.today_data.get(activity_name, False)
                self.save_data()
                self.draw_screen()
                
                # Show feedback
                if self.today_data[activity_name]:
                    self.show_encouragement()
                    
                time.sleep_ms(200)
                
            # Switch to stats view
            if self.buttons.is_pressed('Y'):
                self.view_mode = "stats"
                self.draw_screen()
                time.sleep_ms(200)
                
        else:  # Stats view
            # Return to tracking
            if self.buttons.is_pressed('Y'):
                self.view_mode = "track"
                self.draw_screen()
                time.sleep_ms(200)
                
        # Check for exit
        if self.buttons.is_pressed('B'):
            return False
            
        return True
        
    def show_encouragement(self):
        """Show encouraging message when activity is completed"""
        messages = [
            "Great job!",
            "Keep it up!",
            "Awesome!",
            "Well done!",
            "Nice work!"
        ]
        
        import random
        msg = random.choice(messages)
        
        # Draw message overlay
        x = (240 - len(msg) * 8) // 2
        y = 120
        
        # Background box
        self.display.fill_rect(x - 10, y - 5, len(msg) * 8 + 20, 20, Color.GREEN)
        self.display.text(msg, x, y, Color.BLACK)
        self.display.display()
        
        time.sleep_ms(500)
        
    def cleanup(self):
        """Cleanup when exiting app"""
        self.save_data()