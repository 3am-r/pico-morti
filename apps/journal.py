"""
Micro-Journal App - 3 words a day
Pick words from a curated list to describe your day
"""

import time
import os
from lib.st7789 import Color

class MicroJournal:
    def __init__(self, display, joystick, buttons):
        """Initialize the micro-journal app"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        # Word categories and options
        self.categories = {
            "Mood": ["happy", "calm", "tired", "excited", "anxious", "peaceful", "energetic", "thoughtful"],
            "Energy": ["high", "moderate", "low", "focused", "scattered", "steady", "variable", "depleted"],
            "Theme": ["productive", "creative", "social", "quiet", "challenging", "learning", "routine", "adventurous"]
        }
        
        self.selected_words = []
        self.current_category = 0
        self.current_word_index = 0
        self.csv_file = "/stores/journal.csv"
        
    def init(self):
        """Initialize app when opened"""
        self.selected_words = []
        self.current_category = 0
        self.current_word_index = 0
        self.draw_screen()
        
    def draw_screen(self):
        """Draw the journal screen"""
        self.display.fill(Color.BLACK)
        
        # Title
        title = "3 Words Today"
        title_x = (240 - len(title) * 8) // 2
        self.display.text(title, title_x, 10, Color.GREEN)
        
        # Show selected words at top
        y_pos = 35
        for i, word in enumerate(self.selected_words):
            text = f"{i+1}. {word}"
            self.display.text(text, 20, y_pos, Color.CYAN)
            y_pos += 15
            
        # Show current category
        if self.current_category < len(self.categories):
            cat_name = list(self.categories.keys())[self.current_category]
            cat_words = self.categories[cat_name]
            
            # Category title
            self.display.text(f"Choose {cat_name}:", 20, 90, Color.YELLOW)
            
            # Show word options in a grid
            words_per_row = 2
            word_y = 110
            
            for i, word in enumerate(cat_words):
                row = i // words_per_row
                col = i % words_per_row
                x = 20 + col * 100
                y = word_y + row * 20
                
                # Highlight selected word
                if i == self.current_word_index:
                    self.display.fill_rect(x - 2, y - 2, len(word) * 8 + 4, 12, Color.WHITE)
                    self.display.text(word, x, y, Color.BLACK)
                else:
                    self.display.text(word, x, y, Color.GRAY)
                    
        # Instructions
        if len(self.selected_words) < 3:
            self.display.text("Joy:Select A:Choose", 30, 215, Color.GRAY)
            self.display.text("B:Home", 90, 225, Color.GRAY)
        else:
            self.display.text("A:Save B:Home", 70, 220, Color.GRAY)
            
        self.display.display()
        
    def update(self):
        """Update journal app"""
        # Check if we've selected all 3 words
        if len(self.selected_words) >= 3:
            if self.buttons.is_pressed('A'):
                self.save_entry()
                return True  # Keep app running
                
        else:
            # Navigate words - use slow response like tamagotchi menu
            direction = self.joystick.get_direction_slow()
            if direction:
                cat_words = list(self.categories.values())[self.current_category]
                
                if direction == 'UP':
                    self.current_word_index = max(0, self.current_word_index - 2)
                elif direction == 'DOWN':
                    self.current_word_index = min(len(cat_words) - 1, self.current_word_index + 2)
                elif direction == 'LEFT':
                    if self.current_word_index % 2 == 1:
                        self.current_word_index -= 1
                elif direction == 'RIGHT':
                    if self.current_word_index % 2 == 0 and self.current_word_index < len(cat_words) - 1:
                        self.current_word_index += 1
                        
                self.draw_screen()
                
            # Select word
            if self.buttons.is_pressed('A'):
                cat_name = list(self.categories.keys())[self.current_category]
                cat_words = self.categories[cat_name]
                selected = cat_words[self.current_word_index]
                
                self.selected_words.append(selected)
                self.current_category += 1
                self.current_word_index = 0
                
                if self.current_category >= len(self.categories):
                    # All words selected
                    self.draw_complete_screen()
                else:
                    self.draw_screen()
                    
                time.sleep_ms(200)  # Debounce
                
        # Check for exit
        if self.buttons.is_pressed('B'):
            return False  # Exit app
            
        return True  # Keep running
        
    def draw_complete_screen(self):
        """Show completion screen"""
        self.display.fill(Color.BLACK)
        
        # Title
        title = "Today's Words"
        title_x = (240 - len(title) * 8) // 2
        self.display.text(title, title_x, 40, Color.GREEN)
        
        # Show selected words centered
        y_pos = 80
        for word in self.selected_words:
            x = (240 - len(word) * 8) // 2
            self.display.text(word, x, y_pos, Color.CYAN)
            y_pos += 25
            
        # Date
        try:
            import machine
            rtc = machine.RTC()
            date_tuple = rtc.datetime()
            date_str = f"{date_tuple[2]}/{date_tuple[1]}/{date_tuple[0]}"
        except:
            date_str = "Today"
            
        date_x = (240 - len(date_str) * 8) // 2
        self.display.text(date_str, date_x, 170, Color.YELLOW)
        
        # Instructions
        self.display.text("A:Save B:Home", 70, 220, Color.GRAY)
        
        self.display.display()
        
    def save_entry(self):
        """Save journal entry to CSV file"""
        try:
            # Get current date/time
            try:
                import machine
                rtc = machine.RTC()
                dt = rtc.datetime()
                date_str = f"{dt[0]}-{dt[1]:02d}-{dt[2]:02d}"
                time_str = f"{dt[4]:02d}:{dt[5]:02d}"
            except:
                date_str = "unknown"
                time_str = "unknown"
                
            # Create CSV line
            csv_line = f"{date_str},{time_str},{','.join(self.selected_words)}\n"
            
            # Append to file
            with open(self.csv_file, 'a') as f:
                f.write(csv_line)
                
            # Show success message
            self.display.fill(Color.BLACK)
            msg = "Saved!"
            x = (240 - len(msg) * 8) // 2
            self.display.text(msg, x, 110, Color.GREEN)
            self.display.display()
            time.sleep_ms(1000)
            
            # Reset for next entry
            self.init()
            
        except Exception as e:
            print(f"Save error: {e}")
            self.display.fill(Color.BLACK)
            self.display.text("Save failed!", 70, 110, Color.RED)
            self.display.display()
            time.sleep_ms(1000)
            self.draw_screen()
            
    def cleanup(self):
        """Cleanup when exiting app"""
        pass