"""
Prayer Times App - Islamic prayer times display and alerts
Based on astronomical calculations with Hijri calendar integration
"""

import time
import math
import machine
from lib.st7789 import Color
from lib.dst_utils import get_current_timezone_offset, format_timezone_string

class Prayers:
    def __init__(self, display, joystick, buttons):
        """Initialize Prayer Times app"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        # App state
        self.view_mode = "main"  # "main", "settings", "hijri"
        self.selected_option = 0
        
        # Location settings (default to Tampa)
        self.latitude = 27.9506
        self.longitude = -82.4572
        self.base_timezone = -5  # EST base timezone (standard time)
        self.dst_enabled = True  # Enable automatic DST
        self.location_name = "Tampa, FL"
        
        # Calculation settings
        self.calculation_method = 'ISNA'  # Islamic Society of North America
        self.asr_madhab = 1  # 1 = Shafi, 2 = Hanafi
        
        # Prayer calculation methods
        self.methods = {
            'ISNA': {'fajr': 15, 'isha': 15},
            'MWL': {'fajr': 18, 'isha': 17},
            'Mecca': {'fajr': 18.5, 'isha': 90}  # 90 minutes after Maghrib
        }
        
        # Prayer times cache
        self.prayer_times_cache = {}
        self.last_update_day = -1
        
        # RTC for time keeping
        self.rtc = machine.RTC()
        
        # Hijri calendar data
        self.hijri_months = [
            "Muharram", "Safar", "Rabi' I", "Rabi' II",
            "Jumada I", "Jumada II", "Rajab", "Sha'ban",
            "Ramadan", "Shawwal", "Dhu al-Qi'dah", "Dhu al-Hijjah"
        ]
        
        # Islamic events
        self.islamic_events = [
            {'name': 'Ashura', 'month': 1, 'day': 10},
            {'name': 'Mawlid', 'month': 3, 'day': 12},
            {'name': 'Isra & Mi\'raj', 'month': 7, 'day': 27},
            {'name': 'Ramadan', 'month': 9, 'day': 1},
            {'name': 'Laylat al-Qadr', 'month': 9, 'day': 27},
            {'name': 'Eid al-Fitr', 'month': 10, 'day': 1},
            {'name': 'Eid al-Adha', 'month': 12, 'day': 10}
        ]
        
    def init(self):
        """Initialize app when opened"""
        self.view_mode = "main"
        self.selected_option = 0
        self.update_prayer_times()
        self.draw_screen()
        
    def draw_screen(self):
        """Draw the appropriate screen"""
        self.display.fill(Color.BLACK)
        
        if self.view_mode == "main":
            self.draw_main_view()
        elif self.view_mode == "settings":
            self.draw_settings_view()
        elif self.view_mode == "hijri":
            self.draw_hijri_view()
            
        self.display.display()
        
    def draw_main_view(self):
        """Draw main prayer times view"""
        # Header with location
        self.display.text("PRAYER TIMES", 70, 5, Color.CYAN)
        
        # Location and date
        location_text = self.location_name[:20]  # Truncate if too long
        loc_x = (240 - len(location_text) * 8) // 2
        self.display.text(location_text, loc_x, 20, Color.GRAY)
        
        # Current time with timezone
        try:
            dt = self.rtc.datetime()
            current_time = f"{dt[4]:02d}:{dt[5]:02d}"
            tz_string = format_timezone_string(self.base_timezone, self.dst_enabled)
            time_tz = f"{current_time} {tz_string}"
            time_x = (240 - len(time_tz) * 8) // 2
            self.display.text(time_tz, time_x, 35, Color.WHITE)
        except:
            pass
            
        # Prayer times
        if not self.prayer_times_cache:
            self.display.text("Calculating...", 75, 100, Color.YELLOW)
        else:
            y_pos = 55
            next_prayer, next_time = self.get_next_prayer()
            
            prayer_order = ['Fajr', 'Sunrise', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']
            for prayer in prayer_order:
                if prayer in self.prayer_times_cache:
                    prayer_time = self.prayer_times_cache[prayer]
                    
                    # Highlight next prayer
                    if prayer == next_prayer:
                        self.display.fill_rect(15, y_pos - 2, 210, 16, Color.GREEN)
                        prayer_color = Color.BLACK
                        time_color = Color.BLACK
                    else:
                        prayer_color = Color.CYAN if prayer in ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha'] else Color.GRAY
                        time_color = Color.WHITE
                        
                    # Prayer name
                    self.display.text(prayer, 20, y_pos, prayer_color)
                    
                    # Prayer time
                    self.display.text(prayer_time, 150, y_pos, time_color)
                    
                    y_pos += 18
                    
            # Next prayer countdown
            if next_prayer and next_time:
                remaining = self.calculate_time_remaining(next_time)
                if remaining:
                    next_text = f"Next: {next_prayer}"
                    self.display.text(next_text, 20, 195, Color.YELLOW)
                    self.display.text(remaining, 20, 210, Color.GREEN)
                    
        # Instructions
        self.display.text("A:Options Y:Hijri B:Back", 40, 225, Color.GRAY)
        
    def draw_settings_view(self):
        """Draw settings view"""
        self.display.text("SETTINGS", 85, 10, Color.CYAN)
        
        # Get current timezone info
        current_tz = get_current_timezone_offset(self.base_timezone, self.dst_enabled)
        tz_display = format_timezone_string(self.base_timezone, self.dst_enabled)
        dst_status = "On" if self.dst_enabled else "Off"
        
        options = [
            f"Method: {self.calculation_method}",
            f"Madhab: {'Shafi' if self.asr_madhab == 1 else 'Hanafi'}",
            f"Timezone: {tz_display}",
            f"Auto DST: {dst_status}",
            f"Location: {self.location_name[:12]}",
            "Update Times"
        ]
        
        y_start = 50
        for i, option in enumerate(options):
            y = y_start + i * 25
            
            if i == self.selected_option:
                self.display.fill_rect(10, y - 3, 220, 18, Color.BLUE)
                text_color = Color.WHITE
            else:
                text_color = Color.WHITE
                
            self.display.text(option, 15, y, text_color)
            
        self.display.text("Joy:Navigate A:Change B:Back", 25, 210, Color.GRAY)
        
    def draw_hijri_view(self):
        """Draw Hijri calendar view"""
        self.display.text("HIJRI CALENDAR", 65, 10, Color.CYAN)
        
        # Get current Hijri date
        hijri_year, hijri_month, hijri_day = self.get_current_hijri_date()
        
        # Hijri date display
        month_name = self.hijri_months[hijri_month - 1] if 1 <= hijri_month <= 12 else "Unknown"
        hijri_date = f"{hijri_day} {month_name} {hijri_year}"
        date_x = (240 - len(hijri_date) * 8) // 2
        self.display.text(hijri_date, date_x, 40, Color.YELLOW)
        
        # Special month indication
        if hijri_month == 9:  # Ramadan
            ramadan_text = f"Ramadan - Day {hijri_day}"
            ram_x = (240 - len(ramadan_text) * 8) // 2
            self.display.text(ramadan_text, ram_x, 65, Color.GREEN)
        elif hijri_month == 12:  # Dhu al-Hijjah
            hajj_text = "Hajj Season"
            hajj_x = (240 - len(hajj_text) * 8) // 2
            self.display.text(hajj_text, hajj_x, 65, Color.PURPLE)
            
        # Next Islamic event
        next_event, days_until = self.get_next_islamic_event(hijri_month, hijri_day)
        if next_event:
            self.display.text("Upcoming Event:", 20, 100, Color.WHITE)
            self.display.text(next_event, 20, 120, Color.ORANGE)
            if days_until == 0:
                self.display.text("Today!", 20, 140, Color.GREEN)
            elif days_until == 1:
                self.display.text("Tomorrow", 20, 140, Color.YELLOW)
            else:
                self.display.text(f"In {days_until} days", 20, 140, Color.CYAN)
                
        # Month progress
        days_in_month = 30 if hijri_month % 2 == 1 else 29
        progress = (hijri_day / days_in_month) * 100
        self.display.text(f"Month: {progress:.0f}% complete", 20, 170, Color.GRAY)
        
        self.display.text("Press B to go back", 60, 215, Color.GRAY)
        
    def calculate_prayer_times(self, year, month, day):
        """Calculate prayer times for a given date"""
        # Julian day calculation
        julian_day = self.gregorian_to_julian(year, month, day)
        T = (julian_day - 2451545.0) / 36525
        
        # Solar position
        sun_data = self.sun_position(T)
        decl = sun_data['declination']
        eqt = sun_data['equation']
        
        # Solar noon (transit)
        transit = 12 - eqt
        
        # Sunrise and sunset
        sunrise_angle = -0.833
        sunrise = self.calculate_horizon_time(transit, sunrise_angle, decl, False)
        sunset = self.calculate_horizon_time(transit, sunrise_angle, decl, True)
        
        # Get method parameters
        method = self.methods.get(self.calculation_method, self.methods['ISNA'])
        
        # Fajr
        fajr_angle = -method['fajr']
        fajr = self.calculate_horizon_time(transit, fajr_angle, decl, False)
        
        # Asr calculation
        shadow_factor = self.asr_madhab
        asr_angle = math.degrees(math.atan(1.0 / (shadow_factor + math.tan(math.radians(abs(self.latitude - decl))))))
        
        cos_h = (math.sin(math.radians(asr_angle)) - 
                math.sin(math.radians(decl)) * math.sin(math.radians(self.latitude))) / \
               (math.cos(math.radians(decl)) * math.cos(math.radians(self.latitude)))
        
        cos_h = max(-1, min(1, cos_h))
        asr = transit + math.degrees(math.acos(cos_h)) / 15
        
        # Maghrib (sunset + 3 minutes)
        maghrib = sunset + 3/60
        
        # Isha
        if method['isha'] > 90:
            isha = maghrib + method['isha'] / 60
        else:
            isha_angle = -method['isha']
            isha = self.calculate_horizon_time(transit, isha_angle, decl, True)
        
        # Convert to time strings with timezone
        times = {
            'Fajr': self.hours_to_time(fajr),
            'Sunrise': self.hours_to_time(sunrise),
            'Dhuhr': self.hours_to_time(transit),
            'Asr': self.hours_to_time(asr),
            'Maghrib': self.hours_to_time(maghrib),
            'Isha': self.hours_to_time(isha)
        }
        
        return times
        
    def calculate_horizon_time(self, transit, angle, declination, after_transit):
        """Calculate time for specific sun altitude angle"""
        cos_h = (math.sin(math.radians(angle)) - 
                math.sin(math.radians(declination)) * math.sin(math.radians(self.latitude))) / \
               (math.cos(math.radians(declination)) * math.cos(math.radians(self.latitude)))
        
        cos_h = max(-1, min(1, cos_h))
        hour_angle = math.degrees(math.acos(cos_h)) / 15
        
        return transit + hour_angle if after_transit else transit - hour_angle
        
    def sun_position(self, T):
        """Calculate sun's declination and equation of time"""
        # Mean solar longitude
        L0 = (280.46646 + 36000.76983 * T) % 360
        
        # Mean anomaly
        M = (357.52911 + 35999.05029 * T) % 360
        
        # Equation of center
        C = (1.914602 * math.sin(math.radians(M)) + 
             0.019993 * math.sin(math.radians(2 * M)))
        
        # True longitude
        L = L0 + C
        
        # Obliquity
        epsilon = 23.439 - 0.00000036 * T
        
        # Declination
        decl = math.degrees(math.asin(math.sin(math.radians(epsilon)) * math.sin(math.radians(L))))
        
        # Right ascension
        RA = math.degrees(math.atan2(math.cos(math.radians(epsilon)) * math.sin(math.radians(L)), 
                                     math.cos(math.radians(L))))
        RA = (RA + 360) % 360
        
        # Equation of time
        eqt = (L0 - RA) / 15
        if eqt > 12:
            eqt -= 24
        elif eqt < -12:
            eqt += 24
            
        return {'declination': decl, 'equation': eqt}
        
    def gregorian_to_julian(self, year, month, day):
        """Convert Gregorian date to Julian day"""
        if month <= 2:
            year -= 1
            month += 12
        
        a = math.floor(year / 100)
        b = 2 - a + math.floor(a / 4)
        
        return math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day + b - 1524.5
        
    def hours_to_time(self, hours):
        """Convert decimal hours to time string with timezone"""
        # Get current timezone offset with DST
        current_timezone = get_current_timezone_offset(self.base_timezone, self.dst_enabled)
        
        # Apply timezone and longitude correction
        longitude_correction = -self.longitude / 15
        hours = hours + longitude_correction + current_timezone
        
        # Normalize to 24-hour format
        while hours < 0:
            hours += 24
        while hours >= 24:
            hours -= 24
            
        h = int(hours)
        m = int((hours - h) * 60)
        
        return f"{h:02d}:{m:02d}"
        
    def update_prayer_times(self):
        """Update prayer times for current day"""
        try:
            year, month, day, _, _, _, _, _ = self.rtc.datetime()
            
            if day != self.last_update_day:
                self.prayer_times_cache = self.calculate_prayer_times(year, month, day)
                self.last_update_day = day
                
        except Exception as e:
            print(f"Prayer times calculation error: {e}")
            
    def get_next_prayer(self):
        """Get next prayer and time"""
        if not self.prayer_times_cache:
            return None, None
            
        try:
            _, _, _, _, hour, minute, _, _ = self.rtc.datetime()
            current_minutes = hour * 60 + minute
            
            prayer_order = ['Fajr', 'Dhuhr', 'Asr', 'Maghrib', 'Isha']
            
            for prayer in prayer_order:
                if prayer in self.prayer_times_cache:
                    prayer_time = self.prayer_times_cache[prayer]
                    prayer_hour, prayer_min = map(int, prayer_time.split(':'))
                    prayer_minutes = prayer_hour * 60 + prayer_min
                    
                    if prayer_minutes > current_minutes:
                        return prayer, prayer_time
            
            # Next is Fajr tomorrow
            return 'Fajr', self.prayer_times_cache.get('Fajr', '--:--')
        except:
            return None, None
            
    def calculate_time_remaining(self, prayer_time):
        """Calculate time remaining until prayer"""
        try:
            _, _, _, _, hour, minute, _, _ = self.rtc.datetime()
            current_minutes = hour * 60 + minute
            
            prayer_hour, prayer_min = map(int, prayer_time.split(':'))
            prayer_minutes = prayer_hour * 60 + prayer_min
            
            if prayer_minutes <= current_minutes:
                prayer_minutes += 24 * 60  # Next day
                
            remaining = prayer_minutes - current_minutes
            hours = remaining // 60
            mins = remaining % 60
            
            if hours > 0:
                return f"{hours}h {mins}m"
            else:
                return f"{mins}m"
        except:
            return None
            
    def get_current_hijri_date(self):
        """Get current Hijri date (simplified calculation)"""
        try:
            year, month, day, _, _, _, _, _ = self.rtc.datetime()
            
            # Simplified Hijri conversion (approximate)
            # Based on average lunar year of 354.37 days
            greg_epoch = self.gregorian_to_julian(622, 7, 16)  # Hijri epoch
            current_jd = self.gregorian_to_julian(year, month, day)
            
            days_since_epoch = current_jd - greg_epoch
            hijri_year = int(days_since_epoch / 354.37) + 1
            
            days_in_year = days_since_epoch - (hijri_year - 1) * 354.37
            hijri_month = int(days_in_year / 29.53) + 1
            hijri_day = int(days_in_year - (hijri_month - 1) * 29.53) + 1
            
            # Ensure valid ranges
            hijri_month = max(1, min(12, hijri_month))
            hijri_day = max(1, min(30, hijri_day))
            
            return int(hijri_year), int(hijri_month), int(hijri_day)
        except:
            return 1446, 3, 12  # Default date
            
    def get_next_islamic_event(self, current_month, current_day):
        """Get next Islamic event"""
        for event in self.islamic_events:
            if (event['month'] > current_month or 
                (event['month'] == current_month and event['day'] >= current_day)):
                
                if event['month'] == current_month:
                    days_until = event['day'] - current_day
                else:
                    # Simplified calculation
                    days_until = (event['month'] - current_month) * 30 + event['day'] - current_day
                    
                return event['name'], days_until
                
        # Next year's first event
        first_event = self.islamic_events[0]
        days_until = (12 - current_month + first_event['month']) * 30 + first_event['day'] - current_day
        return first_event['name'], days_until
        
    def update(self):
        """Update Prayer Times app"""
        if self.view_mode == "main":
            # Update prayer times periodically
            self.update_prayer_times()
            
            if self.buttons.is_pressed('A'):
                self.view_mode = "settings"
                self.selected_option = 0
                self.draw_screen()
                time.sleep_ms(200)
            elif self.buttons.is_pressed('Y'):
                self.view_mode = "hijri"
                self.draw_screen()
                time.sleep_ms(200)
                
        elif self.view_mode == "settings":
            direction = self.joystick.get_direction_slow()
            if direction == 'UP':
                self.selected_option = max(0, self.selected_option - 1)
                self.draw_screen()
            elif direction == 'DOWN':
                self.selected_option = min(5, self.selected_option + 1)
                self.draw_screen()
                
            if self.buttons.is_pressed('A'):
                if self.selected_option == 0:  # Method
                    methods = ['ISNA', 'MWL', 'Mecca']
                    current_idx = methods.index(self.calculation_method)
                    self.calculation_method = methods[(current_idx + 1) % len(methods)]
                elif self.selected_option == 1:  # Madhab
                    self.asr_madhab = 2 if self.asr_madhab == 1 else 1
                elif self.selected_option == 2:  # Timezone
                    # Cycle through common US timezones
                    timezones = [-8, -7, -6, -5, -4]  # PST, MST, CST, EST, AST
                    if self.base_timezone in timezones:
                        current_idx = timezones.index(self.base_timezone)
                        self.base_timezone = timezones[(current_idx + 1) % len(timezones)]
                    else:
                        self.base_timezone = -5  # Default to EST
                elif self.selected_option == 3:  # Auto DST
                    self.dst_enabled = not self.dst_enabled
                elif self.selected_option == 5:  # Update
                    self.last_update_day = -1  # Force update
                    self.update_prayer_times()
                    
                self.draw_screen()
                time.sleep_ms(200)
                
        elif self.view_mode == "hijri":
            # Auto-refresh these views
            if time.ticks_ms() % 5000 == 0:
                self.draw_screen()
                
        # Check for exit
        if self.buttons.is_pressed('B'):
            if self.view_mode == "main":
                return False
            else:
                self.view_mode = "main"
                self.draw_screen()
                time.sleep_ms(200)
                
        return True
        
    def cleanup(self):
        """Cleanup when exiting app"""
        pass