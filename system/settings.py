"""
Settings App - System configuration interface
Clock settings, timezone selection, and WiFi configuration with onscreen keyboard
"""

import time
import machine
import network
from lib.st7789 import Color
from lib.battery_monitor import BatteryMonitor

class Settings:
    def __init__(self, display, joystick, buttons):
        """Initialize Settings app"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        # App state
        self.view_mode = "main"  # "main", "clock", "timezone", "wifi", "keyboard"
        self.selected_option = 0
        
        # Clock settings
        self.temp_time = [12, 0, 0]  # [hour, minute, second]
        self.temp_date = [2024, 1, 1]  # [year, month, day]
        self.clock_field = 0  # 0=hour, 1=minute, 2=second, 3=year, 4=month, 5=day
        
        # Timezone settings
        self.timezones = [
            ("UTC-12", -12), ("UTC-11", -11), ("UTC-10", -10), ("UTC-9", -9),
            ("UTC-8 PST", -8), ("UTC-7 MST", -7), ("UTC-6 CST", -6), ("UTC-5 EST", -5),
            ("UTC-4", -4), ("UTC-3", -3), ("UTC-2", -2), ("UTC-1", -1),
            ("UTC+0 GMT", 0), ("UTC+1", 1), ("UTC+2", 2), ("UTC+3", 3),
            ("UTC+4", 4), ("UTC+5", 5), ("UTC+5:30 IST", 5.5), ("UTC+6", 6),
            ("UTC+7", 7), ("UTC+8", 8), ("UTC+9 JST", 9), ("UTC+10", 10),
            ("UTC+11", 11), ("UTC+12", 12)
        ]
        self.selected_timezone = 12  # Default to UTC+0
        
        # WiFi settings
        self.wifi_networks = []
        self.selected_network = 0
        self.wifi_scanning = False
        self.wifi_password = ""
        self.wifi_connecting = False
        
        # Onscreen keyboard
        self.keyboard_layout = [
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l', 'DEL'],
            ['z', 'x', 'c', 'v', 'b', 'n', 'm', '.', '@', 'SPC'],
            ['1', '2', '3', '4', '5', '6', '7', '8', '9', '0'],
            ['!', '#', '$', '%', '&', '*', '(', ')', '-', 'OK']
        ]
        self.kb_row = 0
        self.kb_col = 0
        
        # Battery monitor
        self.battery_monitor = None
        self.init_battery_monitor()
        
    def init_battery_monitor(self):
        """Initialize battery monitor using hardware configuration"""
        try:
            # Import hardware configuration
            import sys
            sys.path.append('devices')
            from devices.hardware_runtime import get_hardware_config
            
            hw_config = get_hardware_config()
            battery_config = hw_config.get("BATTERY", {})
            
            # Only initialize if battery monitoring is enabled in hardware config
            if not battery_config.get("ENABLED", False):
                print("Battery monitoring disabled in hardware config")
                return
                
            # Use hardware-configured pins
            safe_configs = [
                {'sda': battery_config.get("SDA_PIN", 8), 'scl': battery_config.get("SCL_PIN", 9)},
                {'sda': 0, 'scl': 1},   # Fallback
                {'sda': 2, 'scl': 3},   # Fallback
            ]
            
            for config in safe_configs:
                try:
                    # Validate pins exist and are safe to use
                    sda_pin = config['sda']
                    scl_pin = config['scl']
                    
                    # Skip invalid pin numbers for Pico
                    if sda_pin > 28 or scl_pin > 28:
                        continue
                        
                    # Skip pins likely used by display (based on main.py)
                    display_pins = [8, 9, 10, 11, 12, 13]  # DC, CS, SCK, MOSI, RST, BL
                    if sda_pin in display_pins or scl_pin in display_pins:
                        continue
                    
                    monitor = BatteryMonitor(sda_pin=sda_pin, scl_pin=scl_pin)
                    if monitor.i2c:
                        # Quick test - don't hang on broken I2C
                        try:
                            info = monitor.get_battery_info()
                            if info['available']:
                                self.battery_monitor = monitor
                                print(f"✅ Battery monitor OK: SDA=GP{sda_pin}, SCL=GP{scl_pin}")
                                return
                        except:
                            # Failed to read battery info, try next config
                            continue
                except Exception as e:
                    # This config failed, try next one
                    print(f"⚠️ I2C config SDA=GP{config.get('sda','?')}, SCL=GP{config.get('scl','?')} failed: {e}")
                    continue
                    
            print("ℹ️ No UPS module detected (normal if no battery HAT installed)")
            
        except Exception as e:
            print(f"⚠️ Battery monitor init error (non-critical): {e}")
            # Don't let battery monitor issues crash the main app
            self.battery_monitor = None
    
    def write_config_file(self, ssid=None, password=None, timezone=None, dst_enabled=None):
        """Write config file while preserving all settings"""
        # Read current config to preserve all settings
        config = {}
        try:
            with open("config.txt", "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        config[key.strip()] = value.strip()
        except OSError:
            pass
        
        # Update only the specified values
        if ssid is not None:
            config["SSID"] = ssid
        if password is not None:
            config["PASSWORD"] = password
        if timezone is not None:
            config["TIMEZONE"] = str(timezone)
        if dst_enabled is not None:
            config["DST"] = 'true' if dst_enabled else 'false'
        
        # Write back the complete config
        try:
            with open("config.txt", "w") as f:
                f.write("# Device Configuration\n")
                f.write("#WAVESHARE_1_3 #GEEKPI_3_5\n")
                if "TARGET_HARDWARE" in config:
                    f.write(f"TARGET_HARDWARE={config['TARGET_HARDWARE']}\n")
                f.write("\n# Personal Configuration\n")
                if "FIRST_NAME" in config:
                    f.write(f"FIRST_NAME={config['FIRST_NAME']}\n")
                if "LAST_NAME" in config:
                    f.write(f"LAST_NAME={config['LAST_NAME']}\n")
                f.write("\n# WiFi Configuration\n")
                if "SSID" in config:
                    f.write(f"SSID={config['SSID']}\n")
                if "PASSWORD" in config:
                    f.write(f"PASSWORD={config['PASSWORD']}\n")
                if "TIMEZONE" in config:
                    f.write(f"TIMEZONE={config['TIMEZONE']}\n")
                if "DST" in config:
                    f.write(f"DST={config['DST']}\n")
        except Exception as e:
            print(f"Config write error: {e}")
            
    def get_battery_status_text(self):
        """Get battery status text for display"""
        if not self.battery_monitor:
            return "No UPS detected"
            
        try:
            info = self.battery_monitor.get_battery_info()
            
            if not info['available']:
                return "UPS unavailable"
                
            percentage = info['percentage']
            status = info['status']
            voltage = info['voltage']
            
            if percentage >= 0:
                icon = self.battery_monitor.get_battery_icon(percentage)
                return f"{icon} {percentage}% {status}"
            elif voltage > 0:
                return f"V:{voltage:.1f} {status}"
            else:
                return f"UPS: {status}"
                
        except Exception as e:
            return f"Battery error: {str(e)[:10]}"
        
    def init(self):
        """Initialize app when opened"""
        self.view_mode = "main"
        self.selected_option = 0
        self.load_current_time()
        self.draw_screen()
        
    def load_current_time(self):
        """Load current RTC time into temp variables"""
        try:
            rtc = machine.RTC()
            dt = rtc.datetime()
            # RTC format: (year, month, day, weekday, hours, minutes, seconds, subseconds)
            self.temp_time = [dt[4], dt[5], dt[6]]
            self.temp_date = [dt[0], dt[1], dt[2]]
        except:
            # Default values if RTC fails
            self.temp_time = [12, 0, 0]
            self.temp_date = [2024, 1, 1]
            
    def draw_screen(self):
        """Draw the appropriate screen"""
        self.display.fill(Color.BLACK)
        
        if self.view_mode == "main":
            self.draw_main_menu()
        elif self.view_mode == "clock":
            self.draw_clock_settings()
        elif self.view_mode == "timezone":
            self.draw_timezone_settings()
        elif self.view_mode == "wifi":
            self.draw_wifi_settings()
        elif self.view_mode == "launcher":
            self.draw_launcher_settings()
        elif self.view_mode == "keyboard":
            self.draw_keyboard()
        elif self.view_mode == "battery":
            self.draw_battery_view()
            
        self.display.display()
        
    def draw_main_menu(self):
        """Draw main settings menu"""
        # Title
        self.display.text("SETTINGS", 85, 10, Color.CYAN)
        
        # Menu options
        options = [
            ("Launcher Style", Color.MAGENTA),
            ("Clock & Date", Color.GREEN),
            ("Timezone", Color.YELLOW),
            ("WiFi Setup", Color.BLUE),
            ("Battery Info", Color.ORANGE),
            ("System Info", Color.PURPLE)
        ]
        
        y_start = 50
        for i, (option, color) in enumerate(options):
            y = y_start + i * 30
            
            # Highlight selected option
            if i == self.selected_option:
                self.display.fill_rect(10, y - 5, 220, 25, Color.WHITE)
                text_color = Color.BLACK
            else:
                text_color = color
                
            self.display.text(option, 20, y, text_color)
            
            # Add status indicators
            if i == 0:  # Clock
                try:
                    rtc = machine.RTC()
                    dt = rtc.datetime()
                    time_str = f"{dt[4]:02d}:{dt[5]:02d}"
                    self.display.text(time_str, 160, y, text_color)
                except:
                    self.display.text("--:--", 160, y, text_color)
                    
            elif i == 1:  # Timezone
                tz_name = self.timezones[self.selected_timezone][0][:8]
                self.display.text(tz_name, 150, y, text_color)
                
            elif i == 2:  # WiFi
                try:
                    wlan = network.WLAN(network.STA_IF)
                    if wlan.isconnected():
                        self.display.text("Connected", 140, y, Color.GREEN if i != self.selected_option else Color.GREEN)
                    else:
                        self.display.text("Not connected", 120, y, text_color)
                except:
                    self.display.text("Unavailable", 130, y, text_color)
                    
            elif i == 3:  # Battery
                battery_text = self.get_battery_status_text()
                # Truncate if too long
                if len(battery_text) > 15:
                    battery_text = battery_text[:12] + "..."
                battery_x = 240 - len(battery_text) * 8 - 5
                
                # Color based on battery level
                if self.battery_monitor:
                    try:
                        info = self.battery_monitor.get_battery_info()
                        if info['percentage'] >= 0:
                            if info['percentage'] <= 15:
                                battery_color = Color.RED
                            elif info['percentage'] <= 30:
                                battery_color = Color.YELLOW
                            else:
                                battery_color = Color.GREEN
                        else:
                            battery_color = text_color
                    except:
                        battery_color = text_color
                else:
                    battery_color = Color.GRAY
                    
                if i == self.selected_option:
                    battery_color = Color.BLACK
                    
                self.display.text(battery_text, battery_x, y, battery_color)
                    
        # Instructions
        self.display.text("Joy:Select A:Enter B:Home", 30, 200, Color.GRAY)
        
    def draw_clock_settings(self):
        """Draw clock and date settings"""
        self.display.text("CLOCK SETTINGS", 65, 10, Color.CYAN)
        
        # Current time display
        time_str = f"{self.temp_time[0]:02d}:{self.temp_time[1]:02d}:{self.temp_time[2]:02d}"
        self.display.text("Time:", 20, 40, Color.WHITE)
        
        # Highlight current field
        x_positions = [70, 95, 120]  # positions for hour, minute, second
        for i, (val, x_pos) in enumerate(zip(self.temp_time, x_positions)):
            if self.clock_field == i:
                self.display.fill_rect(x_pos - 2, 38, 20, 16, Color.YELLOW)
                self.display.text(f"{val:02d}", x_pos, 40, Color.BLACK)
            else:
                self.display.text(f"{val:02d}", x_pos, 40, Color.WHITE)
                
        # Separators
        self.display.text(":", 87, 40, Color.WHITE)
        self.display.text(":", 112, 40, Color.WHITE)
        
        # Date display
        date_str = f"{self.temp_date[0]}/{self.temp_date[1]:02d}/{self.temp_date[2]:02d}"
        self.display.text("Date:", 20, 70, Color.WHITE)
        
        # Date fields
        x_positions = [70, 110, 140]  # positions for year, month, day
        widths = [32, 20, 20]
        for i, (val, x_pos, width) in enumerate(zip(self.temp_date, x_positions, widths)):
            field_idx = i + 3  # offset by 3 for time fields
            if self.clock_field == field_idx:
                self.display.fill_rect(x_pos - 2, 68, width, 16, Color.YELLOW)
                if i == 0:  # year
                    self.display.text(f"{val}", x_pos, 70, Color.BLACK)
                else:
                    self.display.text(f"{val:02d}", x_pos, 70, Color.BLACK)
            else:
                if i == 0:  # year
                    self.display.text(f"{val}", x_pos, 70, Color.WHITE)
                else:
                    self.display.text(f"{val:02d}", x_pos, 70, Color.WHITE)
                    
        # Separators
        self.display.text("/", 102, 70, Color.WHITE)
        self.display.text("/", 132, 70, Color.WHITE)
        
        # Instructions
        self.display.text("Joy:Navigate U/D:Change", 20, 110, Color.GRAY)
        self.display.text("A:Apply B:Back", 70, 130, Color.GRAY)
        
        # Current RTC time for reference
        try:
            rtc = machine.RTC()
            dt = rtc.datetime()
            current = f"Current: {dt[4]:02d}:{dt[5]:02d} {dt[2]:02d}/{dt[1]:02d}/{dt[0]}"
            self.display.text(current, 20, 160, Color.DARK_GRAY)
        except:
            pass
            
    def draw_timezone_settings(self):
        """Draw timezone selection"""
        self.display.text("TIMEZONE", 85, 10, Color.CYAN)
        
        # Show 5 timezones at a time
        start_idx = max(0, self.selected_timezone - 2)
        end_idx = min(len(self.timezones), start_idx + 5)
        
        y_start = 40
        for i in range(start_idx, end_idx):
            y = y_start + (i - start_idx) * 25
            tz_name, tz_offset = self.timezones[i]
            
            # Highlight selected
            if i == self.selected_timezone:
                self.display.fill_rect(10, y - 3, 220, 20, Color.YELLOW)
                text_color = Color.BLACK
            else:
                text_color = Color.WHITE
                
            self.display.text(tz_name, 20, y, text_color)
            
            # Show offset
            if tz_offset >= 0:
                offset_str = f"+{tz_offset}"
            else:
                offset_str = f"{tz_offset}"
            self.display.text(offset_str, 180, y, text_color)
            
        # Instructions
        self.display.text("Joy:Select A:Apply B:Back", 40, 180, Color.GRAY)
        
        # Current timezone indicator
        current_tz = self.timezones[self.selected_timezone][0]
        self.display.text(f"Selected: {current_tz}", 20, 200, Color.GREEN)
        
    def draw_wifi_settings(self):
        """Draw WiFi configuration"""
        self.display.text("WiFi SETUP", 80, 10, Color.CYAN)
        
        if self.wifi_scanning:
            self.display.text("Scanning networks...", 50, 80, Color.YELLOW)
            self.display.text("Please wait", 85, 100, Color.WHITE)
            return
            
        if self.wifi_connecting:
            self.display.text("Connecting...", 75, 80, Color.YELLOW)
            self.display.text("Please wait", 85, 100, Color.WHITE)
            return
            
        # Current status
        try:
            wlan = network.WLAN(network.STA_IF)
            if wlan.isconnected():
                self.display.text("Status: Connected", 20, 30, Color.GREEN)
                config = wlan.ifconfig()
                ip = config[0] if config else "Unknown"
                if len(ip) > 15:
                    ip = ip[:12] + "..."
                self.display.text(f"IP: {ip}", 20, 45, Color.WHITE)
            else:
                self.display.text("Status: Disconnected", 20, 30, Color.RED)
        except:
            self.display.text("Status: WiFi Error", 20, 30, Color.RED)
            
        # Network list
        if self.wifi_networks:
            self.display.text("Available Networks:", 20, 70, Color.WHITE)
            
            # Show up to 6 networks
            start_idx = max(0, self.selected_network - 3)
            end_idx = min(len(self.wifi_networks), start_idx + 6)
            
            y_start = 90
            for i in range(start_idx, end_idx):
                y = y_start + (i - start_idx) * 15
                network_info = self.wifi_networks[i]
                ssid = network_info[0].decode('utf-8') if isinstance(network_info[0], bytes) else network_info[0]
                
                # Truncate long SSIDs
                if len(ssid) > 25:
                    ssid = ssid[:22] + "..."
                    
                # Highlight selected
                if i == self.selected_network:
                    self.display.fill_rect(15, y - 2, 210, 12, Color.BLUE)
                    text_color = Color.WHITE
                else:
                    text_color = Color.GRAY
                    
                self.display.text(ssid, 20, y, text_color)
                
                # Signal strength indicator
                rssi = network_info[3] if len(network_info) > 3 else -100
                signal_bars = max(1, min(4, (rssi + 100) // 15))
                bars_x = 200
                for bar in range(4):
                    if bar < signal_bars:
                        self.display.fill_rect(bars_x + bar * 3, y + 8 - bar * 2, 2, bar * 2 + 2, text_color)
                    else:
                        self.display.rect(bars_x + bar * 3, y + 8 - bar * 2, 2, bar * 2 + 2, Color.DARK_GRAY)
                        
            # Instructions
            self.display.text("Joy:Select A:Connect", 50, 210, Color.GRAY)
            self.display.text("Y:Scan X:Forget B:Back", 35, 225, Color.GRAY)
        else:
            self.display.text("No networks found", 60, 100, Color.GRAY)
            self.display.text("Press Y to scan", 70, 120, Color.WHITE)
            self.display.text("B:Back", 95, 200, Color.GRAY)
            
    def draw_keyboard(self):
        """Draw onscreen keyboard for WiFi password"""
        self.display.text("ENTER PASSWORD", 65, 5, Color.CYAN)
        
        # Show current password (masked)
        masked_password = "*" * len(self.wifi_password)
        if len(masked_password) > 25:
            masked_password = masked_password[:22] + "..."
        self.display.text(f"Pass: {masked_password}", 10, 25, Color.WHITE)
        
        # Keyboard layout
        key_width = 20
        key_height = 15
        start_x = 10
        start_y = 50
        
        for row_idx, row in enumerate(self.keyboard_layout):
            y = start_y + row_idx * (key_height + 2)
            
            for col_idx, key in enumerate(row):
                x = start_x + col_idx * (key_width + 2)
                
                # Highlight selected key
                if row_idx == self.kb_row and col_idx == self.kb_col:
                    self.display.fill_rect(x, y, key_width, key_height, Color.YELLOW)
                    text_color = Color.BLACK
                else:
                    self.display.rect(x, y, key_width, key_height, Color.WHITE)
                    text_color = Color.WHITE
                    
                # Draw key text
                if key == "SPC":
                    key_text = " "
                elif key == "DEL":
                    key_text = "<"
                elif key == "OK":
                    key_text = "OK"
                else:
                    key_text = key
                    
                # Center text in key
                text_x = x + (key_width - len(key_text) * 8) // 2
                text_y = y + (key_height - 8) // 2
                self.display.text(key_text, text_x, text_y, text_color)
                
        # Instructions
        self.display.text("Joy:Navigate A:Select B:Cancel", 20, 215, Color.GRAY)
        
    def draw_launcher_settings(self):
        """Draw launcher selection settings"""
        # Title
        self.display.text("LAUNCHER STYLE", 65, 10, Color.MAGENTA)
        
        # Load current launcher preference
        try:
            from launcher import LauncherManager
            current_launcher = LauncherManager.load_launcher_preference()
        except:
            current_launcher = "mindful"
            
        # Launcher options
        launcher_options = [
            ("mindful", "Intent-Based", "Ask what you want to do"),
            ("standard", "Classic Grid", "Traditional app layout")
        ]
        
        y_start = 60
        for i, (launcher_type, name, description) in enumerate(launcher_options):
            y = y_start + i * 60
            
            # Highlight current launcher
            if launcher_type == current_launcher:
                self.display.fill_rect(10, y - 5, 220, 50, Color.DARK_GRAY)
                
            # Highlight selected option
            if i == self.selected_option:
                self.display.fill_rect(15, y, 210, 40, Color.MAGENTA)
                text_color = Color.BLACK
                self.display.text(">", 20, y + 5, Color.BLACK)
            else:
                text_color = Color.WHITE if launcher_type != current_launcher else Color.CYAN
                
            # Launcher name
            self.display.text(name, 30, y + 5, text_color)
            
            # Description
            desc_color = Color.GRAY if i != self.selected_option else Color.DARK_GRAY
            self.display.text(description, 30, y + 20, desc_color)
            
            # Current indicator
            if launcher_type == current_launcher:
                self.display.text("(current)", 160, y + 5, Color.GREEN)
        
        # Instructions
        self.display.text("Joy:Select A:Apply B:Back", 50, 200, Color.GRAY)
        
    def draw_battery_view(self):
        """Draw detailed battery information view"""
        self.display.text("BATTERY STATUS", 70, 5, Color.CYAN)
        
        if not self.battery_monitor:
            self.display.text("No UPS Module Detected", 35, 30, Color.RED)
            
            self.display.text("Check connections:", 10, 55, Color.WHITE)
            self.display.text("UPS HAT -> Pico 2 WH", 10, 70, Color.CYAN)
            
            self.display.text("Expected I2C pins:", 10, 90, Color.WHITE)
            self.display.text("SDA: GP0, GP2, GP4, GP6", 10, 105, Color.GRAY)
            self.display.text("SCL: GP1, GP3, GP5, GP7", 10, 120, Color.GRAY)
            
            self.display.text("Try these addresses:", 10, 140, Color.WHITE)
            self.display.text("0x36, 0x6B, 0x17, 0x55", 10, 155, Color.GRAY)
            
            self.display.text("Ensure UPS HAT power", 10, 175, Color.YELLOW)
            self.display.text("and proper seating", 10, 190, Color.YELLOW)
            
            self.display.text("Press B to go back", 60, 215, Color.GRAY)
            return
            
        try:
            info = self.battery_monitor.get_battery_info()
            
            if not info['available']:
                self.display.text("UPS Module Found", 65, 40, Color.YELLOW)
                self.display.text("But no battery data", 55, 60, Color.ORANGE)
                self.display.text("available", 95, 80, Color.ORANGE)
            else:
                # Battery percentage and icon
                percentage = info['percentage']
                if percentage >= 0:
                    icon = self.battery_monitor.get_battery_icon(percentage)
                    
                    # Large percentage display
                    perc_text = f"{percentage}%"
                    perc_x = (240 - len(perc_text) * 12) // 2  # Approximate larger font
                    self.display.text(perc_text, perc_x, 35, Color.WHITE)
                    
                    # Battery icon
                    icon_x = (240 - len(icon) * 8) // 2
                    
                    # Color based on charge level
                    if percentage <= 15:
                        icon_color = Color.RED
                    elif percentage <= 30:
                        icon_color = Color.YELLOW
                    else:
                        icon_color = Color.GREEN
                        
                    self.display.text(icon, icon_x, 60, icon_color)
                    
                    # Status text
                    status = info['status']
                    status_x = (240 - len(status) * 8) // 2
                    self.display.text(status, status_x, 85, Color.CYAN)
                    
                    # Voltage if available
                    voltage = info['voltage']
                    if voltage > 0:
                        volt_text = f"Voltage: {voltage:.2f}V"
                        volt_x = (240 - len(volt_text) * 8) // 2
                        self.display.text(volt_text, volt_x, 105, Color.WHITE)
                    
                    # Battery health indicator
                    y_pos = 130
                    if percentage <= 15:
                        self.display.text("Battery Critical!", 60, y_pos, Color.RED)
                        self.display.text("Charge immediately", 50, y_pos + 15, Color.RED)
                    elif percentage <= 30:
                        self.display.text("Battery Low", 80, y_pos, Color.YELLOW)
                        self.display.text("Consider charging", 55, y_pos + 15, Color.YELLOW)
                    elif percentage >= 95:
                        self.display.text("Battery Full", 80, y_pos, Color.GREEN)
                    else:
                        self.display.text("Battery OK", 85, y_pos, Color.GREEN)
                        
                    # I2C info for debugging
                    i2c_text = f"I2C: {hex(self.battery_monitor.i2c_addr)}"
                    self.display.text(i2c_text, 10, 185, Color.GRAY)
                    
                else:
                    self.display.text("No percentage data", 55, 60, Color.ORANGE)
                    
                    # Show voltage if available
                    voltage = info['voltage']
                    if voltage > 0:
                        volt_text = f"Voltage: {voltage:.2f}V"
                        volt_x = (240 - len(volt_text) * 8) // 2
                        self.display.text(volt_text, volt_x, 85, Color.WHITE)
                        
                    status = info['status']
                    status_x = (240 - len(status) * 8) // 2
                    self.display.text(status, status_x, 110, Color.CYAN)
                    
        except Exception as e:
            self.display.text("Battery Read Error", 60, 60, Color.RED)
            error_text = str(e)[:20]
            error_x = (240 - len(error_text) * 8) // 2
            self.display.text(error_text, error_x, 85, Color.ORANGE)
            
        self.display.text("Press B to go back", 60, 215, Color.GRAY)
        
    def scan_wifi_networks(self):
        """Scan for available WiFi networks"""
        self.wifi_scanning = True
        self.draw_screen()
        
        try:
            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)
            
            # Scan for networks
            networks = wlan.scan()
            
            # Filter and sort by signal strength
            unique_networks = {}
            for net in networks:
                ssid = net[0].decode('utf-8') if net[0] else ""
                if ssid and ssid not in unique_networks:
                    unique_networks[ssid] = net
                    
            # Sort by signal strength (RSSI)
            self.wifi_networks = sorted(unique_networks.values(), key=lambda x: x[3], reverse=True)
            self.selected_network = 0
            
        except Exception as e:
            print(f"WiFi scan error: {e}")
            self.wifi_networks = []
            
        self.wifi_scanning = False
        
    def connect_to_wifi(self, ssid, password):
        """Connect to selected WiFi network"""
        self.wifi_connecting = True
        self.draw_screen()
        
        try:
            wlan = network.WLAN(network.STA_IF)
            wlan.active(True)
            
            # Disconnect from current network
            wlan.disconnect()
            time.sleep_ms(500)
            
            # Connect to new network
            wlan.connect(ssid, password)
            
            # Wait for connection (timeout after 10 seconds)
            timeout = 100  # 10 seconds
            while timeout > 0 and not wlan.isconnected():
                time.sleep_ms(100)
                timeout -= 1
                
            if wlan.isconnected():
                # Save credentials to file
                self.save_wifi_config(ssid, password)
                success = True
            else:
                success = False
                
        except Exception as e:
            print(f"WiFi connect error: {e}")
            success = False
            
        self.wifi_connecting = False
        
        # Show result
        if success:
            self.display.fill(Color.BLACK)
            self.display.text("Connected!", 85, 100, Color.GREEN)
            self.display.text("WiFi setup complete", 55, 120, Color.WHITE)
        else:
            self.display.fill(Color.BLACK)
            self.display.text("Connection failed!", 65, 100, Color.RED)
            self.display.text("Check password", 70, 120, Color.WHITE)
            
        self.display.display()
        time.sleep_ms(2000)
        
        return success
        
    def save_wifi_config(self, ssid, password):
        """Save WiFi configuration to file"""
        try:
            # Read current config if available
            timezone = -5  # Default
            dst_enabled = True  # Default
            try:
                with open("config.txt", "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("TIMEZONE="):
                            timezone = int(line.split("=")[1].strip())
                        elif line.startswith("DST="):
                            dst_setting = line.split("=")[1].strip().lower()
                            dst_enabled = dst_setting in ['true', '1', 'yes', 'on']
            except:
                pass
                
            # Write new config while preserving other settings
            self.write_config_file(ssid=ssid, password=password, timezone=timezone, dst_enabled=dst_enabled)
                
        except Exception as e:
            print(f"Save config error: {e}")
            
    def apply_clock_settings(self):
        """Apply clock settings to RTC"""
        try:
            rtc = machine.RTC()
            # RTC datetime format: (year, month, day, weekday, hours, minutes, seconds, subseconds)
            # Calculate weekday (0=Monday, 6=Sunday)
            year, month, day = self.temp_date
            hour, minute, second = self.temp_time
            
            # Simple weekday calculation (not 100% accurate but close enough)
            weekday = 0  # Default to Monday
            
            rtc.datetime((year, month, day, weekday, hour, minute, second, 0))
            
            # Show success message
            self.display.fill(Color.BLACK)
            self.display.text("Clock Updated!", 75, 100, Color.GREEN)
            self.display.text(f"{hour:02d}:{minute:02d} {day:02d}/{month:02d}/{year}", 60, 120, Color.WHITE)
            self.display.display()
            time.sleep_ms(1500)
            
            return True
            
        except Exception as e:
            print(f"RTC error: {e}")
            self.display.fill(Color.BLACK)
            self.display.text("Clock update failed!", 55, 100, Color.RED)
            self.display.display()
            time.sleep_ms(1500)
            return False
            
    def apply_timezone_settings(self):
        """Apply timezone settings"""
        try:
            # Update config.txt with new timezone
            ssid = "BFamily"  # Default
            password = "er0dMonzen"  # Default
            dst_enabled = True  # Default
            
            # Read current WiFi settings if available
            try:
                with open("config.txt", "r") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("SSID="):
                            ssid = line.split("=")[1].strip()
                        elif line.startswith("PASSWORD="):
                            password = line.split("=")[1].strip()
                        elif line.startswith("DST="):
                            dst_setting = line.split("=")[1].strip().lower()
                            dst_enabled = dst_setting in ['true', '1', 'yes', 'on']
            except:
                pass
                
            # Write updated config while preserving other settings
            tz_offset = int(self.timezones[self.selected_timezone][1])
            self.write_config_file(ssid=ssid, password=password, timezone=tz_offset, dst_enabled=dst_enabled)
                
            # Show success
            tz_name = self.timezones[self.selected_timezone][0]
            self.display.fill(Color.BLACK)
            self.display.text("Timezone Updated!", 65, 100, Color.GREEN)
            self.display.text(tz_name, 80, 120, Color.WHITE)
            self.display.display()
            time.sleep_ms(1500)
            
            return True
            
        except Exception as e:
            print(f"Timezone error: {e}")
            self.display.fill(Color.BLACK)
            self.display.text("Update failed!", 75, 100, Color.RED)
            self.display.display()
            time.sleep_ms(1500)
            return False
            
    def update(self):
        """Update Settings app"""
        if self.view_mode == "main":
            # Navigate main menu
            direction = self.joystick.get_direction_slow()
            if direction == 'UP':
                self.selected_option = max(0, self.selected_option - 1)
                self.draw_screen()
            elif direction == 'DOWN':
                self.selected_option = min(5, self.selected_option + 1)
                self.draw_screen()
                
            # Enter selected option
            if self.buttons.is_pressed('A'):
                if self.selected_option == 0:  # Launcher Style
                    self.view_mode = "launcher"
                    self.selected_option = 0  # Reset for launcher selection
                elif self.selected_option == 1:  # Clock
                    self.view_mode = "clock"
                    self.clock_field = 0
                    self.load_current_time()
                elif self.selected_option == 2:  # Timezone
                    self.view_mode = "timezone"
                elif self.selected_option == 3:  # WiFi
                    self.view_mode = "wifi"
                    if not self.wifi_networks:
                        self.scan_wifi_networks()
                elif self.selected_option == 4:  # Battery Info
                    self.view_mode = "battery"
                elif self.selected_option == 5:  # System Info
                    self.show_system_info()
                    
                self.draw_screen()
                time.sleep_ms(200)
                
        elif self.view_mode == "launcher":
            self.handle_launcher_input()
            
        elif self.view_mode == "clock":
            self.handle_clock_input()
            
        elif self.view_mode == "timezone":
            self.handle_timezone_input()
            
        elif self.view_mode == "wifi":
            self.handle_wifi_input()
            
        elif self.view_mode == "keyboard":
            self.handle_keyboard_input()
            
        # Check for exit
        if self.buttons.is_pressed('B'):
            if self.view_mode == "main":
                return False  # Exit app
            else:
                self.view_mode = "main"  # Back to main menu
                self.draw_screen()
                time.sleep_ms(200)
                
        return True
        
    def handle_launcher_input(self):
        """Handle launcher selection input"""
        # Navigation
        direction = self.joystick.get_direction_slow()
        if direction == 'UP':
            self.selected_option = max(0, self.selected_option - 1)
            self.draw_screen()
        elif direction == 'DOWN':
            self.selected_option = min(1, self.selected_option + 1)  # 0 or 1 for two launcher options
            self.draw_screen()
            
        # Apply launcher selection
        if self.buttons.is_pressed('A'):
            launcher_options = ["mindful", "standard"]
            selected_launcher = launcher_options[self.selected_option]
            
            try:
                from launcher import LauncherManager
                if LauncherManager.save_launcher_preference(selected_launcher):
                    # Show confirmation
                    self.display.fill(Color.BLACK)
                    self.display.text("LAUNCHER UPDATED!", 55, 100, Color.GREEN)
                    self.display.text("Restart to apply", 65, 120, Color.WHITE)
                    self.display.display()
                    time.sleep_ms(2000)
                else:
                    # Show error
                    self.display.fill(Color.BLACK)
                    self.display.text("SAVE FAILED", 75, 100, Color.RED)
                    self.display.text("Try again", 85, 120, Color.WHITE)
                    self.display.display()
                    time.sleep_ms(1500)
            except Exception as e:
                # Show error
                self.display.fill(Color.BLACK)
                self.display.text("ERROR", 95, 100, Color.RED)
                self.display.text(str(e)[:20], 30, 120, Color.WHITE)
                self.display.display()
                time.sleep_ms(1500)
                
            self.view_mode = "main"
            self.selected_option = 0
            self.draw_screen()
            time.sleep_ms(200)
        
    def handle_clock_input(self):
        """Handle clock setting input"""
        direction = self.joystick.get_direction_slow()
        
        if direction == 'LEFT':
            self.clock_field = max(0, self.clock_field - 1)
            self.draw_screen()
        elif direction == 'RIGHT':
            self.clock_field = min(5, self.clock_field + 1)
            self.draw_screen()
        elif direction == 'UP':
            if self.clock_field == 0:  # hour
                self.temp_time[0] = (self.temp_time[0] + 1) % 24
            elif self.clock_field == 1:  # minute
                self.temp_time[1] = (self.temp_time[1] + 1) % 60
            elif self.clock_field == 2:  # second
                self.temp_time[2] = (self.temp_time[2] + 1) % 60
            elif self.clock_field == 3:  # year
                self.temp_date[0] = min(2099, self.temp_date[0] + 1)
            elif self.clock_field == 4:  # month
                self.temp_date[1] = max(1, min(12, self.temp_date[1] + 1))
            elif self.clock_field == 5:  # day
                self.temp_date[2] = max(1, min(31, self.temp_date[2] + 1))
            self.draw_screen()
        elif direction == 'DOWN':
            if self.clock_field == 0:  # hour
                self.temp_time[0] = (self.temp_time[0] - 1) % 24
            elif self.clock_field == 1:  # minute
                self.temp_time[1] = (self.temp_time[1] - 1) % 60
            elif self.clock_field == 2:  # second
                self.temp_time[2] = (self.temp_time[2] - 1) % 60
            elif self.clock_field == 3:  # year
                self.temp_date[0] = max(2020, self.temp_date[0] - 1)
            elif self.clock_field == 4:  # month
                self.temp_date[1] = max(1, min(12, self.temp_date[1] - 1))
            elif self.clock_field == 5:  # day
                self.temp_date[2] = max(1, min(31, self.temp_date[2] - 1))
            self.draw_screen()
            
        # Apply settings
        if self.buttons.is_pressed('A'):
            if self.apply_clock_settings():
                self.view_mode = "main"
                self.draw_screen()
            time.sleep_ms(200)
            
    def handle_timezone_input(self):
        """Handle timezone selection input"""
        direction = self.joystick.get_direction_slow()
        
        if direction == 'UP':
            self.selected_timezone = max(0, self.selected_timezone - 1)
            self.draw_screen()
        elif direction == 'DOWN':
            self.selected_timezone = min(len(self.timezones) - 1, self.selected_timezone + 1)
            self.draw_screen()
            
        # Apply timezone
        if self.buttons.is_pressed('A'):
            if self.apply_timezone_settings():
                self.view_mode = "main"
                self.draw_screen()
            time.sleep_ms(200)
            
    def handle_wifi_input(self):
        """Handle WiFi input"""
        direction = self.joystick.get_direction_slow()
        
        if direction == 'UP' and self.wifi_networks:
            self.selected_network = max(0, self.selected_network - 1)
            self.draw_screen()
        elif direction == 'DOWN' and self.wifi_networks:
            self.selected_network = min(len(self.wifi_networks) - 1, self.selected_network + 1)
            self.draw_screen()
            
        # Connect to network
        if self.buttons.is_pressed('A') and self.wifi_networks:
            network_info = self.wifi_networks[self.selected_network]
            ssid = network_info[0].decode('utf-8') if isinstance(network_info[0], bytes) else network_info[0]
            
            # Start keyboard for password input
            self.wifi_password = ""
            self.kb_row = 0
            self.kb_col = 0
            self.view_mode = "keyboard"
            self.draw_screen()
            time.sleep_ms(200)
            
        # Scan networks
        if self.buttons.is_pressed('Y'):
            self.scan_wifi_networks()
            self.draw_screen()
            time.sleep_ms(200)
            
    def handle_keyboard_input(self):
        """Handle onscreen keyboard input"""
        direction = self.joystick.get_direction_slow()
        
        if direction == 'UP':
            self.kb_row = max(0, self.kb_row - 1)
            self.kb_col = min(len(self.keyboard_layout[self.kb_row]) - 1, self.kb_col)
            self.draw_screen()
        elif direction == 'DOWN':
            self.kb_row = min(len(self.keyboard_layout) - 1, self.kb_row + 1)
            self.kb_col = min(len(self.keyboard_layout[self.kb_row]) - 1, self.kb_col)
            self.draw_screen()
        elif direction == 'LEFT':
            self.kb_col = max(0, self.kb_col - 1)
            self.draw_screen()
        elif direction == 'RIGHT':
            self.kb_col = min(len(self.keyboard_layout[self.kb_row]) - 1, self.kb_col + 1)
            self.draw_screen()
            
        # Key selection
        if self.buttons.is_pressed('A'):
            key = self.keyboard_layout[self.kb_row][self.kb_col]
            
            if key == 'DEL':
                if self.wifi_password:
                    self.wifi_password = self.wifi_password[:-1]
            elif key == 'SPC':
                if len(self.wifi_password) < 50:
                    self.wifi_password += ' '
            elif key == 'OK':
                # Connect with password
                if self.wifi_networks:
                    network_info = self.wifi_networks[self.selected_network]
                    ssid = network_info[0].decode('utf-8') if isinstance(network_info[0], bytes) else network_info[0]
                    
                    if self.connect_to_wifi(ssid, self.wifi_password):
                        self.view_mode = "main"
                    else:
                        self.view_mode = "wifi"
                    self.draw_screen()
            else:
                if len(self.wifi_password) < 50:
                    self.wifi_password += key
                    
            self.draw_screen()
            time.sleep_ms(150)
            
    def show_system_info(self):
        """Show system information"""
        self.display.fill(Color.BLACK)
        self.display.text("SYSTEM INFO", 75, 10, Color.CYAN)
        
        y_pos = 40
        
        # Device info
        self.display.text("Device: Pi Pico 2 WH", 10, y_pos, Color.WHITE)
        y_pos += 20
        
        # Memory info
        try:
            import gc
            gc.collect()
            free_mem = gc.mem_free()
            self.display.text(f"Free RAM: {free_mem} bytes", 10, y_pos, Color.GREEN)
        except:
            self.display.text("Memory: Unknown", 10, y_pos, Color.GRAY)
        y_pos += 20
        
        # CPU frequency
        try:
            freq = machine.freq()
            self.display.text(f"CPU: {freq//1000000}MHz", 10, y_pos, Color.YELLOW)
        except:
            self.display.text("CPU: Unknown", 10, y_pos, Color.GRAY)
        y_pos += 20
        
        # WiFi MAC
        try:
            wlan = network.WLAN(network.STA_IF)
            mac = wlan.config('mac')
            mac_str = ':'.join([f'{b:02x}' for b in mac])
            if len(mac_str) > 20:
                mac_str = mac_str[:17] + "..."
            self.display.text(f"MAC: {mac_str}", 10, y_pos, Color.BLUE)
        except:
            self.display.text("MAC: Unknown", 10, y_pos, Color.GRAY)
        y_pos += 20
        
        # App count
        self.display.text(f"Apps: 14 installed", 10, y_pos, Color.PURPLE)
        y_pos += 20
        
        # Battery status if available
        if self.battery_monitor:
            try:
                info = self.battery_monitor.get_battery_info()
                if info['available'] and info['percentage'] >= 0:
                    battery_text = f"Battery: {info['percentage']}%"
                    self.display.text(battery_text, 10, y_pos, Color.GREEN)
                elif info['voltage'] > 0:
                    battery_text = f"UPS: {info['voltage']:.1f}V"
                    self.display.text(battery_text, 10, y_pos, Color.YELLOW)
                else:
                    self.display.text("UPS: Connected", 10, y_pos, Color.CYAN)
            except:
                self.display.text("UPS: Error", 10, y_pos, Color.RED)
        else:
            self.display.text("UPS: Not detected", 10, y_pos, Color.GRAY)
        
        self.display.text("Press any button", 65, 200, Color.GRAY)
        self.display.display()
        
        # Wait for button press
        while True:
            if (self.buttons.is_pressed('A') or self.buttons.is_pressed('B') or 
                self.buttons.is_pressed('X') or self.buttons.is_pressed('Y')):
                break
            time.sleep_ms(50)
            
        time.sleep_ms(200)  # Debounce
        
    def cleanup(self):
        """Cleanup when exiting app"""
        pass