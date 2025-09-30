"""
Hardware Configuration for Waveshare ESP32-S3-Touch-AMOLED-2.06
High-performance wearable watch-style development board
2.06" AMOLED capacitive touch display with 410×502 resolution
"""

from machine import Pin

HARDWARE_CONFIG = {
    # Device identification
    "DEVICE_NAME": "ESP32-S3-Touch-AMOLED-2.06",
    "DEVICE_TYPE": "WAVESHARE_ESP32_S3_AMOLED",
    "DEVICE_VARIANT": "2.06_INCH",
    "FORM_FACTOR": "WEARABLE_WATCH",

    # Display configuration - CO5300 AMOLED driver
    "DISPLAY": {
        "WIDTH": 410,
        "HEIGHT": 502,
        "DRIVER": "CO5300",
        "TYPE": "AMOLED",
        "INTERFACE": "QSPI",
        "COLOR_DEPTH": 24,  # 16.7M colors
        "ROTATION": 0,
        # QSPI pins for CO5300 AMOLED
        "CS": 11,      # Chip Select
        "DC": 10,      # Data/Command
        "RST": 12,     # Reset
        "SCLK": 6,     # Serial Clock
        "MOSI": 7,     # Data Out
        "MISO": 8,     # Data In
        "BACKLIGHT": None,  # AMOLED doesn't need backlight
        "BRIGHTNESS_CONTROL": True,  # Through CO5300 commands
        "REFRESH_RATE": 60,  # AMOLED fast response
        "VIEWING_ANGLE": 178,  # Wide viewing angle
        "CONTRAST_RATIO": 100000  # High AMOLED contrast
    },

    # Touch controller - FT3168 capacitive touch
    "TOUCH": {
        "ENABLED": True,
        "DRIVER": "FT3168",
        "INTERFACE": "I2C",
        "MAX_POINTS": 5,  # Multi-touch support
        "I2C_ADDR": 0x38,
        "I2C_SDA": 42,
        "I2C_SCL": 41,
        "I2C_FREQ": 400000,
        "INT_PIN": 40,  # Touch interrupt
        "RST_PIN": 39,  # Touch reset
        "GESTURES": ["SWIPE_UP", "SWIPE_DOWN", "SWIPE_LEFT", "SWIPE_RIGHT", "TAP", "DOUBLE_TAP", "LONG_PRESS"]
    },

    # Joystick/Buttons configuration
    "JOYSTICK": {
        "ENABLED": False,  # Watch uses touch instead
        "TOUCH_EMULATION": True,  # Emulate joystick with touch swipes
        "SWIPE_THRESHOLD": 50  # Pixels for swipe detection
    },

    # Physical buttons
    "BUTTONS": {
        "BUTTON_A": None,  # Touch button
        "BUTTON_B": None,  # Touch button
        "BUTTON_X": None,  # Touch button
        "BUTTON_Y": None,  # Touch button
        "PWR": 15,  # Physical power button
        "BOOT": 0,  # Physical boot button
        "TOUCH_BUTTONS": True,  # Use on-screen buttons
        "BUTTON_ZONES": {
            # Define touch zones for virtual buttons (x, y, width, height)
            "A": (320, 420, 80, 60),
            "B": (10, 420, 80, 60),
            "X": (320, 10, 80, 60),
            "Y": (10, 10, 80, 60)
        }
    },

    # IMU - QMI8658 6-axis sensor
    "IMU": {
        "ENABLED": True,
        "DRIVER": "QMI8658",
        "TYPE": "6_AXIS",  # 3-axis accel + 3-axis gyro
        "I2C_ADDR": 0x6B,
        "I2C_SDA": 42,  # Shared with touch
        "I2C_SCL": 41,  # Shared with touch
        "INT_PIN": 38,
        "FEATURES": ["STEP_COUNTER", "MOTION_DETECTION", "ORIENTATION", "TAP_DETECTION", "WRIST_TILT"]
    },

    # RTC - PCF85063 real-time clock
    "RTC": {
        "ENABLED": True,
        "DRIVER": "PCF85063",
        "I2C_ADDR": 0x51,
        "I2C_SDA": 42,  # Shared I2C bus
        "I2C_SCL": 41,
        "BATTERY_BACKUP": True,
        "ALARM_SUPPORT": True,
        "TIMER_SUPPORT": True
    },

    # Power Management - AXP2101
    "POWER": {
        "ENABLED": True,
        "DRIVER": "AXP2101",
        "I2C_ADDR": 0x34,
        "I2C_SDA": 42,  # Shared I2C bus
        "I2C_SCL": 41,
        "BATTERY_VOLTAGE": 3.7,
        "BATTERY_CAPACITY": 500,  # mAh typical for watch battery
        "CHARGE_CURRENT": 200,  # mA charging current
        "FEATURES": ["BATTERY_MONITOR", "USB_DETECTION", "CHARGE_CONTROL", "VOLTAGE_REGULATION", "POWER_PATH"]
    },

    # Storage
    "STORAGE": {
        "INTERNAL_FLASH": 32 * 1024 * 1024,  # 32MB external flash
        "PSRAM": 8 * 1024 * 1024,  # 8MB PSRAM
        "SD_CARD": True,
        "SD_CS": 5,
        "SD_MISO": 3,
        "SD_MOSI": 4,
        "SD_SCLK": 2
    },

    # Communication interfaces
    "INTERFACES": {
        "UART": {
            "TX": 43,
            "RX": 44,
            "BAUDRATE": 115200
        },
        "I2C": {
            "SDA": 42,
            "SCL": 41,
            "FREQ": 400000
        },
        "USB": {
            "TYPE": "TYPE_C",
            "OTG": True,
            "POWER_DELIVERY": False
        }
    },

    # Wireless capabilities
    "WIRELESS": {
        "WIFI": {
            "ENABLED": True,
            "STANDARD": "802.11b/g/n",
            "FREQUENCY": "2.4GHz",
            "ANTENNA": "ONBOARD"
        },
        "BLUETOOTH": {
            "ENABLED": True,
            "VERSION": "5.0",
            "BLE": True,
            "CLASSIC": False
        }
    },

    # LED configuration
    "LED": {
        "ENABLED": False,  # No status LED
        "RGB_LED": False,
        "DISPLAY_NOTIFICATION": True  # Use display for notifications
    },

    # Haptic feedback
    "HAPTICS": {
        "ENABLED": False,  # Add external haptic motor if needed
        "PIN": None,
        "TYPE": None
    },

    # Performance settings
    "PERFORMANCE": {
        "CPU_FREQ": 240000000,  # 240MHz ESP32-S3
        "USE_PSRAM": True,
        "DISPLAY_BUFFER": "DOUBLE",  # Double buffering for smooth animation
        "TOUCH_POLLING_RATE": 120,  # Hz for responsive touch
        "IMU_SAMPLE_RATE": 100,  # Hz for motion detection
        "LOW_POWER_MODE": True  # Battery optimization
    },

    # Watch-specific features
    "WATCH_FEATURES": {
        "ALWAYS_ON_DISPLAY": True,  # AMOLED low power AOD
        "WRIST_DETECTION": True,  # Using IMU
        "RAISE_TO_WAKE": True,  # Using IMU
        "BATTERY_PERCENTAGE": True,
        "STEP_COUNTER": True,
        "HEART_RATE": False,  # No HR sensor
        "NOTIFICATIONS": True,
        "WATER_RESISTANT": False
    }
}

