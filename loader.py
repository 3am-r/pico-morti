"""
Loading screen with greeting for Amr
"""

import time
import random
from lib.st7789 import ST7789, Color

class Loader:
    def __init__(self, display):
        """
        Initialize loader with display
        
        Args:
            display: ST7789 display instance
        """
        self.display = display
        self.width = display.width
        self.height = display.height
    
    def load_names_from_config(self):
        """Load first name and last name from config.txt"""
        first_name = "Awesom"  # Default values
        last_name = "Gorgeous"
        
        try:
            with open("config.txt", "r") as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("FIRST_NAME="):
                        first_name = line.split("=", 1)[1].strip()
                    elif line.startswith("LAST_NAME="):
                        last_name = line.split("=", 1)[1].strip()
        except OSError:
            # If config file doesn't exist, use defaults
            pass
        
        return first_name, last_name
        
    def show_greeting(self):
        """Show personalized greeting"""
        # Clear screen with dark background
        self.display.fill(Color.BLACK)
        
        # Draw decorative border
        self.draw_border()
        
        # Main greeting - centered with larger text (loaded from config)
        first_name, last_name = self.load_names_from_config()
        greeting = f"Ya {first_name}"
        greeting2 = f"Ya {last_name}"
        
        # Calculate positions for 2x sized text
        x1 = (self.width - len(greeting) * 16) // 2  # 16 pixels wide for 2x text
        x2 = (self.width - len(greeting2) * 16) // 2
        
        # Animate greeting appearance with larger text
        for i in range(len(greeting)):
            # Clear previous text area
            self.display.fill_rect(x1, 70, len(greeting) * 16, 20, Color.BLACK)
            self.draw_large_text(greeting[:i+1], x1, 75, Color.CYAN)
            self.display.display()
            time.sleep_ms(150)
            
        time.sleep_ms(300)
        
        for i in range(len(greeting2)):
            # Clear previous text area
            self.display.fill_rect(x2, 95, len(greeting2) * 16, 20, Color.BLACK)
            self.draw_large_text(greeting2[:i+1], x2, 100, Color.GREEN)
            self.display.display()
            time.sleep_ms(150)
            
        time.sleep_ms(300)
        
        # Add motivational text - also larger
        msg = "Let's do it!"
        x3 = (self.width - len(msg) * 12) // 2  # Smaller than main greeting but bigger than default
        self.draw_medium_text(msg, x3, 125, Color.YELLOW)
        
        # Draw progress bar
        self.draw_progress_bar()
        
        self.display.display()
        
    def draw_large_text(self, text, x, y, color):
        """Draw text at 2x size by drawing each character in a scaled pattern"""
        char_width = 16  # 2x normal character width for spacing
        
        for i, char in enumerate(text):
            char_x = x + i * char_width
            
            # Draw each character in a 2x2 grid to create actual scaling
            for row in range(2):
                for col in range(2):
                    # Offset each character copy to create a solid scaled appearance
                    offset_x = char_x + col
                    offset_y = y + row
                    self.display.text(char, offset_x, offset_y, color)
                
    def draw_medium_text(self, text, x, y, color):
        """Draw text at 1.5x size using display's text method"""
        char_width = 12  # 1.5x normal character width for spacing
        for i, char in enumerate(text):
            char_x = x + i * char_width
            # Draw character with slight scaling for medium size
            self.display.text(char, char_x, y, color)
            self.display.text(char, char_x + 1, y, color)
                
    def draw_border(self):
        """Draw decorative border"""
        # Top and bottom borders
        for i in range(0, self.width, 10):
            self.display.fill_rect(i, 0, 8, 3, Color.PURPLE)
            self.display.fill_rect(i, self.height - 3, 8, 3, Color.PURPLE)
            
        # Left and right borders
        for i in range(0, self.height, 10):
            self.display.fill_rect(0, i, 3, 8, Color.PURPLE)
            self.display.fill_rect(self.width - 3, i, 3, 8, Color.PURPLE)
            
    def draw_progress_bar(self):
        """Animate a loading progress bar"""
        bar_width = 180
        bar_height = 10
        bar_x = (self.width - bar_width) // 2
        bar_y = 170
        
        # Draw progress bar border
        self.display.rect(bar_x - 2, bar_y - 2, bar_width + 4, bar_height + 4, Color.WHITE)
        
        # Animate filling
        for i in range(bar_width):
            self.display.fill_rect(bar_x + i, bar_y, 1, bar_height, Color.GREEN)
            if i % 10 == 0:
                self.display.display()
                time.sleep_ms(20)
                
    def show_loading_animation(self):
        """Show a simple loading animation"""
        center_x = self.width // 2
        center_y = self.height // 2
        
        # Clear screen
        self.display.fill(Color.BLACK)
        
        # Draw loading text
        loading_text = "Loading..."
        text_x = (self.width - len(loading_text) * 8) // 2
        self.display.text(loading_text, text_x, center_y + 30, Color.WHITE)
        
        # Animated dots
        radius = 20
        num_dots = 8
        
        for frame in range(30):
            # Clear previous dots area
            self.display.fill_rect(center_x - 30, center_y - 30, 60, 60, Color.BLACK)
            
            for i in range(num_dots):
                angle = (360 / num_dots) * i + frame * 10
                x = center_x + int(radius * self.cos_approx(angle))
                y = center_y + int(radius * self.sin_approx(angle))
                
                # Vary dot size based on position
                size = 3 if i == (frame // 3) % num_dots else 2
                color = Color.CYAN if i == (frame // 3) % num_dots else Color.GRAY
                self.display.fill_circle(x, y, size, color)
                
            self.display.display()
            time.sleep_ms(50)
            
    def cos_approx(self, degrees):
        """Approximate cosine for animation"""
        import math
        return math.cos(math.radians(degrees))
        
    def sin_approx(self, degrees):
        """Approximate sine for animation"""
        import math
        return math.sin(math.radians(degrees))
        
    def show_tips(self):
        """Show usage tips during loading"""
        tips = [
            "Fix bedtime and wake-up time",
            "Eat balanced, drink plenty",
            "Divide largers into smallers",
            "Minimize distractions"
        ]
        
        self.display.fill(Color.BLACK)
        
        # Title
        title = "Quick Tips"
        title_x = (self.width - len(title) * 8) // 2
        self.display.text(title, title_x, 30, Color.YELLOW)
        
        # Show tips
        y_pos = 60
        for tip in tips:
            # Center each tip
            x = (self.width - len(tip) * 8) // 2
            self.display.text(tip, x, y_pos, Color.WHITE)
            y_pos += 25
            
        self.display.display()
        time.sleep_ms(2000)
        
    def run(self):
        """
        Run the complete loading sequence
        """
        # Show greeting first
        self.show_greeting()
        time.sleep_ms(1500)
        
        # Show tips
        self.show_tips()
        
        # Show loading animation
        self.show_loading_animation()
        
        # Clear for main app
        self.display.fill(Color.BLACK)
        self.display.display()