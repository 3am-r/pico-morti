"""
Qibla Compass App
Shows direction to Kaaba (Mecca) from current location
Displays compass with direction arrow and distance
"""

import math
import time
from lib.st7789 import Color

class QiblaCompass:
    def __init__(self, display, joystick, buttons):
        """Initialize Qibla Compass app"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        # Default location (can be changed in settings)
        # Default to New York coordinates
        self.latitude = 40.7128
        self.longitude = -74.0060
        
        # Load location from settings if available
        self.load_location()
        
    def load_location(self):
        """Load location from settings file"""
        try:
            with open('settings.json', 'r') as f:
                import json
                settings = json.load(f)
                if 'latitude' in settings and 'longitude' in settings:
                    self.latitude = settings['latitude']
                    self.longitude = settings['longitude']
        except:
            # Use default location if settings unavailable
            pass
            
    def init(self):
        """Initialize app"""
        self.draw_screen()
        
    def draw_screen(self):
        """Draw Qibla compass screen"""
        self.display.fill(Color.BLACK)
        
        # Title
        self.display.text("QIBLA COMPASS", 65, 10, Color.CYAN)
        
        # Calculate Qibla direction
        qibla_bearing = self.calculate_qibla_direction()
        
        # Draw compass
        center_x, center_y = 120, 120
        radius = 60
        
        # Compass circle
        self.display.circle(center_x, center_y, radius, Color.WHITE)
        self.display.circle(center_x, center_y, radius - 2, Color.WHITE)
        
        # Cardinal directions
        self.display.text("N", center_x - 4, center_y - radius - 15, Color.WHITE)
        self.display.text("S", center_x - 4, center_y + radius + 5, Color.WHITE)
        self.display.text("E", center_x + radius + 5, center_y - 4, Color.WHITE)
        self.display.text("W", center_x - radius - 15, center_y - 4, Color.WHITE)
        
        # Qibla direction arrow
        qibla_rad = math.radians(qibla_bearing - 90)  # -90 to start from north
        arrow_length = radius - 10
        
        # Arrow tip
        tip_x = center_x + int(arrow_length * math.cos(qibla_rad))
        tip_y = center_y + int(arrow_length * math.sin(qibla_rad))
        
        # Draw arrow shaft
        self.display.line(center_x, center_y, tip_x, tip_y, Color.GREEN)
        
        # Arrow head (simple triangular shape)
        head_length = 8
        head_angle = 0.5
        
        head1_x = tip_x - int(head_length * math.cos(qibla_rad - head_angle))
        head1_y = tip_y - int(head_length * math.sin(qibla_rad - head_angle))
        head2_x = tip_x - int(head_length * math.cos(qibla_rad + head_angle))
        head2_y = tip_y - int(head_length * math.sin(qibla_rad + head_angle))
        
        self.display.line(tip_x, tip_y, head1_x, head1_y, Color.GREEN)
        self.display.line(tip_x, tip_y, head2_x, head2_y, Color.GREEN)
        
        # Center dot
        self.display.fill_rect(center_x - 2, center_y - 2, 4, 4, Color.WHITE)
        
        # Bearing text
        bearing_text = f"Qibla: {qibla_bearing:.0f}°"
        bearing_x = (240 - len(bearing_text) * 8) // 2
        self.display.text(bearing_text, bearing_x, 200, Color.YELLOW)
        
        # Distance to Kaaba
        distance = self.calculate_distance_to_kaaba()
        dist_text = f"Distance: {distance:.0f} km"
        dist_x = (240 - len(dist_text) * 8) // 2
        self.display.text(dist_text, dist_x, 215, Color.GRAY)
        
        # Location info
        loc_text = f"From: {self.latitude:.1f}, {self.longitude:.1f}"
        loc_x = (240 - len(loc_text) * 8) // 2
        self.display.text(loc_text, loc_x, 30, Color.GRAY)
        
        # Instructions
        self.display.text("A:Refresh B:Back", 60, 5, Color.GRAY)
        
        self.display.display()
        
    def calculate_qibla_direction(self):
        """Calculate Qibla direction from current location to Kaaba"""
        # Kaaba coordinates (Mecca, Saudi Arabia)
        kaaba_lat = 21.4225
        kaaba_lon = 39.8262
        
        # Convert to radians
        lat1 = math.radians(self.latitude)
        lon1 = math.radians(self.longitude)
        lat2 = math.radians(kaaba_lat)
        lon2 = math.radians(kaaba_lon)
        
        # Calculate bearing using haversine formula
        dlon = lon2 - lon1
        y = math.sin(dlon) * math.cos(lat2)
        x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
        
        bearing = math.atan2(y, x)
        bearing = math.degrees(bearing)
        bearing = (bearing + 360) % 360
        
        return bearing
        
    def calculate_distance_to_kaaba(self):
        """Calculate distance to Kaaba in kilometers using haversine formula"""
        # Kaaba coordinates
        kaaba_lat = 21.4225
        kaaba_lon = 39.8262
        
        # Haversine formula
        lat1 = math.radians(self.latitude)
        lon1 = math.radians(self.longitude)
        lat2 = math.radians(kaaba_lat)
        lon2 = math.radians(kaaba_lon)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = (math.sin(dlat/2)**2 + 
             math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2)
        c = 2 * math.asin(math.sqrt(a))
        
        # Earth radius in kilometers
        earth_radius = 6371
        distance = earth_radius * c
        
        return distance
        
    def update(self):
        """Update Qibla Compass app"""
        # Update button states
        self.buttons.update()
        
        # Handle input
        if self.buttons.is_pressed('A'):
            # Refresh the display and recalculate
            self.load_location()  # Reload location in case settings changed
            self.draw_screen()
            time.sleep_ms(200)
            
        if self.buttons.is_pressed('B'):
            return False  # Exit app
            
        # Auto-refresh every 5 seconds to update calculations
        if time.ticks_ms() % 5000 == 0:
            self.draw_screen()
            
        return True
        
    def cleanup(self):
        """Cleanup when exiting app"""
        pass