"""
Waveshare Pico-LCD-1.3 Hardware Configuration
Pin definitions and hardware constants for the Waveshare Pico-LCD-1.3 board
"""

# Device identification
DEVICE_NAME = "Waveshare Pico-LCD-1.3"
DEVICE_ID = "WAVESHARE_1.3"

# Joystick configuration (digital 5-way joystick)
JOYSTICK = {
    "UP": 2,
    "DOWN": 18,
    "LEFT": 16,
    "RIGHT": 20,
    "CENTER": 3,
    "TYPE": "digital",  # digital vs analog
    "PULL_UP": True
}

# Button configuration (4 user buttons)
BUTTONS = {
    "A": 15,
    "B": 17,
    "X": 19,
    "Y": 21,
    "PULL_UP": True
}

# SPI configuration for display
SPI = {
    "ID": 1,  # SPI bus ID
    "SCK": 10,  # SPI Clock
    "MOSI": 11,  # SPI MOSI (Master Out Slave In)
    "BAUDRATE": 62500000,
    "POLARITY": 0,
    "PHASE": 0
}

# Display configuration (ST7789 240x240)
DISPLAY = {
    "DRIVER": "st7789",
    "WIDTH": 240,
    "HEIGHT": 240,
    "RESET": 12,
    "DC": 8,  # Data/Command pin
    "CS": 9,  # Chip Select
    "BACKLIGHT": 13,
    "ROTATION": 0,  # 0 degrees - screen upright with joystick on left
    "COLOR_FORMAT": "RGB565"
}

# Battery/Power monitoring configuration (I2C)
BATTERY = {
    "SDA_PIN": 0,  # I2C SDA pin
    "SCL_PIN": 1,  # I2C SCL pin
    "I2C_ADDR": 0x36,  # I2C address of UPS module
    "ENABLED": True
}

# Hardware capabilities
CAPABILITIES = {
    "JOYSTICK": True,
    "BUTTONS": True,
    "DISPLAY": True,
    "BATTERY_MONITOR": True,
    "WIFI": True,
    "BLUETOOTH": False,
    "AUDIO": False,
    "SENSORS": False
}

# Performance settings
PERFORMANCE = {
    "CPU_FREQ": 125000000,  # 125MHz
    "MEMORY_LIMIT": 264000,  # Approximate usable RAM in bytes
    "FLASH_SIZE": 2097152   # 2MB flash
}