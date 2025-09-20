"""
Launcher Utilities - Common functions for all launcher types
Shared functionality for app finding, analytics, and launcher operations
"""

import json
import time
import sys
sys.path.append('..')  # Add parent directory to access app_info
from lib.st7789 import Color
from app_info import AppInfo

class LauncherUtils:
    """Utility class with common launcher functions"""
    
    @staticmethod
    def find_app_by_class_name(apps, app_name):
        """Find app instance by its class name (lowercase)"""
        app_class_map = {
            "journal": "MicroJournal",
            "countdown": "CountdownHub", 
            "tracker": "ActivityTracker",
            "pet": "XPet",
            "energy_dial": "EnergyDial",
            "gratitude": "GratitudeProxy",
            "win_logger": "WinLogger",
            "worry_box": "WorryBox",
            "world_clock": "WorldClock",
            "air_monkey": "AirMonkey",
            "elemental": "ElementalSandbox",
            "fidget_spinner": "FidgetSpinner",
            "settings": "Settings",
            "prayers": "Prayers",
            "hijri_calendar": "HijriCalendar",
            "qibla": "QiblaCompass",
            "time_sync": "TimeSyncApp"
        }
        
        target_class = app_class_map.get(app_name)
        if not target_class:
            return None
            
        for app in apps:
            if app.__class__.__name__ == target_class:
                return app
        return None
        
    @staticmethod
    def get_app_by_name(apps, app_name):
        """Alias for find_app_by_class_name for compatibility"""
        return LauncherUtils.find_app_by_class_name(apps, app_name)
        
    @staticmethod
    def get_intent_apps(apps, intent):
        """Get apps relevant to the current intent"""
        relevant_apps = []
        intent_app_names = intent["apps"]
        
        for app_name in intent_app_names:
            app = LauncherUtils.get_app_by_name(apps, app_name)
            if app:
                relevant_apps.append(app)
                
        # If no apps found, return all apps as fallback
        return relevant_apps if relevant_apps else apps
        
    @staticmethod
    def log_intent_selection(intent_name):
        """Log when user selects an intent"""
        try:
            # Try to load existing analytics
            with open("analytics.json", "r") as f:
                analytics = json.load(f)
        except:
            analytics = {"intent_selections": {}, "app_usage": {}}
            
        # Update intent selections
        if "intent_selections" not in analytics:
            analytics["intent_selections"] = {}
            
        if intent_name not in analytics["intent_selections"]:
            analytics["intent_selections"][intent_name] = 0
        analytics["intent_selections"][intent_name] += 1
        
        # Save analytics
        try:
            with open("analytics.json", "w") as f:
                json.dump(analytics, f)
        except:
            pass  # Fail silently
            
    @staticmethod
    def log_app_usage(app_class_name):
        """Log when user opens an app"""
        try:
            # Try to load existing analytics
            with open("analytics.json", "r") as f:
                analytics = json.load(f)
        except:
            analytics = {"intent_selections": {}, "app_usage": {}}
            
        # Update app usage
        if "app_usage" not in analytics:
            analytics["app_usage"] = {}
            
        if app_class_name not in analytics["app_usage"]:
            analytics["app_usage"][app_class_name] = 0
        analytics["app_usage"][app_class_name] += 1
        
        # Save analytics
        try:
            with open("analytics.json", "w") as f:
                json.dump(analytics, f)
        except:
            pass  # Fail silently
            
    @staticmethod
    def get_analytics():
        """Get current analytics data"""
        try:
            with open("analytics.json", "r") as f:
                return json.load(f)
        except:
            return {"intent_selections": {}, "app_usage": {}}
            
    @staticmethod
    def get_app_display_info():
        """Get standardized app display names and colors from centralized registry"""
        app_names = {}
        app_colors = {}
        
        for class_name, app_data in AppInfo.APPS.items():
            app_names[class_name] = app_data["short_name"]
            app_colors[class_name] = app_data["color"]
        
        return app_names, app_colors
        
    @staticmethod
    def calculate_grid_layout(num_apps):
        """Calculate optimal grid layout for given number of apps"""
        if num_apps <= 6:
            cols = 2
            rows = (num_apps + 1) // 2
            icon_width = 100
            icon_height = 40
            padding_x = 10
            padding_y = 5
        elif num_apps <= 8:
            cols = 2
            rows = (num_apps + 1) // 2
            icon_width = 80
            icon_height = 35
            padding_x = 8
            padding_y = 4
        elif num_apps <= 9:
            cols = 3
            rows = (num_apps + 2) // 3
            icon_width = 70
            icon_height = 32
            padding_x = 6
            padding_y = 3
        else:
            cols = 3
            rows = (num_apps + 2) // 3
            icon_width = 60
            icon_height = 30
            padding_x = 6
            padding_y = 2
            
        return {
            'cols': cols,
            'rows': rows,
            'icon_width': icon_width,
            'icon_height': icon_height,
            'padding_x': padding_x,
            'padding_y': padding_y
        }
        
    @staticmethod
    def draw_app_grid(display, apps, current_app_index, title="APPS", start_y=25):
        """Draw a standard app grid using common layout logic"""
        # Center title
        title_x = (240 - len(title) * 8) // 2
        display.text(title, title_x, 5, Color.CYAN)
        
        num_apps = len(apps)
        layout = LauncherUtils.calculate_grid_layout(num_apps)
        
        start_x = (240 - (layout['icon_width'] * layout['cols'] + layout['padding_x'] * (layout['cols'] - 1))) // 2
        
        # Get app display info
        app_names, app_colors = LauncherUtils.get_app_display_info()
        
        for i, app in enumerate(apps):
            if i >= num_apps:
                break
                
            row = i // layout['cols']
            col = i % layout['cols']
            x = start_x + col * (layout['icon_width'] + layout['padding_x'])
            y = start_y + row * (layout['icon_height'] + layout['padding_y'])
            
            # Get app info
            class_name = app.__class__.__name__
            name = app_names.get(class_name, class_name[:8])
            color = app_colors.get(class_name, Color.WHITE)
            
            # Highlight selected app
            if i == current_app_index:
                display.fill_rect(x - 3, y - 3, layout['icon_width'] + 6, layout['icon_height'] + 6, Color.WHITE)
                display.fill_rect(x - 1, y - 1, layout['icon_width'] + 2, layout['icon_height'] + 2, Color.BLACK)
            
            # Draw app rectangle
            display.rect(x, y, layout['icon_width'], layout['icon_height'], color)
            display.fill_rect(x + 1, y + 1, layout['icon_width'] - 2, layout['icon_height'] - 2, color)
            
            # Draw app name - centered
            name_x = x + (layout['icon_width'] - len(name) * 8) // 2
            name_y = y + (layout['icon_height'] - 8) // 2
            display.text(name, name_x, name_y, Color.BLACK)
        
        # Calculate instruction position
        grid_end_y = start_y + (layout['rows'] * layout['icon_height']) + ((layout['rows'] - 1) * layout['padding_y'])
        return grid_end_y + 20  # Return instruction_y position
        
    @staticmethod
    def handle_grid_navigation(joystick, apps, current_app_index):
        """Handle grid navigation for any app list"""
        moved = False
        num_apps = len(apps)
        layout = LauncherUtils.calculate_grid_layout(num_apps)
        cols = layout['cols']
        
        # Grid navigation
        if not joystick.right_pin.value() and not moved:
            if current_app_index % cols < cols - 1 and current_app_index < num_apps - 1:
                current_app_index += 1
                moved = True
        elif not joystick.left_pin.value() and not moved:
            if current_app_index % cols > 0:
                current_app_index -= 1
                moved = True
        elif not joystick.down_pin.value() and not moved:
            if current_app_index < num_apps - cols:
                current_app_index += cols
                moved = True
        elif not joystick.up_pin.value() and not moved:
            if current_app_index >= cols:
                current_app_index -= cols
                moved = True
                
        if moved:
            # Keep index in bounds
            current_app_index = max(0, min(num_apps - 1, current_app_index))
            
        return current_app_index, moved