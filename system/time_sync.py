"""
Time Sync App - WiFi Time Synchronization Interface
User-friendly interface for setting up WiFi and syncing time
"""

import time
from lib.st7789 import Color
from lib.wifi_time import WiFiTimeSync

class TimeSyncApp:
    def __init__(self, display, joystick, buttons):
        """Initialize Time Sync app"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        self.wifi_sync = WiFiTimeSync(display)
        self.view_mode = "main"  # "main", "setup", "sync", "status"
        
    def init(self):
        """Initialize app when opened"""
        self.view_mode = "main"
        self.draw_screen()
        
    def draw_screen(self):
        """Draw the appropriate screen"""
        self.display.fill(Color.BLACK)
        
        if self.view_mode == "main":
            self.draw_main_view()
        elif self.view_mode == "setup":
            self.draw_setup_view()
        elif self.view_mode == "sync":
            self.draw_sync_view()
        elif self.view_mode == "status":
            self.draw_status_view()
            
        self.display.display()
        
    def draw_main_view(self):
        """Draw main time sync view"""
        # Title
        self.display.text("TIME SYNC", 80, 10, Color.CYAN)
        
        # Current time display
        current_time = self.wifi_sync.get_formatted_time()
        current_date = self.wifi_sync.get_formatted_date()
        
        self.display.text("Current Time:", 20, 40, Color.WHITE)
        # Large time display
        time_x = (240 - len(current_time) * 12) // 2  # Approximate larger font
        self.display.text(current_time, time_x, 60, Color.GREEN)
        
        self.display.text("Current Date:", 20, 90, Color.WHITE)
        date_x = (240 - len(current_date) * 8) // 2
        self.display.text(current_date, date_x, 110, Color.YELLOW)
        
        # WiFi status
        if self.wifi_sync.ssid:
            wifi_status = f"WiFi: {self.wifi_sync.ssid}"
            if len(wifi_status) > 25:
                wifi_status = wifi_status[:22] + "..."
        else:
            wifi_status = "WiFi: Not configured"
            
        self.display.text(wifi_status, 10, 140, Color.GRAY)
        
        # Last sync info
        if self.wifi_sync.last_sync_time > 0:
            sync_text = "Last sync: OK"
            sync_color = Color.GREEN
        else:
            sync_text = "Never synced"
            sync_color = Color.ORANGE
            
        sync_x = (240 - len(sync_text) * 8) // 2
        self.display.text(sync_text, sync_x, 160, sync_color)
        
        # Instructions
        self.display.text("A:Sync Now Y:Setup", 50, 190, Color.GRAY)
        self.display.text("X:Status B:Home", 60, 205, Color.GRAY)
        
    def draw_setup_view(self):
        """Draw WiFi setup instructions"""
        self.display.text("WiFi SETUP", 75, 10, Color.CYAN)
        
        self.display.text("1. Create file:", 10, 40, Color.WHITE)
        self.display.text("  config.txt", 10, 55, Color.YELLOW)
        
        self.display.text("2. Add your info:", 10, 80, Color.WHITE)
        self.display.text("SSID=YourWiFiName", 10, 100, Color.CYAN)
        self.display.text("PASSWORD=YourPass", 10, 115, Color.CYAN)
        self.display.text("TIMEZONE=-5", 10, 130, Color.CYAN)
        
        self.display.text("3. Restart device", 10, 155, Color.WHITE)
        
        self.display.text("Timezone examples:", 10, 180, Color.GRAY)
        self.display.text("EST=-5 PST=-8 GMT=0", 10, 195, Color.GRAY)
        
        self.display.text("Press B to go back", 50, 220, Color.GRAY)
        
    def draw_sync_view(self):
        """Draw time sync in progress"""
        self.display.text("TIME SYNC", 80, 10, Color.CYAN)
        
        # This view is handled by the WiFiTimeSync class
        # which will show status messages directly
        self.display.text("Syncing...", 90, 100, Color.YELLOW)
        self.display.text("Please wait", 85, 120, Color.WHITE)
        
    def draw_status_view(self):
        """Draw detailed status information"""
        self.display.text("TIME STATUS", 70, 10, Color.CYAN)
        
        # Current time info
        rtc_time = self.wifi_sync.get_formatted_time()
        rtc_date = self.wifi_sync.get_formatted_date()
        
        status_items = [
            (f"Time: {rtc_time}", Color.GREEN),
            (f"Date: {rtc_date}", Color.YELLOW),
        ]
        
        # WiFi info
        if self.wifi_sync.ssid:
            status_items.append((f"SSID: {self.wifi_sync.ssid[:15]}", Color.BLUE))
        else:
            status_items.append(("WiFi: Not set up", Color.RED))
            
        # Timezone info
        tz_hours = self.wifi_sync.timezone_offset // 3600
        if tz_hours == 0:
            tz_text = "Timezone: UTC"
        elif tz_hours > 0:
            tz_text = f"Timezone: UTC+{tz_hours}"
        else:
            tz_text = f"Timezone: UTC{tz_hours}"
        status_items.append((tz_text, Color.PURPLE))
        
        # Connection status
        if self.wifi_sync.is_connected:
            status_items.append(("Connected: YES", Color.GREEN))
        else:
            status_items.append(("Connected: NO", Color.GRAY))
            
        # Draw status items
        y_pos = 40
        for item, color in status_items:
            self.display.text(item, 10, y_pos, color)
            y_pos += 20
            
        # Sync recommendations
        if not self.wifi_sync.ssid:
            rec_text = "Setup WiFi first"
            rec_color = Color.RED
        elif self.wifi_sync.last_sync_time == 0:
            rec_text = "Sync recommended"
            rec_color = Color.ORANGE
        elif self.wifi_sync.should_sync_time():
            rec_text = "Sync needed (24h+)"
            rec_color = Color.YELLOW
        else:
            rec_text = "Sync up to date"
            rec_color = Color.GREEN
            
        self.display.text(rec_text, 10, y_pos + 20, rec_color)
        
        self.display.text("Press B to go back", 50, 220, Color.GRAY)
        
    def perform_sync(self):
        """Perform time synchronization"""
        self.view_mode = "sync"
        self.draw_screen()
        
        # Show sync status
        success = self.wifi_sync.sync_time()
        
        # Brief result display
        if success:
            self.display.fill_rect(50, 140, 140, 40, Color.BLACK)
            self.display.text("Sync successful!", 60, 150, Color.GREEN)
        else:
            self.display.fill_rect(50, 140, 140, 40, Color.BLACK)
            self.display.text("Sync failed!", 80, 150, Color.RED)
        
        self.display.display()
        time.sleep_ms(2000)
        
        # Return to main view
        self.view_mode = "main"
        self.draw_screen()
        
    def update(self):
        """Update Time Sync app"""
        if self.view_mode == "main":
            if self.buttons.is_pressed('A'):
                # Sync now
                self.perform_sync()
                time.sleep_ms(200)
                
            elif self.buttons.is_pressed('Y'):
                # Setup instructions
                self.view_mode = "setup"
                self.draw_screen()
                time.sleep_ms(200)
                
            elif self.buttons.is_pressed('X'):
                # Status view
                self.view_mode = "status"
                self.draw_screen()
                time.sleep_ms(200)
                
        elif self.view_mode in ["setup", "status"]:
            if self.buttons.is_pressed('B'):
                self.view_mode = "main"
                self.draw_screen()
                time.sleep_ms(200)
                
        # Check for exit (only from main view)
        if self.buttons.is_pressed('B') and self.view_mode == "main":
            return False
            
        return True
        
    def cleanup(self):
        """Cleanup when exiting app"""
        # Disconnect WiFi to save power
        self.wifi_sync.disconnect_wifi()