"""
Hardware Configuration for PicoCalc Handheld
Built on ClockworkPi v2.0 mainboard with Raspberry Pi Pico
4-inch 320×320 IPS display, QWERTY keyboard, dual 18650 batteries
"""

from machine import Pin

HARDWARE_CONFIG = {
    # Device identification
    "DEVICE_NAME": "PicoCalc Handheld",
    "DEVICE_TYPE": "PICOCALC",
    "DEVICE_VARIANT": "CLOCKWORKPI_V2",
    "FORM_FACTOR": "HANDHELD",

    # Display configuration - 4-inch IPS
    "DISPLAY": {
        "WIDTH": 320,
        "HEIGHT": 320,
        "DRIVER": "ili9488",  # ILI9488 driver for 4-inch IPS
        "TYPE": "IPS",
        "INTERFACE": "SPI",
        "COLOR_DEPTH": 16,  # RGB565
        "ROTATION": 0,
        # SPI pins for display
        "CS": 9,       # Chip Select
        "DC": 8,       # Data/Command
        "RESET": 15,   # Reset
        "BACKLIGHT": 13,  # Backlight PWM control
        "BRIGHTNESS_CONTROL": True,
        "REFRESH_RATE": 60,
        "VIEWING_ANGLE": 170,
        "SIZE_INCHES": 4.0
    },

    # Keyboard configuration - STM32 controlled via I2C
    "KEYBOARD": {
        "ENABLED": True,
        "TYPE": "QWERTY",
        "CONTROLLER": "STM32",
        "INTERFACE": "I2C",
        "I2C_ADDR": 0x5F,  # STM32 keyboard controller address
        "I2C_SDA": 4,
        "I2C_SCL": 5,
        "I2C_FREQ": 400000,
        "BACKLIGHT": True,
        "BACKLIGHT_PIN": 22,  # Keyboard backlight control
        "LAYOUT": "COMPACT_QWERTY",
        "KEYS": {
            # Special keys mapping
            "MODIFIER_KEYS": ["SHIFT", "FN", "ALT", "CTRL"],
            "FUNCTION_KEYS": ["F1", "F2", "F3", "F4"],
            "NAVIGATION": ["UP", "DOWN", "LEFT", "RIGHT", "ENTER", "ESC"],
            "SYMBOLS": True,
            "NUMBERS": True
        },
        "KEY_REPEAT": True,
        "REPEAT_DELAY": 500,  # ms before repeat starts
        "REPEAT_RATE": 30     # ms between repeats
    },

    # SPI configuration for display
    "SPI": {
        "ID": 0,
        "BAUDRATE": 62500000,  # 62.5MHz for fast display
        "SCK": 10,     # Serial Clock
        "MOSI": 11,    # Master Out Slave In
        "MISO": 12,    # Master In Slave Out (if needed)
        "POLARITY": 0,
        "PHASE": 0
    },

    # Joystick/D-Pad configuration (using keyboard arrows)
    "JOYSTICK": {
        "ENABLED": False,  # Use keyboard navigation instead
        "KEYBOARD_EMULATION": True,  # Use keyboard arrows as joystick
        "UP_KEY": "UP",
        "DOWN_KEY": "DOWN",
        "LEFT_KEY": "LEFT",
        "RIGHT_KEY": "RIGHT",
        "CENTER_KEY": "ENTER"
    },

    # Buttons configuration (mapped to keyboard keys)
    "BUTTONS": {
        "BUTTON_A": "SPACE",    # Map to space key
        "BUTTON_B": "ESC",      # Map to escape key
        "BUTTON_X": "X",        # Map to X key
        "BUTTON_Y": "Y",        # Map to Y key
        "START": "ENTER",       # Map to enter key
        "SELECT": "TAB",        # Map to tab key
        "KEYBOARD_MAPPED": True,
        "PHYSICAL_BUTTONS": False
    },

    # Audio configuration
    "AUDIO": {
        "ENABLED": True,
        "TYPE": "STEREO",
        "OUTPUT": {
            "SPEAKERS": {
                "ENABLED": True,
                "TYPE": "PWM",
                "LEFT_PIN": 16,
                "RIGHT_PIN": 17,
                "AMPLIFIER": "BUILTIN",
                "MAX_VOLUME": 100
            },
            "HEADPHONE": {
                "ENABLED": True,
                "TYPE": "3.5MM_JACK",
                "DETECT_PIN": 18,  # Headphone detection
                "AUTO_SWITCH": True  # Auto switch to headphones when plugged
            }
        },
        "PWM_FREQUENCY": 22050,  # Audio PWM frequency
        "SAMPLE_RATE": 22050,
        "BIT_DEPTH": 8
    },

    # Storage configuration
    "STORAGE": {
        "INTERNAL_FLASH": 2 * 1024 * 1024,  # 2MB Pico internal
        "PSRAM": 8 * 1024 * 1024,  # 8MB onboard PSRAM
        "SD_CARD": {
            "ENABLED": True,
            "TYPE": "FULL_SIZE",  # Full-size SD card slot
            "CS": 5,
            "MISO": 3,
            "MOSI": 4,
            "SCLK": 2,
            "DETECT_PIN": 6,  # Card detection pin
            "MAX_SPEED": 25000000  # 25MHz SD card speed
        }
    },

    # Power management - Dual 18650 batteries
    "POWER": {
        "ENABLED": True,
        "TYPE": "DUAL_18650",
        "BATTERY": {
            "COUNT": 2,
            "TYPE": "18650_LITHIUM",
            "VOLTAGE_NOMINAL": 3.7,  # Per cell
            "VOLTAGE_MAX": 4.2,       # Per cell
            "VOLTAGE_MIN": 3.0,       # Per cell
            "CAPACITY": 3000,         # mAh per cell (user-supplied)
            "CONFIGURATION": "PARALLEL",  # Or SERIES depending on design
            "MONITOR_PIN": 26,        # ADC pin for battery monitoring
            "CHARGE_DETECT": 27       # Charging detection pin
        },
        "CHARGING": {
            "ENABLED": True,
            "TYPE": "USB_C",
            "MAX_CURRENT": 2000,  # mA charging current
            "CHARGE_LED": 28      # Charging indicator LED
        },
        "POWER_MANAGEMENT": {
            "AUTO_SLEEP": True,
            "SLEEP_TIMEOUT": 300000,  # 5 minutes
            "LOW_BATTERY_WARNING": 15,  # Percentage
            "CRITICAL_BATTERY": 5        # Percentage
        }
    },

    # GPIO expansion
    "GPIO": {
        "PICO_EXPOSED": {
            "PINS": [0, 1, 2, 3, 14, 19, 20, 21],  # Available GPIO pins
            "TYPE": "HEADER",
            "VOLTAGE": 3.3
        },
        "STM32_EXPOSED": {
            "PINS": [0, 1, 2, 3],  # STM32 GPIO pins
            "TYPE": "HEADER",
            "VOLTAGE": 3.3,
            "I2C_ADDR": 0x5E  # For GPIO expansion via I2C
        }
    },

    # USB ports
    "USB": {
        "USB_C": {
            "ENABLED": True,
            "PURPOSE": ["CHARGING", "POWER", "DATA"],
            "OTG": False,
            "POWER_DELIVERY": False
        },
        "MICRO_USB": {
            "ENABLED": True,
            "PURPOSE": ["FIRMWARE", "DEBUG"],
            "DEDICATED": True
        }
    },

    # LED indicators
    "LED": {
        "POWER_LED": {
            "ENABLED": True,
            "PIN": 25,  # Pico onboard LED
            "COLOR": "GREEN"
        },
        "STATUS_LED": {
            "ENABLED": True,
            "PIN": 29,
            "COLOR": "BLUE",
            "PWM_CAPABLE": True
        },
        "CHARGE_LED": {
            "ENABLED": True,
            "PIN": 28,
            "COLOR": "RED"
        }
    },

    # Performance settings
    "PERFORMANCE": {
        "CPU_FREQ": 133000000,  # 133MHz standard
        "USE_PSRAM": True,
        "DISPLAY_BUFFER": "DOUBLE",
        "KEYBOARD_POLLING_RATE": 100,  # Hz
        "LOW_POWER_MODE": True
    },

    # Handheld-specific features
    "HANDHELD_FEATURES": {
        "PORTABLE": True,
        "BATTERY_POWERED": True,
        "KEYBOARD_INPUT": True,
        "GAMING_CONTROLS": True,
        "PRODUCTIVITY": True,
        "CALCULATOR_MODE": True,  # PicoCalc specific
        "TERMINAL_MODE": True,    # Terminal emulator support
        "TEXT_EDITOR": True,      # Text editing with keyboard
        "PROGRAMMING": True       # On-device programming
    },

    # Capabilities
    "CAPABILITIES": {
        "DISPLAY": True,
        "TOUCH": False,
        "KEYBOARD": True,
        "AUDIO": True,
        "STORAGE": True,
        "WIRELESS": False,  # No built-in WiFi/BT on base Pico
        "BATTERY": True,
        "EXPANDABLE": True
    }
}

