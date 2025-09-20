"""
GeeekPi GPIO Expansion Module Hardware Configuration
Pin definitions and hardware constants for the GeeekPi GPIO Expansion Module
with 3.5" ST7796 display (320x480) and GT911 touch controller
"""

# Device identification
DEVICE_NAME = "GeeekPi GPIO Module 3.5inch"
DEVICE_ID = "GEEKPI_3_5"

# Joystick configuration (analog 2-axis joystick with center button)
JOYSTICK = {
    "X_PIN": 27,       # GP27 (ADC1) - X axis (analog)
    "Y_PIN": 26,       # GP26 (ADC0) - Y axis (analog)  
    "CENTER": 22,      # GP22 - joystick center button
    "TYPE": "analog",  # analog vs digital
    "PULL_UP": True,
    # Analog thresholds for direction detection
    "THRESHOLD_LOW": 20000,   # Below this = direction pressed
    "THRESHOLD_HIGH": 45000,  # Above this = opposite direction
    "CENTER_RANGE": 5000,     # Dead zone around center (32768)
    # Virtual pin mapping for compatibility with digital joystick interface
    "UP": -1,     # Will be determined by Y axis analog reading
    "DOWN": -1,   # Will be determined by Y axis analog reading
    "LEFT": -1,   # Will be determined by X axis analog reading
    "RIGHT": -1,  # Will be determined by X axis analog reading
}

# Button configuration (2 user buttons)
BUTTONS = {
    "A": 14,      # GP14 - Button 1 (Select/OK)
    "B": 15,      # GP15 - Button 2 (Back/Cancel)
    "X": -1,      # Not available - will be mapped to joystick directions
    "Y": -1,      # Not available - will be mapped to joystick directions
    "PULL_UP": True
}

# SPI configuration for display (ST7796)
SPI = {
    "ID": 0,      # SPI bus ID (SPI0)
    "SCK": 2,     # GP2 - SPI Clock
    "MOSI": 3,    # GP3 - SPI MOSI
    "MISO": -1,   # Not used for display-only SPI
    "BAUDRATE": 40000000,  # Reduced to 40MHz for more stable operation
    "POLARITY": 0,
    "PHASE": 0
}

# Display configuration (ST7796 320x480)
DISPLAY = {
    "DRIVER": "st7796",
    "WIDTH": 320,
    "HEIGHT": 480,
    "RESET": 7,      # GP7 - Display reset
    "DC": 6,         # GP6 - Data/Command pin
    "CS": 5,         # GP5 - Chip Select
    "BACKLIGHT": -1, # No dedicated backlight pin (always on or controlled via display commands)
    "ROTATION": 0,   # 0 degrees - portrait mode
    "COLOR_FORMAT": "RGB565"
}

# Touch controller configuration (GT911)
TOUCH = {
    "ENABLED": True,
    "DRIVER": "gt911",
    "I2C_ID": 0,     # I2C0
    "SDA_PIN": 8,    # GP8 - I2C SDA
    "SCL_PIN": 9,    # GP9 - I2C SCL
    "RST_PIN": 10,   # GP10 - Touch reset
    "INT_PIN": 11,   # GP11 - Touch interrupt
    "I2C_ADDR": 0x5D, # GT911 I2C address
    "WIDTH": 320,
    "HEIGHT": 480,
    "SWAP_XY": False,
    "INVERT_X": False,
    "INVERT_Y": False
}

# Battery/Power monitoring configuration (I2C)
BATTERY = {
    "SDA_PIN": 8,    # GP8 - Shared with touch I2C
    "SCL_PIN": 9,    # GP9 - Shared with touch I2C
    "I2C_ADDR": 0x36, # I2C address of UPS module (if present)
    "ENABLED": False  # Disabled by default unless UPS module is connected
}

# Additional hardware features
PERIPHERALS = {
    "BUZZER": {
        "ENABLED": True,
        "PIN": 13     # GP13 - Buzzer pin
    },
    "RGB_LED": {
        "ENABLED": True,
        "PIN": 12     # GP12 - RGB LED (WS2812)
    },
    "BLUE_LED_1": {
        "ENABLED": True,
        "PIN": 16     # GP16 - Blue LED 1
    },
    "BLUE_LED_2": {
        "ENABLED": True,
        "PIN": 17     # GP17 - Blue LED 2
    }
}

# Hardware capabilities
CAPABILITIES = {
    "JOYSTICK": True,
    "BUTTONS": True,
    "DISPLAY": True,
    "TOUCH": True,
    "BATTERY_MONITOR": False,  # Optional with external UPS
    "WIFI": True,
    "BLUETOOTH": False,
    "AUDIO": True,  # Via buzzer
    "SENSORS": False,
    "RGB_LED": True,
    "STATUS_LEDS": True
}

# Performance settings
PERFORMANCE = {
    "CPU_FREQ": 133000000,  # 133MHz for better performance with larger display
    "MEMORY_LIMIT": 264000,  # Approximate usable RAM in bytes
    "FLASH_SIZE": 2097152   # 2MB flash
}