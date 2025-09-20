"""
Energy Dial - Focus/Energy Level Tracker
0-5 slider for current energy/focus level with intelligent action suggestions
"""

import time
from lib.st7789 import Color

class EnergyDial:
    def __init__(self, display, joystick, buttons):
        """Initialize Energy Dial app"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        # Current energy level (0-5)
        self.energy_level = 3  # start at neutral
        self.last_update_time = time.ticks_ms()
        
        # Action suggestions based on energy level
        self.action_suggestions = {
            0: ["Take a nap", "Eat something", "Go for a walk", "Deep breathing"],
            1: ["Light stretching", "Easy reading", "Organize desk", "Listen to music"],
            2: ["Check emails", "Plan tomorrow", "Light tasks", "Tidy up"],
            3: ["Moderate work", "Review notes", "Creative tasks", "Call someone"],
            4: ["Deep work", "Hard problems", "Writing", "Learning new"],
            5: ["Tackle big project", "Complex analysis", "Creative flow", "Peak performance"]
        }
        
        # Energy level descriptions
        self.energy_descriptions = {
            0: "Exhausted",
            1: "Very Low",
            2: "Low",
            3: "Moderate",
            4: "High",
            5: "Peak Energy"
        }
        
        # Load saved energy level
        self.load_data()
        
    def init(self):
        """Initialize app when opened"""
        self.draw_screen()
        
    def load_data(self):
        """Load saved energy level"""
        try:
            with open("energy_dial.dat", "r") as f:
                line = f.readline().strip()
                if line:
                    parts = line.split(",")
                    if len(parts) >= 2:
                        self.energy_level = max(0, min(5, int(parts[0])))
                        # Could load timestamp here if needed
        except:
            # Default to moderate energy
            self.energy_level = 3
            
    def save_data(self):
        """Save current energy level"""
        try:
            with open("energy_dial.dat", "w") as f:
                f.write(f"{self.energy_level},{time.ticks_ms()}\n")
        except Exception as e:
            print(f"Save error: {e}")
            
    def draw_screen(self):
        """Draw the energy dial interface"""
        self.display.fill(Color.BLACK)
        
        # Title
        title = "ENERGY DIAL"
        title_x = (240 - len(title) * 8) // 2
        self.display.text(title, title_x, 10, Color.CYAN)
        
        # Current energy level display
        current_desc = self.energy_descriptions[self.energy_level]
        desc_x = (240 - len(current_desc) * 8) // 2
        level_color = self.get_energy_color(self.energy_level)
        self.display.text(current_desc, desc_x, 30, level_color)
        
        # Draw energy dial (horizontal slider)
        self.draw_energy_slider()
        
        # Show current action suggestion
        self.draw_action_suggestion()
        
        # Instructions
        self.display.text("Joy:Adjust A:Log B:Home", 30, 205, Color.GRAY)
        self.display.text("Y:History", 90, 220, Color.GRAY)
        
        self.display.display()
        
    def draw_energy_slider(self):
        """Draw the energy level slider (0-5)"""
        # Slider background
        slider_width = 180
        slider_height = 20
        slider_x = (240 - slider_width) // 2
        slider_y = 60
        
        # Background bar
        self.display.rect(slider_x, slider_y, slider_width, slider_height, Color.WHITE)
        self.display.fill_rect(slider_x + 1, slider_y + 1, slider_width - 2, slider_height - 2, Color.DARK_GRAY)
        
        # Energy level segments (0-5 = 6 segments)
        segment_width = (slider_width - 2) // 6
        
        for i in range(6):
            seg_x = slider_x + 1 + (i * segment_width)
            seg_color = self.get_energy_color(i) if i <= self.energy_level else Color.DARK_GRAY
            
            # Fill segment if at or below current level
            if i <= self.energy_level:
                self.display.fill_rect(seg_x, slider_y + 1, segment_width - 1, slider_height - 2, seg_color)
            
            # Draw segment border
            self.display.rect(seg_x, slider_y + 1, segment_width, slider_height - 2, Color.GRAY)
        
        # Current level indicator (triangle pointer)
        indicator_x = slider_x + 1 + (self.energy_level * segment_width) + (segment_width // 2)
        self.draw_triangle_pointer(indicator_x, slider_y - 8, Color.WHITE)
        
        # Level numbers
        for i in range(6):
            num_x = slider_x + (i * segment_width) + (segment_width // 2) + 5
            self.display.text(str(i), num_x, slider_y + 25, Color.GRAY)
            
    def draw_triangle_pointer(self, x, y, color):
        """Draw a small triangle pointer"""
        # Simple triangle pointing down
        self.display.pixel(x, y, color)
        self.display.pixel(x - 1, y + 1, color)
        self.display.pixel(x, y + 1, color)
        self.display.pixel(x + 1, y + 1, color)
        self.display.pixel(x - 2, y + 2, color)
        self.display.pixel(x - 1, y + 2, color)
        self.display.pixel(x, y + 2, color)
        self.display.pixel(x + 1, y + 2, color)
        self.display.pixel(x + 2, y + 2, color)
        
    def draw_action_suggestion(self):
        """Draw suggested action based on current energy level"""
        suggestions = self.action_suggestions[self.energy_level]
        
        # Pick suggestion based on time of day (simple rotation)
        suggestion_index = (time.ticks_ms() // 10000) % len(suggestions)
        current_suggestion = suggestions[suggestion_index]
        
        # Suggestion header
        header = "Suggested Action:"
        header_x = (240 - len(header) * 8) // 2
        self.display.text(header, header_x, 120, Color.YELLOW)
        
        # Suggestion text (may need to wrap)
        if len(current_suggestion) <= 20:
            # Single line
            sug_x = (240 - len(current_suggestion) * 8) // 2
            self.display.text(current_suggestion, sug_x, 140, Color.WHITE)
        else:
            # Split into two lines
            mid_point = len(current_suggestion) // 2
            # Find a good break point near the middle
            break_point = mid_point
            for i in range(mid_point - 5, mid_point + 6):
                if i < len(current_suggestion) and current_suggestion[i] == ' ':
                    break_point = i
                    break
                    
            line1 = current_suggestion[:break_point].strip()
            line2 = current_suggestion[break_point:].strip()
            
            line1_x = (240 - len(line1) * 8) // 2
            line2_x = (240 - len(line2) * 8) // 2
            
            self.display.text(line1, line1_x, 135, Color.WHITE)
            self.display.text(line2, line2_x, 150, Color.WHITE)
            
        # Energy level as big number
        level_str = str(self.energy_level)
        level_color = self.get_energy_color(self.energy_level)
        
        # Draw large number (3x scale approximation)
        self.draw_large_number(level_str, 200, 170, level_color)
        
    def draw_large_number(self, number, x, y, color):
        """Draw a large version of a number"""
        # Simple 3x3 block representation of numbers 0-5
        patterns = {
            '0': [[1,1,1],[1,0,1],[1,0,1],[1,0,1],[1,1,1]],
            '1': [[0,1,0],[1,1,0],[0,1,0],[0,1,0],[1,1,1]],
            '2': [[1,1,1],[0,0,1],[1,1,1],[1,0,0],[1,1,1]],
            '3': [[1,1,1],[0,0,1],[1,1,1],[0,0,1],[1,1,1]],
            '4': [[1,0,1],[1,0,1],[1,1,1],[0,0,1],[0,0,1]],
            '5': [[1,1,1],[1,0,0],[1,1,1],[0,0,1],[1,1,1]]
        }
        
        if number in patterns:
            pattern = patterns[number]
            block_size = 3
            for row in range(5):
                for col in range(3):
                    if pattern[row][col]:
                        self.display.fill_rect(
                            x + col * block_size, 
                            y + row * block_size, 
                            block_size - 1, 
                            block_size - 1, 
                            color
                        )
    
    def get_energy_color(self, level):
        """Get color for energy level"""
        colors = {
            0: Color.RED,      # Exhausted
            1: Color.ORANGE,   # Very Low  
            2: Color.YELLOW,   # Low
            3: Color.BLUE,     # Moderate
            4: Color.GREEN,    # High
            5: Color.MAGENTA   # Peak
        }
        return colors.get(level, Color.WHITE)
        
    def show_history(self):
        """Show energy level history/trends"""
        self.display.fill(Color.BLACK)
        
        # Title
        self.display.text("ENERGY TRENDS", 60, 10, Color.CYAN)
        
        # Simple placeholder - could be enhanced with actual data tracking
        self.display.text("Today's Readings:", 20, 40, Color.YELLOW)
        
        # Mock some trend data
        times = ["Morning", "Midday", "Evening"]
        readings = [4, 3, 2]  # Example readings
        
        y_pos = 65
        for i, (time_str, reading) in enumerate(zip(times, readings)):
            color = self.get_energy_color(reading)
            self.display.text(f"{time_str}: {reading}", 30, y_pos, Color.WHITE)
            
            # Draw mini bar
            bar_x = 150
            bar_width = reading * 10  # 10px per level
            self.display.rect(bar_x, y_pos, 50, 10, Color.GRAY)
            self.display.fill_rect(bar_x + 1, y_pos + 1, bar_width, 8, color)
            
            y_pos += 25
            
        # Average
        avg = sum(readings) / len(readings)
        self.display.text(f"Average: {avg:.1f}", 30, y_pos + 20, Color.GREEN)
        
        # Tips based on trends
        if avg < 2.5:
            tip = "Consider more breaks!"
        elif avg > 4:
            tip = "Great energy today!"
        else:
            tip = "Balanced energy levels"
            
        self.display.text(tip, 20, y_pos + 45, Color.YELLOW)
        
        self.display.text("Press any button", 50, 200, Color.GRAY)
        self.display.display()
        
        # Wait for button press
        while not any([self.buttons.is_pressed(b) for b in ['A', 'B', 'X', 'Y']]):
            time.sleep_ms(50)
    
    def update(self):
        """Update Energy Dial app"""
        # Handle joystick for energy level adjustment
        direction = self.joystick.get_direction_slow()
        
        if direction == 'LEFT':
            if self.energy_level > 0:
                self.energy_level -= 1
                self.draw_screen()
                time.sleep_ms(200)
        elif direction == 'RIGHT':
            if self.energy_level < 5:
                self.energy_level += 1
                self.draw_screen()
                time.sleep_ms(200)
                
        # Log current energy level
        if self.buttons.is_pressed('A'):
            self.save_data()
            # Show confirmation
            self.display.fill_rect(50, 100, 140, 30, Color.GREEN)
            self.display.text("Energy Logged!", 70, 110, Color.BLACK)
            self.display.display()
            time.sleep_ms(800)
            self.draw_screen()
            
        # Show history
        if self.buttons.is_pressed('Y'):
            self.show_history()
            self.draw_screen()
            time.sleep_ms(200)
            
        # Check for exit
        if self.buttons.is_pressed('B'):
            return False
            
        return True
        
    def cleanup(self):
        """Cleanup when exiting app"""
        self.save_data()