def get_hardware_config():
    """Return hardware configuration for PicoCalc Handheld"""
    return HARDWARE_CONFIG

def init_hardware():
    """Initialize PicoCalc-specific hardware"""
    import machine

    # Set CPU frequency
    machine.freq(HARDWARE_CONFIG["PERFORMANCE"]["CPU_FREQ"])

    # Initialize I2C for keyboard controller
    from machine import I2C, Pin
    keyboard_config = HARDWARE_CONFIG["KEYBOARD"]
    i2c = I2C(0,
              scl=Pin(keyboard_config["I2C_SCL"]),
              sda=Pin(keyboard_config["I2C_SDA"]),
              freq=keyboard_config["I2C_FREQ"])

    # Initialize keyboard backlight if enabled
    if keyboard_config["BACKLIGHT"]:
        kb_backlight = Pin(keyboard_config["BACKLIGHT_PIN"], Pin.OUT)
        kb_backlight.value(1)  # Turn on keyboard backlight

    # Initialize audio system
    if HARDWARE_CONFIG["AUDIO"]["ENABLED"]:
        from machine import PWM
        # Initialize PWM for speakers
        left_speaker = PWM(Pin(HARDWARE_CONFIG["AUDIO"]["OUTPUT"]["SPEAKERS"]["LEFT_PIN"]))
        right_speaker = PWM(Pin(HARDWARE_CONFIG["AUDIO"]["OUTPUT"]["SPEAKERS"]["RIGHT_PIN"]))
        left_speaker.freq(HARDWARE_CONFIG["AUDIO"]["PWM_FREQUENCY"])
        right_speaker.freq(HARDWARE_CONFIG["AUDIO"]["PWM_FREQUENCY"])

    # Initialize SD card if present
    if HARDWARE_CONFIG["STORAGE"]["SD_CARD"]["ENABLED"]:
        detect_pin = Pin(HARDWARE_CONFIG["STORAGE"]["SD_CARD"]["DETECT_PIN"], Pin.IN, Pin.PULL_UP)
        if detect_pin.value() == 0:  # Card detected (active low)
            print("SD card detected")
            # Initialize SD card interface
            # This would require SD card driver implementation

    # Initialize battery monitoring
    if HARDWARE_CONFIG["POWER"]["ENABLED"]:
        from machine import ADC
        battery_adc = ADC(Pin(HARDWARE_CONFIG["POWER"]["BATTERY"]["MONITOR_PIN"]))
        # Set up battery monitoring

    # Initialize status LEDs
    power_led = Pin(HARDWARE_CONFIG["LED"]["POWER_LED"]["PIN"], Pin.OUT)
    power_led.value(1)  # Turn on power LED

    return i2c

