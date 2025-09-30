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
        
        # Launcher state - 5 rows x 3 columns grid
        self.current_app_index = 0
        self.scroll_offset = 0
        self.grid_cols = 3
        self.grid_rows = 5
        self.apps_per_page = self.grid_cols * self.grid_rows  # 15 apps per page
        
    def init(self):
        """Initialize standard launcher"""
        self.current_app_index = 0
        self.scroll_offset = 0
        self.draw_screen()
        
    def draw_screen(self):
        """Draw the standard launcher interface"""
        self.display.fill(Color.BLACK)
        self.draw_menu()
        self.display.display()
        
    def draw_menu(self):
        """Draw 5x3 grid with infinite scroll"""
        num_apps = len(self.apps)

        # Fixed 5 rows x 3 columns layout
        cols = self.grid_cols
        rows = self.grid_rows

        # Calculate icon dimensions to fit 5x3 grid
        available_width = self.display.width - 20  # 10px margin on each side
        available_height = self.display.height - 80  # Leave room for instructions

        icon_width = (available_width - (cols - 1) * 8) // cols  # 8px padding between cols
        icon_height = (available_height - (rows - 1) * 6) // rows  # 6px padding between rows

        padding_x = 8
        padding_y = 6

        start_x = (self.display.width - (icon_width * cols + padding_x * (cols - 1))) // 2
        start_y = 15

        # Calculate which apps to show based on scroll offset
        visible_start = self.scroll_offset
        visible_end = min(visible_start + self.apps_per_page, num_apps)

        # Draw visible apps in grid
        grid_position = 0
        for app_index in range(visible_start, visible_end):
            if app_index < num_apps:
                app = self.apps[app_index]
                class_name = app.__class__.__name__
                name = AppInfo.get_short_name(class_name)
                color = AppInfo.get_color(class_name)
            else:
                name, color = ("App", Color.GRAY)

            row = grid_position // cols
            col = grid_position % cols
            x = start_x + col * (icon_width + padding_x)
            y = start_y + row * (icon_height + padding_y)

            # Highlight selected app
            if app_index == self.current_app_index:
                self.display.fill_rect(x - 2, y - 2, icon_width + 4, icon_height + 4, Color.WHITE)
                self.display.fill_rect(x, y, icon_width, icon_height, Color.BLACK)

            # Draw app rectangle
            self.display.rect(x, y, icon_width, icon_height, color)
            if app_index != self.current_app_index:
                self.display.fill_rect(x + 1, y + 1, icon_width - 2, icon_height - 2, color)

            # Draw app name - centered in the rectangle
            text_color = Color.WHITE if app_index == self.current_app_index else Color.BLACK
            name_len = min(len(name), icon_width // 8)  # Truncate if too long
            display_name = name[:name_len]
            name_x = x + (icon_width - len(display_name) * 8) // 2
            name_y = y + (icon_height - 8) // 2
            self.display.text(display_name, name_x, name_y, text_color)

            grid_position += 1

        # Draw scroll indicators
        self.draw_scroll_indicators(num_apps)

        # Instructions at bottom
        instruction_y = self.display.height - 35
        self.display.text("Joy:Navigate A:Open B:Sleep", 15, instruction_y, Color.GRAY)

        # Show page info
        total_pages = (num_apps + self.apps_per_page - 1) // self.apps_per_page
        current_page = (self.scroll_offset // self.apps_per_page) + 1
        page_info = f"{current_page}/{total_pages}"
        self.display.text(page_info, self.display.width - len(page_info) * 8 - 5, instruction_y, Color.GRAY)

    def draw_scroll_indicators(self, num_apps):
        """Draw scroll indicators on the right side"""
        if num_apps <= self.apps_per_page:
            return  # No scrolling needed

        indicator_x = self.display.width - 10
        indicator_height = 100
        indicator_y = 40

        # Draw scroll track
        self.display.rect(indicator_x, indicator_y, 3, indicator_height, Color.DARK_GRAY)

        # Calculate scroll thumb position and size
        total_pages = (num_apps + self.apps_per_page - 1) // self.apps_per_page
        current_page = self.scroll_offset // self.apps_per_page
        thumb_height = max(5, indicator_height // total_pages)
        thumb_y = indicator_y + (current_page * (indicator_height - thumb_height)) // (total_pages - 1) if total_pages > 1 else indicator_y

        # Draw scroll thumb
        self.display.fill_rect(indicator_x, int(thumb_y), 3, thumb_height, Color.WHITE)

        # Draw up/down arrows if there's more content
        if self.scroll_offset > 0:
            # Up arrow
            self.display.text("^", indicator_x - 5, indicator_y - 15, Color.WHITE)

        if self.scroll_offset + self.apps_per_page < num_apps:
            # Down arrow
            self.display.text("v", indicator_x - 5, indicator_y + indicator_height + 5, Color.WHITE)

    def handle_input(self):
        """Handle input in standard launcher"""
        # Update input devices
        self.buttons.update()
        
        # 5x3 grid navigation with infinite scroll
        moved = False
        num_apps = len(self.apps)
        cols = self.grid_cols

        # Calculate current position in grid
        current_grid_pos = self.current_app_index - self.scroll_offset
        current_row = current_grid_pos // cols
        current_col = current_grid_pos % cols

        # Navigation logic
        if not self.joystick.right_pin.value() and not moved:
            if current_col < cols - 1:  # Can move right within current row
                if self.current_app_index < num_apps - 1:
                    self.current_app_index += 1
                    moved = True
            else:  # At rightmost column, wrap to next row
                if self.current_app_index < num_apps - 1:
                    self.current_app_index += 1
                    if self.current_app_index >= self.scroll_offset + self.apps_per_page:
                        self.scroll_offset += self.grid_cols  # Scroll to next row
                    moved = True

        elif not self.joystick.left_pin.value() and not moved:
            if current_col > 0:  # Can move left within current row
                self.current_app_index -= 1
                moved = True
            else:  # At leftmost column, wrap to previous row
                if self.current_app_index > 0:
                    self.current_app_index -= 1
                    if self.current_app_index < self.scroll_offset:
                        self.scroll_offset -= self.grid_cols  # Scroll to previous row
                    moved = True

        elif not self.joystick.down_pin.value() and not moved:
            if self.current_app_index + cols < num_apps:  # Can move down
                self.current_app_index += cols
                if self.current_app_index >= self.scroll_offset + self.apps_per_page:
                    self.scroll_offset += cols  # Scroll down
                moved = True
            else:  # Wrap to top (infinite scroll)
                self.current_app_index = self.current_app_index % cols  # Same column, first row
                self.scroll_offset = 0
                moved = True

        elif not self.joystick.up_pin.value() and not moved:
            if self.current_app_index >= cols:  # Can move up
                self.current_app_index -= cols
                if self.current_app_index < self.scroll_offset:
                    self.scroll_offset -= cols  # Scroll up
                moved = True
            else:  # Wrap to bottom (infinite scroll)
                # Find last row with apps in same column
                target_col = self.current_app_index % cols
                last_full_row = ((num_apps - 1) // cols) * cols
                self.current_app_index = min(last_full_row + target_col, num_apps - 1)
                # Scroll to show the bottom
                self.scroll_offset = max(0, self.current_app_index - self.apps_per_page + cols)
                moved = True

        # Ensure scroll offset is valid
        max_scroll = max(0, num_apps - self.apps_per_page)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))

        if moved:
            self.draw_screen()
            time.sleep_ms(150)  # Debounce
            
        # Button A - Open app
        if self.buttons.is_pressed('A'):
            app = self.apps[self.current_app_index]
            LauncherUtils.log_app_usage(app.__class__.__name__)
            return ("launch_app", app)
            
        # Button B - Sleep mode (simple press detection)
        if self.buttons.is_pressed('B'):
            return "sleep"
            
        return "continue"