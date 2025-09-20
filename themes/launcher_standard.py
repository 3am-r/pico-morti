"""
Standard Launcher - Classic grid-based application launcher
Traditional home screen layout with improved grid layouts
"""

import time
import sys
sys.path.append('..')  # Add parent directory to access app_info
from lib.st7789 import Color
from launcher_utils import LauncherUtils
from app_info import AppInfo

class StandardLauncher:
    """Traditional grid-based launcher with classic UX"""
    
    def __init__(self, apps, display, joystick, buttons):
        self.apps = apps
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        # Launcher state
        self.current_app_index = 0
        
    def init(self):
        """Initialize standard launcher"""
        self.current_app_index = 0
        self.draw_screen()
        
    def draw_screen(self):
        """Draw the standard launcher interface"""
        self.display.fill(Color.BLACK)
        self.draw_menu()
        self.display.display()
        
    def draw_menu(self):
        """Draw main menu with app grid - original working layout"""
        num_apps = len(self.apps)
        
        # Enhanced grid layout logic for better scaling (from backup)
        if num_apps <= 6:
            # 2x3 layout for 1-6 apps 
            cols = 2
            rows = 3
            icon_width = 100
            icon_height = 45
            padding_x = 15
            padding_y = 5
        elif num_apps <= 8:
            # 2x4 layout for 7-8 apps
            cols = 2
            rows = 4
            icon_width = 75
            icon_height = 40
            padding_x = 12
            padding_y = 3
        elif num_apps <= 9:
            # 3x3 layout for 9 apps
            cols = 3
            rows = 3
            icon_width = 65
            icon_height = 35
            padding_x = 8
            padding_y = 3
        else:
            # 3x4 layout for 10+ apps (compact)
            cols = 3
            rows = 4
            icon_width = 60
            icon_height = 30
            padding_x = 6
            padding_y = 2
            
        start_x = (240 - (icon_width * cols + padding_x * (cols - 1))) // 2
        start_y = 25
        
        # Get app info from centralized registry
        app_info = AppInfo.get_app_list_for_standard_launcher()
        
        for i, (name, color) in enumerate(app_info):
            if i >= num_apps:  # Don't draw more apps than we have
                break
                
            row = i // cols
            col = i % cols
            x = start_x + col * (icon_width + padding_x)
            y = start_y + row * (icon_height + padding_y)
            
            # Highlight selected app
            if i == self.current_app_index:
                self.display.fill_rect(x - 3, y - 3, icon_width + 6, icon_height + 6, Color.WHITE)
                self.display.fill_rect(x - 1, y - 1, icon_width + 2, icon_height + 2, Color.BLACK)
            
            # Draw app rectangle
            self.display.rect(x, y, icon_width, icon_height, color)
            self.display.fill_rect(x + 1, y + 1, icon_width - 2, icon_height - 2, color)
            
            # Draw app name - centered in the rectangle
            name_x = x + (icon_width - len(name) * 8) // 2
            name_y = y + (icon_height - 8) // 2  # Center vertically in rectangle
            self.display.text(name, name_x, name_y, Color.BLACK)
        
        # Instructions - positioned based on grid end
        grid_end_y = start_y + (rows * icon_height) + ((rows - 1) * padding_y)
        instruction_y = grid_end_y + 40  # Original spacing
        
        self.display.text("Joystick:Move A:Open", 30, instruction_y, Color.GRAY)
        self.display.text("B:Sleep Hold:Exit", 60, instruction_y + 15, Color.GRAY)
        
    def handle_input(self):
        """Handle input in standard launcher"""
        # Update input devices
        self.buttons.update()
        
        # Enhanced joystick navigation - adaptive for current layout
        moved = False
        num_apps = len(self.apps)
        
        # Determine current grid layout (same logic as draw_menu)
        if num_apps <= 6:
            cols = 2
        elif num_apps <= 8:
            cols = 2
        elif num_apps <= 9:
            cols = 3
        else:
            cols = 3
        
        # Universal navigation that works for any grid layout (from backup)
        if not self.joystick.right_pin.value() and not moved:
            if self.current_app_index % cols < cols - 1:  # Not in rightmost column
                if self.current_app_index < num_apps - 1:  # Not the last app
                    self.current_app_index += 1
                    moved = True
        elif not self.joystick.left_pin.value() and not moved:
            if self.current_app_index % cols > 0:  # Not in leftmost column
                self.current_app_index -= 1
                moved = True
        elif not self.joystick.down_pin.value() and not moved:
            if self.current_app_index < num_apps - cols:  # Not in bottom row
                self.current_app_index += cols
                moved = True
        elif not self.joystick.up_pin.value() and not moved:
            if self.current_app_index >= cols:  # Not in top row
                self.current_app_index -= cols
                moved = True
        
        if moved:
            # Keep index in bounds for current number of apps
            self.current_app_index = max(0, min(num_apps - 1, self.current_app_index))
            self.draw_screen()
            time.sleep_ms(150)  # Simple debounce after movement
            
        # Button A - Open app
        if self.buttons.is_pressed('A'):
            app = self.apps[self.current_app_index]
            LauncherUtils.log_app_usage(app.__class__.__name__)
            return ("launch_app", app)
            
        # Button B - Sleep mode (simple press detection)
        if self.buttons.is_pressed('B'):
            return "sleep"
            
        return "continue"