def get_battery_status():
    """Get battery status from dual 18650 cells"""
    from machine import ADC, Pin

    battery_config = HARDWARE_CONFIG["POWER"]["BATTERY"]
    battery_adc = ADC(Pin(battery_config["MONITOR_PIN"]))

    # Read battery voltage (assuming voltage divider)
    adc_value = battery_adc.read_u16()
    voltage = (adc_value / 65535) * 3.3 * 2  # Assuming 2:1 voltage divider

    # Calculate percentage based on battery configuration
    if battery_config["CONFIGURATION"] == "PARALLEL":
        # Parallel: voltage same as single cell, capacity doubled
        voltage_min = battery_config["VOLTAGE_MIN"]
        voltage_max = battery_config["VOLTAGE_MAX"]
    else:  # SERIES
        # Series: voltage doubled, capacity same as single cell
        voltage_min = battery_config["VOLTAGE_MIN"] * 2
        voltage_max = battery_config["VOLTAGE_MAX"] * 2

    percentage = int(((voltage - voltage_min) / (voltage_max - voltage_min)) * 100)
    percentage = max(0, min(100, percentage))

    # Check charging status
    charge_pin = Pin(HARDWARE_CONFIG["POWER"]["CHARGING"]["CHARGE_DETECT"], Pin.IN)
    charging = charge_pin.value() == 1

    return {
        "voltage": voltage,
        "percentage": percentage,
        "charging": charging,
        "battery_count": battery_config["COUNT"],
        "configuration": battery_config["CONFIGURATION"]
    }

def set_keyboard_backlight(enabled):
    """Control keyboard backlight"""
    if HARDWARE_CONFIG["KEYBOARD"]["BACKLIGHT"]:
        from machine import Pin
        kb_backlight = Pin(HARDWARE_CONFIG["KEYBOARD"]["BACKLIGHT_PIN"], Pin.OUT)
        kb_backlight.value(1 if enabled else 0)

def set_display_brightness(level):
    """Set display backlight brightness (0-100)"""
    from machine import Pin, PWM

    backlight_pin = HARDWARE_CONFIG["DISPLAY"]["BACKLIGHT"]
    if backlight_pin and HARDWARE_CONFIG["DISPLAY"]["BRIGHTNESS_CONTROL"]:
        backlight = PWM(Pin(backlight_pin))
        backlight.freq(1000)  # 1kHz PWM frequency
        duty = int((level / 100) * 65535)
        backlight.duty_u16(duty)