def get_hardware_config():
    """Return hardware configuration for ESP32-S3-Touch-AMOLED-2.06"""
    return HARDWARE_CONFIG

def init_hardware():
    """Initialize hardware-specific features"""
    import machine

    # Set CPU frequency for optimal performance
    machine.freq(HARDWARE_CONFIG["PERFORMANCE"]["CPU_FREQ"])

    # Initialize I2C for touch, IMU, RTC, and power management
    from machine import I2C
    i2c_config = HARDWARE_CONFIG["INTERFACES"]["I2C"]
    i2c = I2C(0,
              scl=Pin(i2c_config["SCL"]),
              sda=Pin(i2c_config["SDA"]),
              freq=i2c_config["FREQ"])

    # Initialize power management first (critical for battery operation)
    if HARDWARE_CONFIG["POWER"]["ENABLED"]:
        try:
            # Initialize AXP2101 power management
            # This would require specific driver implementation
            pass
        except:
            print("Power management initialization failed")

    # Initialize RTC for time keeping
    if HARDWARE_CONFIG["RTC"]["ENABLED"]:
        try:
            # Initialize PCF85063 RTC
            # This would require specific driver implementation
            pass
        except:
            print("RTC initialization failed")

    # Initialize IMU for motion detection
    if HARDWARE_CONFIG["IMU"]["ENABLED"]:
        try:
            # Initialize QMI8658 IMU
            # This would require specific driver implementation
            pass
        except:
            print("IMU initialization failed")

    return i2c

def get_battery_status():
    """Get battery status from AXP2101"""
    # This would interface with AXP2101 to get:
    # - Battery voltage
    # - Battery percentage
    # - Charging status
    # - USB power status
    return {
        "voltage": 3.7,
        "percentage": 75,
        "charging": False,
        "usb_connected": False
    }

def get_motion_data():
    """Get motion data from QMI8658 IMU"""
    # This would interface with QMI8658 to get:
    # - Accelerometer data
    # - Gyroscope data
    # - Step count
    # - Wrist tilt detection
    return {
        "accel": {"x": 0, "y": 0, "z": 1},
        "gyro": {"x": 0, "y": 0, "z": 0},
        "steps": 0,
        "wrist_up": False
    }

def enable_raise_to_wake():
    """Enable raise-to-wake using IMU interrupt"""
    if HARDWARE_CONFIG["WATCH_FEATURES"]["RAISE_TO_WAKE"]:
        # Configure IMU interrupt for wrist tilt detection
        pass

def set_display_brightness(level):
    """Set AMOLED display brightness (0-100)"""
    # Send brightness command to CO5300 controller
    # AMOLED brightness control is different from LCD backlight
    pass