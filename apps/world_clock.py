"""
World Clock App - Display time in multiple cities
Shows current time in New York, Cairo, Dubai, and Chennai
"""

import time
import machine
from lib.st7789 import Color
from lib.dst_utils import is_dst_active, get_current_timezone_offset

# Try to import wifi time sync to check if it's available
try:
    from lib.wifi_time import WiFiTimeSync
    WIFI_TIME_AVAILABLE = True
except ImportError:
    WIFI_TIME_AVAILABLE = False

class WorldClock:
    def __init__(self, display, joystick, buttons):
        """Initialize World Clock app"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        # World cities with their timezone offsets from UTC
        self.cities = [
            {
                "name": "New York",
                "country": "USA",
                "base_offset": -5,  # EST (UTC-5)
                "timezone_code": "EST",  # For DST calculation
                "color": Color.BLUE,
                "icon": "NY"
            },
            {
                "name": "Cairo", 
                "country": "Egypt",
                "base_offset": 3,   # EET (UTC+3) - Egypt Standard Time
                "timezone_code": "EET",  # Egypt doesn't observe DST anymore
                "color": Color.YELLOW,
                "icon": "CA"
            },
            {
                "name": "Dubai",
                "country": "UAE", 
                "base_offset": 4,   # GST (UTC+4)
                "timezone_code": "GST",  # No DST
                "color": Color.GREEN,
                "icon": "DB"
            },
            {
                "name": "Chennai",
                "country": "India",
                "base_offset": 5.5,  # IST (UTC+5:30)
                "timezone_code": "IST",  # No DST
                "color": Color.ORANGE,
                "icon": "CH"
            }
        ]
        
        self.selected_city = 0
        self.view_mode = "grid"  # "grid" or "detail"
        self.last_update = 0
        
        # Initialize WiFi time sync if available
        self.wifi_sync = None
        if WIFI_TIME_AVAILABLE:
            try:
                self.wifi_sync = WiFiTimeSync()
            except:
                pass
        
    def init(self):
        """Initialize app when opened"""
        self.view_mode = "grid"
        self.selected_city = 0
        self.draw_screen()
        
    def get_utc_time(self):
        """Get current UTC time"""
        try:
            rtc = machine.RTC()
            dt = rtc.datetime()
            
            # Check if WiFi time sync is available and has synced
            if self.wifi_sync and self.wifi_sync.last_sync_time > 0:
                # WiFi time sync sets RTC to UTC time
                time_tuple = (dt[0], dt[1], dt[2], dt[4], dt[5], dt[6], dt[3], 0)
                utc_timestamp = time.mktime(time_tuple)
                return time.gmtime(utc_timestamp)
            else:
                # RTC is set to local time (Tampa EDT = UTC-4)
                # Need to convert to UTC by subtracting the local offset
                
                # Get Tampa's current timezone offset (accounting for DST)
                tampa_base_offset = -5  # EST
                tampa_current_offset = get_current_timezone_offset(tampa_base_offset, dst_enabled=True)
                
                # Convert RTC local time to UTC
                time_tuple = (dt[0], dt[1], dt[2], dt[4], dt[5], dt[6], dt[3], 0)
                local_timestamp = time.mktime(time_tuple)
                
                # Convert to UTC by subtracting Tampa's offset
                utc_timestamp = local_timestamp - (tampa_current_offset * 3600)
                return time.gmtime(utc_timestamp)
        except:
            # Fallback to system time if RTC fails
            return time.gmtime()
            
    def get_city_time(self, city):
        """Get local time for a specific city with DST support"""
        utc_time = self.get_utc_time()
        utc_timestamp = time.mktime(utc_time)
        
        # Get current offset (with DST if applicable)
        if city["timezone_code"] == "EST":
            # New York - use DST calculation
            timezone_offset = get_current_timezone_offset(city["base_offset"], dst_enabled=True)
        else:
            # Other cities don't observe DST or have different rules
            timezone_offset = city["base_offset"]
            
        # Apply timezone offset
        offset_seconds = int(timezone_offset * 3600)
        local_timestamp = utc_timestamp + offset_seconds
        local_time = time.localtime(local_timestamp)
        
        return local_time
        
    def format_time_12h(self, time_tuple):
        """Format time in 12-hour format"""
        hour = time_tuple[3]
        minute = time_tuple[4]
        
        if hour == 0:
            hour_12 = 12
            ampm = "AM"
        elif hour < 12:
            hour_12 = hour
            ampm = "AM"
        elif hour == 12:
            hour_12 = 12
            ampm = "PM"
        else:
            hour_12 = hour - 12
            ampm = "PM"
            
        return f"{hour_12:2d}:{minute:02d} {ampm}"
        
    def format_time_24h(self, time_tuple):
        """Format time in 24-hour format"""
        return f"{time_tuple[3]:02d}:{time_tuple[4]:02d}"
        
    def format_date(self, time_tuple):
        """Format date"""
        months = ["", "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                 "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
        month_name = months[time_tuple[1]] if time_tuple[1] < len(months) else "???"
        return f"{time_tuple[2]:02d} {month_name}"
        
    def get_day_name(self, time_tuple):
        """Get day name"""
        days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return days[time_tuple[6]] if time_tuple[6] < len(days) else "???"
        
    def draw_screen(self):
        """Draw the world clock screen"""
        self.display.fill(Color.BLACK)
        
        if self.view_mode == "grid":
            self.draw_grid_view()
        else:
            self.draw_detail_view()
            
        self.display.display()
        
    def draw_grid_view(self):
        """Draw grid view showing all cities"""
        # Title
        self.display.text("WORLD CLOCK", 65, 5, Color.CYAN)
        
        # Draw city grid (2x2)
        grid_width = 110
        grid_height = 70
        padding_x = 10
        padding_y = 8
        start_x = (240 - (grid_width * 2 + padding_x)) // 2
        start_y = 25
        
        for i, city in enumerate(self.cities):
            row = i // 2
            col = i % 2
            x = start_x + col * (grid_width + padding_x)
            y = start_y + row * (grid_height + padding_y)
            
            # Highlight selected city
            if i == self.selected_city:
                self.display.fill_rect(x - 2, y - 2, grid_width + 4, grid_height + 4, Color.WHITE)
                self.display.fill_rect(x, y, grid_width, grid_height, Color.BLACK)
                
            # City box
            self.display.rect(x, y, grid_width, grid_height, city["color"])
            
            # City name and country
            name_text = city["name"]
            name_x = x + (grid_width - len(name_text) * 8) // 2
            self.display.text(name_text, name_x, y + 5, city["color"])
            
            country_x = x + (grid_width - len(city["country"]) * 8) // 2
            self.display.text(city["country"], country_x, y + 20, Color.GRAY)
            
            # Current time in that city
            city_time = self.get_city_time(city)
            time_str = self.format_time_12h(city_time)
            time_x = x + (grid_width - len(time_str) * 8) // 2
            self.display.text(time_str, time_x, y + 35, Color.WHITE)
            
            # Date
            date_str = self.format_date(city_time)
            date_x = x + (grid_width - len(date_str) * 8) // 2
            self.display.text(date_str, date_x, y + 50, Color.GRAY)
            
        # Time difference info for selected city
        if self.selected_city < len(self.cities):
            selected = self.cities[self.selected_city]
            
            # Calculate current offset (including DST)
            if selected["timezone_code"] == "EST":
                current_offset = get_current_timezone_offset(selected["base_offset"], dst_enabled=True)
            else:
                current_offset = selected["base_offset"]
                
            if current_offset >= 0:
                if current_offset == int(current_offset):
                    offset_str = f"UTC+{int(current_offset)}"
                else:
                    offset_str = f"UTC+{current_offset}"
            else:
                if current_offset == int(current_offset):
                    offset_str = f"UTC{int(current_offset)}"
                else:
                    offset_str = f"UTC{current_offset}"
                
            offset_text = f"{selected['name']}: {offset_str}"
            offset_x = (240 - len(offset_text) * 8) // 2
            self.display.text(offset_text, offset_x, 175, selected["color"])
        
        # Time source indicator
        if self.wifi_sync and self.wifi_sync.last_sync_time > 0:
            source_text = "WiFi Synced"
            source_color = Color.GREEN
        else:
            source_text = "Local Time"
            source_color = Color.ORANGE
            
        source_x = (240 - len(source_text) * 8) // 2
        self.display.text(source_text, source_x, 190, source_color)
        
        # Instructions
        self.display.text("Joy:Select A:Detail", 50, 205, Color.GRAY)
        self.display.text("Y:Refresh B:Home", 55, 220, Color.GRAY)
        
    def draw_detail_view(self):
        """Draw detailed view for selected city"""
        city = self.cities[self.selected_city]
        city_time = self.get_city_time(city)
        
        # Title with city name
        title = f"{city['name']}, {city['country']}"
        title_x = (240 - len(title) * 8) // 2
        self.display.text(title, title_x, 10, city["color"])
        
        # Large time display
        time_12h = self.format_time_12h(city_time)
        time_24h = self.format_time_24h(city_time)
        
        # 12-hour time (larger)
        time_x = (240 - len(time_12h) * 12) // 2  # Approximate 1.5x scaling
        self.draw_large_text(time_12h, time_x, 40, Color.WHITE)
        
        # 24-hour time (smaller)
        time_24_x = (240 - len(time_24h) * 8) // 2
        self.display.text(f"({time_24h})", time_24_x, 70, Color.GRAY)
        
        # Day and date
        day_name = self.get_day_name(city_time)
        date_str = self.format_date(city_time)
        full_date = f"{day_name}, {date_str} {city_time[0]}"
        date_x = (240 - len(full_date) * 8) // 2
        self.display.text(full_date, date_x, 90, Color.YELLOW)
        
        # Timezone info (show current offset including DST)
        if city["timezone_code"] == "EST":
            current_offset = get_current_timezone_offset(city["base_offset"], dst_enabled=True)
        else:
            current_offset = city["base_offset"]
            
        if current_offset >= 0:
            if current_offset == int(current_offset):
                offset_str = f"UTC+{int(current_offset)}"
            else:
                offset_str = f"UTC+{current_offset}"
        else:
            if current_offset == int(current_offset):
                offset_str = f"UTC{int(current_offset)}"
            else:
                offset_str = f"UTC{current_offset}"
                
        tz_text = f"Timezone: {offset_str}"
        tz_x = (240 - len(tz_text) * 8) // 2
        self.display.text(tz_text, tz_x, 110, city["color"])
        
        # Time comparison with other cities
        self.display.text("Other Cities:", 20, 135, Color.CYAN)
        
        y_pos = 155
        for i, other_city in enumerate(self.cities):
            if i == self.selected_city:
                continue  # Skip current city
                
            other_time = self.get_city_time(other_city)
            other_time_str = self.format_time_12h(other_time)
            
            # City name and time
            city_text = f"{other_city['name']}: {other_time_str}"
            if len(city_text) > 28:  # Truncate if too long
                city_text = city_text[:25] + "..."
                
            self.display.text(city_text, 15, y_pos, other_city["color"])
            y_pos += 15
            
            if y_pos > 190:  # Don't go too low
                break
                
        # Time source indicator
        if self.wifi_sync and self.wifi_sync.last_sync_time > 0:
            source_text = "WiFi Synced"
            source_color = Color.GREEN
        else:
            source_text = "Local Time"
            source_color = Color.ORANGE
            
        source_x = (240 - len(source_text) * 8) // 2
        self.display.text(source_text, source_x, 205, source_color)
                
        # Instructions
        self.display.text("A:Back B:Home", 70, 225, Color.GRAY)
        
    def draw_large_text(self, text, x, y, color):
        """Draw larger text (approximate 1.5x scaling)"""
        # Simple approach: draw text with slight offsets for thickness
        self.display.text(text, x, y, color)
        self.display.text(text, x + 1, y, color)
        self.display.text(text, x, y + 1, color)
        self.display.text(text, x + 1, y + 1, color)
        
    def auto_update_times(self):
        """Update times if enough time has passed"""
        current_time = time.ticks_ms()
        if time.ticks_diff(current_time, self.last_update) > 30000:  # Update every 30 seconds
            self.last_update = current_time
            # Times are calculated dynamically with DST support
            self.draw_screen()
            
    def update(self):
        """Update World Clock app"""
        # Auto-update times
        self.auto_update_times()
        
        if self.view_mode == "grid":
            # Navigate cities
            direction = self.joystick.get_direction_slow()
            if direction == 'UP':
                if self.selected_city >= 2:
                    self.selected_city -= 2
                    self.draw_screen()
            elif direction == 'DOWN':
                if self.selected_city < 2:
                    self.selected_city += 2
                    self.draw_screen()
            elif direction == 'LEFT':
                if self.selected_city % 2 == 1:
                    self.selected_city -= 1
                    self.draw_screen()
            elif direction == 'RIGHT':
                if self.selected_city % 2 == 0 and self.selected_city < 3:
                    self.selected_city += 1
                    self.draw_screen()
                    
            # Show city detail
            if self.buttons.is_pressed('A'):
                self.view_mode = "detail"
                self.draw_screen()
                time.sleep_ms(200)
                
            # Manual refresh
            if self.buttons.is_pressed('Y'):
                self.last_update = 0  # Force update
                self.draw_screen()
                time.sleep_ms(200)
                
        elif self.view_mode == "detail":
            # Navigate between cities in detail view
            direction = self.joystick.get_direction_slow()
            if direction in ['UP', 'LEFT']:
                self.selected_city = (self.selected_city - 1) % len(self.cities)
                self.draw_screen()
            elif direction in ['DOWN', 'RIGHT']:
                self.selected_city = (self.selected_city + 1) % len(self.cities)
                self.draw_screen()
                
            # Back to grid
            if self.buttons.is_pressed('A'):
                self.view_mode = "grid"
                self.draw_screen()
                time.sleep_ms(200)
                
        # Check for exit
        if self.buttons.is_pressed('B'):
            return False
            
        return True
        
    def cleanup(self):
        """Cleanup when exiting app"""
        pass