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
        first_name = "Amr"  # Default values
        last_name = "Salem"
        
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
        x1 = (self.width - len(greeting) * 12) // 2  # 16 pixels wide for 2x text
        x2 = (self.width - len(greeting2) * 12) // 2
        
        # Animate greeting appearance with larger text
        for i in range(len(greeting)):
            # Clear previous text area
            self.display.fill_rect(x1, 70, len(greeting) * 8, 20, Color.BLACK)
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
        """Draw text at 2x size"""
        for i, char in enumerate(text):
            char_x = x + i * 16  # Each character is 16 pixels wide (2x8)
            
            # Draw character at 2x scale by drawing 4 pixels for each original pixel
            # This creates a simple 2x scaling effect
            for row in range(8):
                for col in range(8):
                    # Get pixel from original 8x8 font pattern
                    # Since we don't have access to the font data, we'll use rectangles
                    # to approximate larger text
                    pass
                    
            # Simplified approach: draw filled rectangles to form letters
            if char == 'Y':
                # Draw Y shape
                self.display.fill_rect(char_x, y, 4, 8, color)        # Left diagonal
                self.display.fill_rect(char_x + 12, y, 4, 8, color)   # Right diagonal  
                self.display.fill_rect(char_x + 4, y + 6, 8, 4, color) # Bottom stem
                self.display.fill_rect(char_x + 6, y + 10, 4, 6, color) # Bottom
            elif char == 'a':
                # Draw lowercase a
                self.display.fill_rect(char_x + 2, y + 4, 10, 4, color) # Top bar
                self.display.fill_rect(char_x + 2, y + 8, 4, 8, color)  # Left side
                self.display.fill_rect(char_x + 8, y + 8, 4, 8, color)  # Right side
                self.display.fill_rect(char_x + 2, y + 12, 10, 4, color) # Bottom bar
            elif char == 'A':
                # Draw uppercase A
                self.display.fill_rect(char_x + 6, y, 4, 16, color)     # Center stem
                self.display.fill_rect(char_x + 2, y + 4, 4, 12, color) # Left side
                self.display.fill_rect(char_x + 10, y + 4, 4, 12, color) # Right side
                self.display.fill_rect(char_x + 2, y + 8, 12, 4, color) # Cross bar
            elif char == 'm':
                # Draw lowercase m
                self.display.fill_rect(char_x, y + 4, 4, 12, color)     # Left stem
                self.display.fill_rect(char_x + 4, y + 4, 4, 8, color)  # First arch
                self.display.fill_rect(char_x + 8, y + 8, 4, 8, color)  # Center
                self.display.fill_rect(char_x + 12, y + 4, 4, 12, color) # Right stem
            elif char == 'r':
                # Draw lowercase r
                self.display.fill_rect(char_x, y + 4, 4, 12, color)     # Left stem
                self.display.fill_rect(char_x + 4, y + 4, 8, 4, color)  # Top bar
            elif char == 'S':
                # Draw uppercase S
                self.display.fill_rect(char_x + 2, y, 10, 4, color)     # Top
                self.display.fill_rect(char_x + 2, y + 6, 10, 4, color) # Middle
                self.display.fill_rect(char_x + 2, y + 12, 10, 4, color) # Bottom
                self.display.fill_rect(char_x, y + 4, 4, 4, color)      # Left middle
                self.display.fill_rect(char_x + 10, y + 8, 4, 4, color) # Right middle
            elif char == 'l':
                # Draw lowercase l
                self.display.fill_rect(char_x + 6, y, 4, 16, color)     # Stem
            elif char == 'e':
                # Draw lowercase e
                self.display.fill_rect(char_x + 2, y + 4, 10, 4, color) # Top
                self.display.fill_rect(char_x + 2, y + 8, 8, 4, color)  # Middle
                self.display.fill_rect(char_x + 2, y + 12, 10, 4, color) # Bottom
                self.display.fill_rect(char_x, y + 6, 4, 8, color)      # Left side
            elif char == ' ':
                # Space - do nothing
                pass
            else:
                # Default: draw a simple rectangle for unknown characters
                self.display.fill_rect(char_x + 2, y + 2, 12, 12, color)
                
    def draw_medium_text(self, text, x, y, color):
        """Draw text at 1.5x size (12px wide per char)"""
        for i, char in enumerate(text):
            char_x = x + i * 12  # Each character is 12 pixels wide
            
            if char == 'L':
                self.display.fill_rect(char_x, y, 3, 12, color)       # Stem
                self.display.fill_rect(char_x, y + 9, 9, 3, color)    # Bottom
            elif char == 'e':
                self.display.fill_rect(char_x + 1, y + 3, 8, 3, color)  # Top
                self.display.fill_rect(char_x + 1, y + 6, 6, 3, color)  # Middle
                self.display.fill_rect(char_x + 1, y + 9, 8, 3, color)  # Bottom
                self.display.fill_rect(char_x, y + 4, 3, 6, color)      # Left
            elif char == 't':
                self.display.fill_rect(char_x + 4, y, 3, 12, color)   # Stem
                self.display.fill_rect(char_x + 1, y + 3, 8, 3, color) # Cross
            elif char == '\'':
                self.display.fill_rect(char_x + 4, y, 2, 4, color)    # Apostrophe
            elif char == 's':
                self.display.fill_rect(char_x + 1, y + 3, 8, 3, color)  # Top
                self.display.fill_rect(char_x + 1, y + 6, 6, 3, color)  # Middle
                self.display.fill_rect(char_x + 1, y + 9, 8, 3, color)  # Bottom
            elif char == ' ':
                pass  # Space
            elif char == 'd':
                self.display.fill_rect(char_x + 7, y, 3, 12, color)   # Right stem
                self.display.fill_rect(char_x + 1, y + 3, 6, 3, color) # Top
                self.display.fill_rect(char_x + 1, y + 9, 6, 3, color) # Bottom  
                self.display.fill_rect(char_x, y + 6, 3, 3, color)     # Left middle
            elif char == 'o':
                self.display.fill_rect(char_x + 1, y + 3, 8, 3, color) # Top
                self.display.fill_rect(char_x + 1, y + 9, 8, 3, color) # Bottom
                self.display.fill_rect(char_x, y + 6, 3, 3, color)     # Left
                self.display.fill_rect(char_x + 7, y + 6, 3, 3, color) # Right
            elif char == 'i':
                self.display.fill_rect(char_x + 4, y + 3, 3, 9, color) # Stem
                self.display.fill_rect(char_x + 4, y, 3, 2, color)     # Dot
            elif char == '!':
                self.display.fill_rect(char_x + 4, y, 3, 8, color)     # Stem
                self.display.fill_rect(char_x + 4, y + 10, 3, 2, color) # Dot
            else:
                # Default
                self.display.fill_rect(char_x + 2, y + 2, 8, 8, color)
                
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
        
    def run(self, duration=3000):
        """
        Run the complete loading sequence
        
        Args:
            duration: Total duration in milliseconds
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