"""
WiFi Time Synchronization Module
Connects to WiFi and syncs RTC with NTP servers for accurate time
Includes automatic daylight saving time (DST) handling
"""

import network
import ntptime
import machine
import time
from lib.st7789 import Color
from lib.dst_utils import get_current_timezone_offset, format_timezone_string

class WiFiTimeSync:
    def __init__(self, display=None):
        """Initialize WiFi time sync"""
        self.display = display
        self.wlan = network.WLAN(network.STA_IF)
        self.is_connected = False
        self.last_sync_time = 0
        self.base_timezone_hours = -5  # Standard timezone (e.g., -5 for EST)
        self.dst_enabled = True  # Enable automatic DST
        
        # Load WiFi credentials
        self.ssid = ""
        self.password = ""
        self.load_wifi_config()
        
    def load_wifi_config(self):
        """Load WiFi credentials from config file"""
        try:
            with open("config.txt", "r") as f:
                lines = f.readlines()
                for line in lines:
                    line = line.strip()
                    if line.startswith("SSID="):
                        self.ssid = line.split("=", 1)[1]
                    elif line.startswith("PASSWORD="):
                        self.password = line.split("=", 1)[1]
                    elif line.startswith("TIMEZONE="):
                        # Base timezone in hours (e.g., -5 for EST)
                        self.base_timezone_hours = int(line.split("=", 1)[1])
                    elif line.startswith("DST="):
                        # DST enabled/disabled
                        dst_setting = line.split("=", 1)[1].strip().lower()
                        self.dst_enabled = dst_setting in ['true', '1', 'yes', 'on']
        except:
            # No config file - will need to be created
            pass
            
    def save_wifi_config(self, ssid, password, timezone_hours=0, dst_enabled=True):
        """Save WiFi credentials to config file"""
        try:
            with open("config.txt", "w") as f:
                f.write(f"SSID={ssid}\n")
                f.write(f"PASSWORD={password}\n")
                f.write(f"TIMEZONE={timezone_hours}\n")
                f.write(f"DST={'true' if dst_enabled else 'false'}\n")
            self.ssid = ssid
            self.password = password
            self.base_timezone_hours = timezone_hours
            self.dst_enabled = dst_enabled
            return True
        except Exception as e:
            print(f"WiFi config save error: {e}")
            return False
            
    def show_status(self, message, color=Color.WHITE):
        """Show status message on display if available"""
        if self.display:
            self.display.fill_rect(10, 100, 220, 40, Color.BLACK)
            # Center the message
            msg_x = (240 - len(message) * 8) // 2
            self.display.text(message, msg_x, 110, color)
            self.display.display()
        print(message)
        
    def connect_wifi(self, timeout=10):
        """Connect to WiFi network"""
        if not self.ssid or not self.password:
            self.show_status("No WiFi config", Color.RED)
            return False
            
        if self.is_connected:
            return True
            
        self.show_status("Connecting WiFi...", Color.YELLOW)
        
        try:
            # Enable WiFi
            self.wlan.active(True)
            
            # Connect to network
            self.wlan.connect(self.ssid, self.password)
            
            # Wait for connection
            start_time = time.ticks_ms()
            while not self.wlan.isconnected():
                if time.ticks_diff(time.ticks_ms(), start_time) > timeout * 1000:
                    self.show_status("WiFi timeout", Color.RED)
                    return False
                time.sleep_ms(100)
                
            self.is_connected = True
            ip = self.wlan.ifconfig()[0]
            self.show_status(f"Connected: {ip}", Color.GREEN)
            return True
            
        except Exception as e:
            self.show_status(f"WiFi error: {str(e)[:15]}", Color.RED)
            return False
            
    def disconnect_wifi(self):
        """Disconnect from WiFi to save power"""
        try:
            self.wlan.disconnect()
            self.wlan.active(False)
            self.is_connected = False
            self.show_status("WiFi disconnected", Color.GRAY)
        except:
            pass
            
    def sync_time(self):
        """Sync RTC with NTP server"""
        if not self.connect_wifi():
            return False
            
        try:
            self.show_status("Syncing time...", Color.YELLOW)
            
            # Set NTP server (you can change this)
            ntptime.settime()
            
            # Get current UTC time
            utc_time = time.gmtime()
            
            # Calculate current timezone offset with DST
            current_timezone_hours = get_current_timezone_offset(self.base_timezone_hours, self.dst_enabled)
            timezone_offset_seconds = current_timezone_hours * 3600
            
            # Apply timezone offset
            local_timestamp = time.mktime(utc_time) + timezone_offset_seconds
            local_time = time.localtime(local_timestamp)
            
            # Set RTC
            rtc = machine.RTC()
            # RTC datetime format: (year, month, day, weekday, hours, minutes, seconds, subseconds)
            rtc.datetime((
                local_time[0],  # year
                local_time[1],  # month
                local_time[2],  # day
                local_time[6],  # weekday (0=Monday)
                local_time[3],  # hours
                local_time[4],  # minutes
                local_time[5],  # seconds
                0               # subseconds
            ))
            
            self.last_sync_time = time.ticks_ms()
            
            # Format time for display
            time_str = f"{local_time[3]:02d}:{local_time[4]:02d}:{local_time[5]:02d}"
            date_str = f"{local_time[2]:02d}/{local_time[1]:02d}/{local_time[0]}"
            tz_str = format_timezone_string(self.base_timezone_hours, self.dst_enabled)
            
            self.show_status(f"Time: {time_str} {tz_str}", Color.GREEN)
            time.sleep_ms(1000)
            self.show_status(f"Date: {date_str}", Color.GREEN)
            
            # Disconnect to save power
            self.disconnect_wifi()
            
            return True
            
        except Exception as e:
            self.show_status(f"NTP error: {str(e)[:15]}", Color.RED)
            self.disconnect_wifi()
            return False
            
    def should_sync_time(self):
        """Check if time sync is needed (every 24 hours)"""
        if self.last_sync_time == 0:
            return True
            
        # Sync every 24 hours
        return time.ticks_diff(time.ticks_ms(), self.last_sync_time) > 24 * 60 * 60 * 1000
        
    def get_formatted_time(self):
        """Get current time formatted as string"""
        try:
            rtc = machine.RTC()
            dt = rtc.datetime()
            return f"{dt[4]:02d}:{dt[5]:02d}:{dt[6]:02d}"
        except:
            return "00:00:00"
            
    def get_formatted_date(self):
        """Get current date formatted as string"""
        try:
            rtc = machine.RTC()
            dt = rtc.datetime()
            return f"{dt[0]}-{dt[1]:02d}-{dt[2]:02d}"
        except:
            return "2024-01-01"
            
    def setup_wizard(self, display, joystick, buttons):
        """WiFi setup wizard with UI"""
        self.display = display
        
        if self.ssid and self.password:
            # Test existing connection
            self.display.fill(Color.BLACK)
            self.display.text("WiFi SETUP", 75, 10, Color.CYAN)
            self.display.text("Testing connection...", 40, 50, Color.WHITE)
            self.display.display()
            
            if self.connect_wifi():
                self.display.text("Connection OK!", 70, 80, Color.GREEN)
                self.display.text("A:Sync B:Skip Y:Reconfig", 15, 150, Color.GRAY)
                self.display.display()
                
                while True:
                    if buttons.is_pressed('A'):
                        success = self.sync_time()
                        if success:
                            time.sleep_ms(2000)
                        return success
                    elif buttons.is_pressed('B'):
                        self.disconnect_wifi()
                        return False
                    elif buttons.is_pressed('Y'):
                        break  # Go to reconfig
                    time.sleep_ms(50)
                    
        # WiFi configuration needed
        self.display.fill(Color.BLACK)
        self.display.text("WiFi SETUP NEEDED", 45, 50, Color.YELLOW)
        self.display.text("Create config.txt", 25, 80, Color.WHITE)
        self.display.text("with your credentials:", 25, 100, Color.WHITE)
        self.display.text("", 10, 130, Color.CYAN)
        self.display.text("SSID=YourWiFiName", 10, 150, Color.CYAN)
        self.display.text("PASSWORD=YourPassword", 10, 170, Color.CYAN)
        self.display.text("TIMEZONE=-5", 10, 190, Color.CYAN)
        self.display.text("Press B to continue", 50, 220, Color.GRAY)
        self.display.display()
        
        while not buttons.is_pressed('B'):
            time.sleep_ms(50)
            
        return False
        
    def auto_sync_check(self):
        """Automatic sync check (call periodically)"""
        if self.should_sync_time():
            print("Auto-syncing time...")
            return self.sync_time()
        return True
        
    def get_current_timezone_info(self):
        """Get current timezone information including DST status"""
        current_offset = get_current_timezone_offset(self.base_timezone_hours, self.dst_enabled)
        tz_string = format_timezone_string(self.base_timezone_hours, self.dst_enabled)
        is_dst = current_offset != self.base_timezone_hours
        
        return {
            'base_timezone': self.base_timezone_hours,
            'current_offset': current_offset,
            'timezone_string': tz_string,
            'dst_enabled': self.dst_enabled,
            'is_dst_active': is_dst
        }