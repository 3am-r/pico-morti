"""
Hijri Calendar App - Islamic lunar calendar with events and observations
Displays current Hijri date, upcoming Islamic events, and month information
"""

import time
import math
import machine
from lib.st7789 import Color

class HijriCalendar:
    def __init__(self, display, joystick, buttons):
        """Initialize Hijri Calendar app"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        # App state
        self.view_mode = "main"  # "main", "events", "months", "converter"
        self.selected_option = 0
        
        # RTC for date/time
        self.rtc = machine.RTC()
        
        # Hijri month names
        self.hijri_months = [
            "Muharram", "Safar", "Rabi' al-Awwal", "Rabi' al-Thani",
            "Jumada al-Awwal", "Jumada al-Thani", "Rajab", "Sha'ban",
            "Ramadan", "Shawwal", "Dhu al-Qi'dah", "Dhu al-Hijjah"
        ]
        
        # Short month names for display
        self.hijri_months_short = [
            "Muharram", "Safar", "Rabi' I", "Rabi' II",
            "Jumada I", "Jumada II", "Rajab", "Sha'ban",
            "Ramadan", "Shawwal", "Dhu al-Qi", "Dhu al-Hij"
        ]
        
        # Important Islamic events with Hijri dates
        self.islamic_events = [
            {'name': 'Hijri New Year', 'month': 1, 'day': 1, 'type': 'celebration'},
            {'name': 'Ashura', 'month': 1, 'day': 10, 'type': 'observance'},
            {'name': 'Mawlid al-Nabi', 'month': 3, 'day': 12, 'type': 'celebration'},
            {'name': 'Isra wal Mi\'raj', 'month': 7, 'day': 27, 'type': 'observance'},
            {'name': 'Nisf Sha\'ban', 'month': 8, 'day': 15, 'type': 'observance'},
            {'name': 'Ramadan Begins', 'month': 9, 'day': 1, 'type': 'month_start'},
            {'name': 'Laylat al-Qadr', 'month': 9, 'day': 27, 'type': 'sacred_night'},
            {'name': 'Eid al-Fitr', 'month': 10, 'day': 1, 'type': 'celebration'},
            {'name': 'Hajj Season', 'month': 12, 'day': 8, 'type': 'pilgrimage'},
            {'name': 'Day of Arafah', 'month': 12, 'day': 9, 'type': 'sacred_day'},
            {'name': 'Eid al-Adha', 'month': 12, 'day': 10, 'type': 'celebration'},
            {'name': 'Days of Tashreeq', 'month': 12, 'day': 11, 'type': 'observance'}
        ]
        
        # Reference dates for accurate Hijri conversion
        # Based on verified Islamic calendar sources
        self.reference_dates = [
            # (greg_year, greg_month, greg_day, hijri_year, hijri_month, hijri_day)
            (2024, 7, 7, 1446, 1, 1),    # Muharram 1, 1446
            (2024, 9, 16, 1446, 3, 12),  # Mawlid al-Nabi 1446
            (2025, 3, 30, 1446, 9, 1),   # Ramadan 1446 (estimated)
            (2025, 6, 26, 1447, 1, 1),   # Muharram 1, 1447 (estimated)
        ]
        
    def init(self):
        """Initialize app when opened"""
        self.view_mode = "main"
        self.selected_option = 0
        self.draw_screen()
        
    def draw_screen(self):
        """Draw the appropriate screen"""
        self.display.fill(Color.BLACK)
        
        if self.view_mode == "main":
            self.draw_main_view()
        elif self.view_mode == "events":
            self.draw_events_view()
        elif self.view_mode == "months":
            self.draw_months_view()
        elif self.view_mode == "converter":
            self.draw_converter_view()
            
        self.display.display()
        
    def draw_main_view(self):
        """Draw main Hijri calendar view"""
        # Header
        self.display.text("HIJRI CALENDAR", 65, 5, Color.CYAN)
        
        # Get current dates
        hijri_year, hijri_month, hijri_day = self.get_current_hijri_date()
        greg_year, greg_month, greg_day, _, _, _, _, _ = self.rtc.datetime()
        
        # Current Hijri date (large display)
        month_name = self.hijri_months_short[hijri_month - 1] if 1 <= hijri_month <= 12 else "Unknown"
        hijri_date = f"{hijri_day} {month_name}"
        date_x = (240 - len(hijri_date) * 8) // 2
        self.display.text(hijri_date, date_x, 30, Color.YELLOW)
        
        # Hijri year
        year_str = f"{hijri_year} AH"
        year_x = (240 - len(year_str) * 8) // 2
        self.display.text(year_str, year_x, 50, Color.WHITE)
        
        # Gregorian date for reference
        greg_date = f"{greg_day:02d}/{greg_month:02d}/{greg_year}"
        greg_x = (240 - len(greg_date) * 8) // 2
        self.display.text(f"({greg_date})", greg_x, 70, Color.GRAY)
        
        # Current month information
        self.display.text("Current Month:", 20, 95, Color.WHITE)
        full_month_name = self.hijri_months[hijri_month - 1] if 1 <= hijri_month <= 12 else "Unknown"
        
        # Truncate long month names
        if len(full_month_name) > 20:
            display_month = full_month_name[:17] + "..."
        else:
            display_month = full_month_name
            
        self.display.text(display_month, 20, 115, Color.ORANGE)
        
        # Special month indicators
        if hijri_month == 1:  # Muharram
            self.display.text("Sacred Month", 20, 135, Color.PURPLE)
        elif hijri_month == 7:  # Rajab
            self.display.text("Sacred Month", 20, 135, Color.PURPLE)
        elif hijri_month == 8:  # Sha'ban
            self.display.text("Month before Ramadan", 20, 135, Color.BLUE)
        elif hijri_month == 9:  # Ramadan
            self.display.text("Holy Month of Fasting", 20, 135, Color.GREEN)
            ramadan_text = f"Ramadan Day {hijri_day}"
            self.display.text(ramadan_text, 20, 155, Color.GREEN)
        elif hijri_month == 10:  # Shawwal
            self.display.text("Month after Ramadan", 20, 135, Color.CYAN)
        elif hijri_month == 11:  # Dhu al-Qi'dah
            self.display.text("Sacred Month", 20, 135, Color.PURPLE)
        elif hijri_month == 12:  # Dhu al-Hijjah
            self.display.text("Sacred Month - Hajj", 20, 135, Color.PURPLE)
            
        # Month progress
        days_in_month = 30 if hijri_month % 2 == 1 else 29
        if hijri_month == 12:  # Dhu al-Hijjah sometimes has 30 days
            days_in_month = 30
            
        progress = (hijri_day / days_in_month) * 100
        progress_text = f"Month: {progress:.0f}% complete"
        self.display.text(progress_text, 20, 175, Color.GRAY)
        
        # Next upcoming event
        next_event, days_until = self.get_next_islamic_event(hijri_month, hijri_day)
        if next_event:
            self.display.text("Next Event:", 20, 195, Color.WHITE)
            
            # Truncate event name if too long
            event_display = next_event[:25] if len(next_event) > 25 else next_event
            self.display.text(event_display, 20, 210, Color.YELLOW)
            
            if days_until == 0:
                self.display.text("TODAY!", 160, 210, Color.GREEN)
            elif days_until == 1:
                self.display.text("Tomorrow", 160, 210, Color.CYAN)
            else:
                days_text = f"{days_until}d"
                self.display.text(days_text, 200, 210, Color.ORANGE)
                
        # Navigation instructions
        self.display.text("A:Events Y:Months X:Convert", 25, 230, Color.GRAY)
        
    def draw_events_view(self):
        """Draw Islamic events view"""
        self.display.text("ISLAMIC EVENTS", 70, 5, Color.CYAN)
        
        hijri_year, hijri_month, hijri_day = self.get_current_hijri_date()
        
        # Show upcoming events (next 5)
        upcoming_events = self.get_upcoming_events(hijri_month, hijri_day)
        
        y_pos = 30
        self.display.text("Upcoming Events:", 10, y_pos, Color.WHITE)
        y_pos += 20
        
        for i, (event, days_until, event_month, event_day) in enumerate(upcoming_events[:6]):
            if y_pos > 190:  # Don't overflow screen
                break
                
            # Event name (truncated if needed)
            event_display = event[:22] if len(event) > 22 else event
            
            # Color coding by event type
            event_data = next((e for e in self.islamic_events if e['name'] == event), None)
            if event_data:
                if event_data['type'] == 'celebration':
                    color = Color.GREEN
                elif event_data['type'] == 'sacred_day' or event_data['type'] == 'sacred_night':
                    color = Color.YELLOW
                elif event_data['type'] == 'observance':
                    color = Color.CYAN
                elif event_data['type'] == 'month_start':
                    color = Color.PURPLE
                else:
                    color = Color.WHITE
            else:
                color = Color.WHITE
                
            self.display.text(event_display, 10, y_pos, color)
            
            # Date and countdown
            if days_until == 0:
                self.display.text("TODAY", 180, y_pos, Color.GREEN)
            elif days_until == 1:
                self.display.text("TMRW", 185, y_pos, Color.YELLOW)
            elif days_until < 30:
                self.display.text(f"{days_until}d", 200, y_pos, Color.ORANGE)
            else:
                month_name = self.hijri_months_short[event_month - 1]
                date_str = f"{event_day} {month_name[:6]}"
                date_x = 240 - len(date_str) * 8
                self.display.text(date_str, date_x, y_pos, Color.GRAY)
                
            y_pos += 18
            
        # Legend
        legend_y = 200
        self.display.text("Colors:", 10, legend_y, Color.WHITE)
        self.display.text("Celebration", 10, legend_y + 15, Color.GREEN)
        self.display.text("Sacred", 100, legend_y + 15, Color.YELLOW)
        self.display.text("Observance", 150, legend_y + 15, Color.CYAN)
        
        self.display.text("Press B to go back", 60, 235, Color.GRAY)
        
    def draw_months_view(self):
        """Draw Hijri months information view"""
        self.display.text("HIJRI MONTHS", 75, 5, Color.CYAN)
        
        hijri_year, hijri_month, hijri_day = self.get_current_hijri_date()
        
        # Show current month highlighted, with 2 before and 2 after
        start_month = max(1, hijri_month - 2)
        end_month = min(12, hijri_month + 2)
        
        y_pos = 30
        for month in range(start_month, end_month + 1):
            month_name = self.hijri_months[month - 1]
            
            # Highlight current month
            if month == hijri_month:
                self.display.fill_rect(5, y_pos - 2, 230, 16, Color.BLUE)
                text_color = Color.WHITE
                name_color = Color.YELLOW
            else:
                text_color = Color.WHITE
                name_color = Color.CYAN
                
            # Month number and name
            month_text = f"{month:2d}. {month_name}"
            self.display.text(month_text, 10, y_pos, name_color)
            
            # Month characteristics
            if month in [1, 7, 11, 12]:  # Sacred months
                self.display.text("Sacred", 180, y_pos, Color.PURPLE)
            elif month == 9:  # Ramadan
                self.display.text("Fasting", 175, y_pos, Color.GREEN)
            elif month == 12:  # Dhu al-Hijjah
                self.display.text("Hajj", 190, y_pos, Color.ORANGE)
                
            y_pos += 20
            
        # Sacred months explanation
        self.display.text("Sacred Months:", 10, y_pos + 10, Color.WHITE)
        self.display.text("Muharram, Rajab,", 10, y_pos + 25, Color.PURPLE)
        self.display.text("Dhu al-Qi'dah, Dhu al-Hijjah", 10, y_pos + 40, Color.PURPLE)
        
        self.display.text("Press B to go back", 60, 235, Color.GRAY)
        
    def draw_converter_view(self):
        """Draw date converter view"""
        self.display.text("DATE CONVERTER", 65, 5, Color.CYAN)
        
        # Get current dates
        hijri_year, hijri_month, hijri_day = self.get_current_hijri_date()
        greg_year, greg_month, greg_day, _, _, _, _, _ = self.rtc.datetime()
        
        # Today's conversion
        self.display.text("Today's Date:", 10, 30, Color.WHITE)
        
        # Gregorian
        greg_str = f"Gregorian: {greg_day:02d}/{greg_month:02d}/{greg_year}"
        self.display.text(greg_str, 10, 50, Color.YELLOW)
        
        # Hijri
        month_name = self.hijri_months_short[hijri_month - 1]
        hijri_str = f"Hijri: {hijri_day} {month_name} {hijri_year}"
        self.display.text(hijri_str, 10, 70, Color.GREEN)
        
        # Sample conversions for reference
        self.display.text("Reference Dates:", 10, 100, Color.WHITE)
        
        y_pos = 120
        sample_dates = [
            ("01/01/2024", "20 Jumada II 1445"),
            ("07/07/2024", "1 Muharram 1446"),
            ("16/09/2024", "12 Rabi' I 1446"),
            ("30/03/2025", "1 Ramadan 1446*"),
            ("26/06/2025", "1 Muharram 1447*")
        ]
        
        for greg_date, hijri_date in sample_dates:
            if y_pos > 200:
                break
                
            self.display.text(greg_date, 10, y_pos, Color.CYAN)
            self.display.text("=", 85, y_pos, Color.WHITE)
            
            # Truncate Hijri date if too long
            if len(hijri_date) > 18:
                hijri_display = hijri_date[:15] + "..."
            else:
                hijri_display = hijri_date
                
            self.display.text(hijri_display, 100, y_pos, Color.ORANGE)
            y_pos += 15
            
        # Note about estimates
        self.display.text("* = Estimated", 10, 210, Color.GRAY)
        self.display.text("Lunar months vary by region", 10, 225, Color.GRAY)
        
        self.display.text("Press B to go back", 60, 5, Color.GRAY)
        
    def get_current_hijri_date(self):
        """Calculate current Hijri date"""
        try:
            year, month, day, _, _, _, _, _ = self.rtc.datetime()
            return self.gregorian_to_hijri(year, month, day)
        except:
            return 1446, 3, 12  # Default fallback
            
    def gregorian_to_hijri(self, year, month, day):
        """Convert Gregorian date to Hijri using reference dates"""
        target_jd = self.gregorian_to_julian(year, month, day)
        
        # Find closest reference date
        best_ref = None
        min_diff = float('inf')
        
        for ref_greg_y, ref_greg_m, ref_greg_d, ref_hij_y, ref_hij_m, ref_hij_d in self.reference_dates:
            ref_jd = self.gregorian_to_julian(ref_greg_y, ref_greg_m, ref_greg_d)
            diff = abs(target_jd - ref_jd)
            if diff < min_diff:
                min_diff = diff
                best_ref = (ref_jd, ref_hij_y, ref_hij_m, ref_hij_d)
                
        if best_ref is None:
            # Fallback calculation
            return self.simple_gregorian_to_hijri(year, month, day)
            
        ref_jd, ref_hij_y, ref_hij_m, ref_hij_d = best_ref
        
        # Calculate days difference
        days_diff = int(target_jd - ref_jd)
        
        # Approximate Hijri calculation from reference
        hijri_days = (ref_hij_y - 1) * 354 + (ref_hij_m - 1) * 29.5 + ref_hij_d + days_diff
        
        hijri_year = int(hijri_days / 354) + 1
        remaining_days = hijri_days - (hijri_year - 1) * 354
        
        hijri_month = int(remaining_days / 29.5) + 1
        hijri_day = int(remaining_days - (hijri_month - 1) * 29.5)
        
        # Ensure valid ranges
        hijri_month = max(1, min(12, hijri_month))
        hijri_day = max(1, min(30, hijri_day))
        
        return int(hijri_year), int(hijri_month), int(hijri_day)
        
    def simple_gregorian_to_hijri(self, year, month, day):
        """Simple Hijri conversion for fallback"""
        # Basic calculation using average lunar year
        greg_epoch = self.gregorian_to_julian(622, 7, 16)  # Hijri epoch
        current_jd = self.gregorian_to_julian(year, month, day)
        
        days_since_epoch = current_jd - greg_epoch
        hijri_year = int(days_since_epoch / 354.37) + 1
        
        days_in_year = days_since_epoch - (hijri_year - 1) * 354.37
        hijri_month = int(days_in_year / 29.53) + 1
        hijri_day = int(days_in_year - (hijri_month - 1) * 29.53) + 1
        
        hijri_month = max(1, min(12, hijri_month))
        hijri_day = max(1, min(30, hijri_day))
        
        return int(hijri_year), int(hijri_month), int(hijri_day)
        
    def gregorian_to_julian(self, year, month, day):
        """Convert Gregorian date to Julian day number"""
        if month <= 2:
            year -= 1
            month += 12
            
        a = int(year / 100)
        b = 2 - a + int(a / 4)
        
        return int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + day + b - 1524.5
        
    def get_next_islamic_event(self, current_month, current_day):
        """Get next Islamic event"""
        # Find the next event in the current year
        for event in self.islamic_events:
            if (event['month'] > current_month or 
                (event['month'] == current_month and event['day'] >= current_day)):
                
                days_until = self.calculate_days_until_event(
                    current_month, current_day, event['month'], event['day']
                )
                return event['name'], days_until
                
        # If no events left this year, return first event of next year
        first_event = self.islamic_events[0]
        days_until = self.calculate_days_until_next_year_event(
            current_month, current_day, first_event['month'], first_event['day']
        )
        return first_event['name'], days_until
        
    def get_upcoming_events(self, current_month, current_day):
        """Get list of upcoming events"""
        upcoming = []
        
        # Events in current year
        for event in self.islamic_events:
            if (event['month'] > current_month or 
                (event['month'] == current_month and event['day'] >= current_day)):
                
                days_until = self.calculate_days_until_event(
                    current_month, current_day, event['month'], event['day']
                )
                upcoming.append((event['name'], days_until, event['month'], event['day']))
                
        # Add next year events if needed
        if len(upcoming) < 8:
            for event in self.islamic_events:
                if len(upcoming) >= 8:
                    break
                    
                days_until = self.calculate_days_until_next_year_event(
                    current_month, current_day, event['month'], event['day']
                )
                upcoming.append((event['name'], days_until, event['month'], event['day']))
                
        # Sort by days until
        upcoming.sort(key=lambda x: x[1])
        return upcoming
        
    def calculate_days_until_event(self, current_month, current_day, event_month, event_day):
        """Calculate days until event in same Hijri year"""
        if current_month == event_month:
            return max(0, event_day - current_day)
            
        # Simplified calculation using average month length
        days = 0
        
        # Days remaining in current month
        days_in_month = [30, 29, 30, 29, 30, 29, 30, 29, 30, 29, 30, 29]
        days += days_in_month[current_month - 1] - current_day
        
        # Days in intervening months
        for month in range(current_month + 1, event_month):
            days += days_in_month[month - 1]
            
        # Days in event month
        days += event_day
        
        return days
        
    def calculate_days_until_next_year_event(self, current_month, current_day, event_month, event_day):
        """Calculate days until event in next Hijri year"""
        days_in_month = [30, 29, 30, 29, 30, 29, 30, 29, 30, 29, 30, 29]
        
        # Days remaining in current year
        days = days_in_month[current_month - 1] - current_day
        for month in range(current_month + 1, 13):
            days += days_in_month[month - 1]
            
        # Days from beginning of next year to event
        for month in range(1, event_month):
            days += days_in_month[month - 1]
        days += event_day
        
        return days
        
    def update(self):
        """Update Hijri Calendar app"""
        if self.view_mode == "main":
            if self.buttons.is_pressed('A'):
                self.view_mode = "events"
                self.draw_screen()
                time.sleep_ms(200)
            elif self.buttons.is_pressed('Y'):
                self.view_mode = "months"
                self.draw_screen()
                time.sleep_ms(200)
            elif self.buttons.is_pressed('X'):
                self.view_mode = "converter"
                self.draw_screen()
                time.sleep_ms(200)
                
        elif self.view_mode in ["events", "months", "converter"]:
            # Auto-refresh these views periodically
            if time.ticks_ms() % 10000 == 0:  # Every 10 seconds
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