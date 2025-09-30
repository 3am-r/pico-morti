"""
Main application entry point - Modular Launcher System
Clean architecture with pluggable launcher implementations
"""

import gc
import time
import sys
from machine import Pin, SPI, freq

# Force garbage collection before heavy imports
gc.collect()

# Add directories to path for MicroPython compatibility
sys.path.append('games')
sys.path.append('apps')
sys.path.append('themes')
sys.path.append('system')
sys.path.append('devices')

# Import hardware configuration
from devices.hardware_runtime import get_hardware_config, validate_hardware_config

# Import display driver based on hardware config
# This will be dynamically selected based on DISPLAY.DRIVER
from lib.joystick import Joystick
from lib.buttons import Buttons
from loader import Loader
from launcher import LauncherManager

# Don't import all apps at startup - import them lazily when needed
# This saves significant memory at startup

class MainApp:
    def __init__(self):
        """Initialize main application with device-agnostic hardware system"""
        # Validate hardware configuration
        if not validate_hardware_config():
            raise RuntimeError("Failed to load hardware configuration")
            
        # Get hardware configuration
        hw_config = get_hardware_config()
        
        # Set CPU frequency based on hardware performance settings
        freq(hw_config["PERFORMANCE"]["CPU_FREQ"])
        
        # Initialize SPI for display using hardware configuration
        spi_config = hw_config["SPI"]
        spi_kwargs = {
            "baudrate": spi_config["BAUDRATE"], 
            "polarity": spi_config["POLARITY"], 
            "phase": spi_config["PHASE"],
            "sck": Pin(spi_config["SCK"]), 
            "mosi": Pin(spi_config["MOSI"])
        }
        
        # Add MISO only if it's specified and valid
        if spi_config.get("MISO", -1) >= 0:
            spi_kwargs["miso"] = Pin(spi_config["MISO"])
            
        self.spi = SPI(spi_config["ID"], **spi_kwargs)
        
        print(f"SPI initialized: ID={spi_config['ID']}, Baudrate={spi_config['BAUDRATE']}")
        print(f"SPI pins: SCK={spi_config['SCK']}, MOSI={spi_config['MOSI']}, MISO={spi_config.get('MISO', 'None')}")
        
        # Initialize display using hardware configuration
        display_config = hw_config["DISPLAY"]
        driver_name = display_config.get("DRIVER", "st7789")
        
        # Import appropriate display driver
        if driver_name == "st7789":
            from lib.st7789 import ST7789 as DisplayDriver, Color
        elif driver_name == "st7796":
            from lib.st7796 import ST7796 as DisplayDriver, Color
        elif driver_name == "CO5300":
            from lib.co5300_amoled import CO5300_AMOLED as DisplayDriver, AMOLEDColor as Color
        elif driver_name == "ili9488":
            from lib.ili9488 import ILI9488 as DisplayDriver, Color
        else:
            raise ValueError(f"Unsupported display driver: {driver_name}")
        
        # Initialize display with appropriate driver
        if display_config["BACKLIGHT"] != -1:
            backlight_pin = Pin(display_config["BACKLIGHT"], Pin.OUT)
        else:
            backlight_pin = None
            
        self.display = DisplayDriver(
            spi=self.spi,
            width=display_config["WIDTH"],
            height=display_config["HEIGHT"],
            reset=Pin(display_config["RESET"], Pin.OUT),
            dc=Pin(display_config["DC"], Pin.OUT),
            cs=Pin(display_config["CS"], Pin.OUT),
            backlight=backlight_pin,
            rotation=display_config["ROTATION"]
        )
        
        # Make Color class globally available
        import builtins
        builtins.Color = Color
        
        # Initialize input devices
        # Check if device has keyboard support (PicoCalc)
        if hw_config.get("KEYBOARD") and hw_config["KEYBOARD"].get("ENABLED"):
            # Initialize STM32 keyboard controller
            from machine import I2C
            from lib.stm32_keyboard import STM32Keyboard, KeyboardButtons, KeyboardJoystick

            keyboard_config = hw_config["KEYBOARD"]
            i2c = I2C(0,
                      sda=Pin(keyboard_config["I2C_SDA"]),
                      scl=Pin(keyboard_config["I2C_SCL"]),
                      freq=keyboard_config["I2C_FREQ"])

            self.keyboard = STM32Keyboard(i2c, address=keyboard_config["I2C_ADDR"])

            # Create virtual joystick and buttons from keyboard
            self.joystick = KeyboardJoystick(self.keyboard)
            self.buttons = KeyboardButtons(self.keyboard)

        # Check if device has touch support
        elif hw_config.get("TOUCH") and hw_config["TOUCH"].get("ENABLED"):
            # Initialize touch controller for watch-style devices
            from machine import I2C
            from lib.ft3168_touch import FT3168Touch, TouchButtons

            touch_config = hw_config["TOUCH"]
            i2c = I2C(0,
                      sda=Pin(touch_config["I2C_SDA"]),
                      scl=Pin(touch_config["I2C_SCL"]),
                      freq=touch_config["I2C_FREQ"])

            self.touch_controller = FT3168Touch(
                i2c=i2c,
                address=touch_config["I2C_ADDR"],
                width=display_config["WIDTH"],
                height=display_config["HEIGHT"],
                int_pin=touch_config.get("INT_PIN"),
                rst_pin=touch_config.get("RST_PIN")
            )

            # Create virtual joystick and buttons from touch
            from lib.touch_joystick import TouchJoystick
            self.joystick = TouchJoystick(self.touch_controller)
            self.buttons = TouchButtons(self.touch_controller)
        else:
            # Traditional hardware buttons and joystick
            self.joystick = Joystick()
            self.buttons = Buttons()
        
        # Initialize apps
        self.apps = self.create_apps()
        
        # Initialize launcher system
        launcher_type = LauncherManager.load_launcher_preference()
        self.launcher_manager = LauncherManager(
            self.apps, self.display, self.joystick, self.buttons, launcher_type
        )
        
        # Application state
        self.running = True
        self.sleeping = False
        self.in_app = False
        self.current_app = None
        
        # Show startup
        self.show_startup()
        
    def create_apps(self):
        """Create and return list of all apps with lazy imports"""
        apps = []
        
        # Define app modules and classes for lazy loading
        app_modules = [
            ('journal', 'MicroJournal'),
            ('tracker', 'ActivityTracker'),
            ('energy_dial', 'EnergyDial'),
            ('gratitude', 'GratitudeProxy'),
            ('win_logger', 'WinLogger'),
            ('worry_box', 'WorryBox'),
            ('med_tracker', 'MedTracker'),
            ('questbits', 'QuestBits'),
            ('scars_stars', 'ScarsStars'),
            ('breath', 'Breath'),
            ('pet', 'XPet'),
            ('air_monkey', 'AirMonkey'),
            ('elemental', 'ElementalSandbox'),
            ('fidget_spinner', 'FidgetSpinner'),
            ('prayers', 'Prayers'),
            ('hijri_calendar', 'HijriCalendar'),
            ('qibla', 'QiblaCompass'),
            ('countdown', 'CountdownHub'),
            ('world_clock', 'WorldClock'),
            ('settings', 'Settings')
        ]
        
        # Import and create apps one by one to manage memory
        for module_name, class_name in app_modules:
            try:
                gc.collect()  # Garbage collect before each import
                module = __import__(module_name)
                app_class = getattr(module, class_name)
                app_instance = app_class(self.display, self.joystick, self.buttons)
                apps.append(app_instance)
            except Exception as e:
                print(f"Failed to load {module_name}: {e}")
        
        # Add time sync if available
        try:
            import time_sync
            apps.append(time_sync.TimeSyncApp(self.display, self.joystick, self.buttons))
        except ImportError:
            print("Time sync module not available")
            
        return apps
        
    def show_startup(self):
        """Show startup screen"""
        self.display.fill(Color.BLACK)
        
        # Loader and main title
        loader = Loader(self.display)
        loader.run()
        
        # Show launcher type
        launcher_type = self.launcher_manager.get_launcher_type()
        # Manual title case for MicroPython compatibility
        launcher_display = launcher_type[0].upper() + launcher_type[1:] if launcher_type else ""
        launcher_text = f"Launcher: {launcher_display}"
        x = (self.display.width - len(launcher_text) * 8) // 2
        y = self.display.height - 280  # Adjust Y position for larger displays
        self.display.text(launcher_text, x, y, Color.CYAN)
        
        self.display.display()
        time.sleep_ms(1500)
        
    def show_sleep_screen(self):
        """Show sleep screen"""
        self.display.fill(Color.BLACK)
        
        msg = "SLEEPING"
        x = (self.display.width - len(msg) * 8) // 2
        y = self.display.height // 2 - 40
        self.display.text(msg, x, y, Color.WHITE)
        
        instruction = "Press any button"
        x2 = (self.display.width - len(instruction) * 8) // 2
        self.display.text(instruction, x2, y + 20, Color.GRAY)
        
        instruction2 = "or move joystick"
        x3 = (self.display.width - len(instruction2) * 8) // 2
        self.display.text(instruction2, x3, y + 40, Color.GRAY)
        
        self.display.display()
        
        # Turn off backlight to save power
        if hasattr(self.display, 'backlight') and self.display.backlight:
            self.display.backlight.value(0)
            
    def wake_up(self):
        """Wake up from sleep"""
        if hasattr(self.display, 'backlight') and self.display.backlight:
            self.display.backlight.value(1)
            
        self.sleeping = False
        self.launcher_manager.draw_screen()
        time.sleep_ms(500)
        
    def handle_sleep_mode(self):
        """Handle input during sleep mode"""
        # Update button states
        self.buttons.update()

        # Check each button individually with is_pressed (debounced)
        if self.buttons.is_pressed('A'):
            self.wake_up()
            return
        if self.buttons.is_pressed('B'):
            self.wake_up()
            return
        if self.buttons.is_pressed('X'):
            self.wake_up()
            return
        if self.buttons.is_pressed('Y'):
            self.wake_up()
            return
            
        # Check joystick (any movement wakes up)
        if (not self.joystick.up_pin.value() or
            not self.joystick.down_pin.value() or
            not self.joystick.left_pin.value() or
            not self.joystick.right_pin.value() or
            not self.joystick.center_pin.value()):
            self.wake_up()
            return
            
    def show_goodbye(self):
        """Show goodbye screen"""
        self.display.fill(Color.BLACK)
        
        msg = "GOODBYE"
        x = (self.display.width - len(msg) * 8) // 2
        y = self.display.height // 2 - 20
        self.display.text(msg, x, y, Color.WHITE)
        
        msg2 = "Shutting down..."
        x2 = (self.display.width - len(msg2) * 8) // 2
        self.display.text(msg2, x2, y + 20, Color.GRAY)
        
        self.display.display()
        time.sleep_ms(1000)
        
        # Turn off display
        self.display.fill(Color.BLACK)
        self.display.display()
        if hasattr(self.display, 'backlight') and self.display.backlight:
            self.display.backlight.value(0)
            
    def run(self):
        """Main application loop"""
        self.launcher_manager.init()
        
        while self.running:
            try:
                if self.sleeping:
                    self.handle_sleep_mode()
                    time.sleep_ms(50)  # Reduce CPU usage during sleep
                elif self.in_app:
                    # Handle app execution
                    if not self.current_app.update():
                        # App wants to exit
                        self.in_app = False
                        self.current_app.cleanup()
                        self.current_app = None
                        self.launcher_manager.init()
                        gc.collect()
                else:
                    # Handle launcher
                    result = self.launcher_manager.handle_input()
                    
                    if result == "exit":
                        self.show_goodbye()
                        self.running = False
                    elif result == "sleep":
                        self.sleeping = True
                        self.show_sleep_screen()
                        # Clear any pending button states to prevent immediate wake
                        self.buttons.update()
                        time.sleep_ms(300)  # Brief delay to prevent immediate wake
                    elif isinstance(result, tuple) and result[0] == "launch_app":
                        # Launch the selected app
                        app = result[1]
                        self.current_app = app
                        self.in_app = True
                        app.init()
                    
                time.sleep_ms(10)  # Small delay to prevent excessive CPU usage
                
            except Exception as e:
                print(f"Error in main loop: {e}")
                import sys
                sys.print_exception(e)
                # Try to recover
                self.in_app = False
                self.current_app = None
                self.launcher_manager.init()
                time.sleep_ms(1000)

# Application entry point
if __name__ == "__main__":
    print("Starting Modular Launcher System...")
    app = MainApp()
    app.run()