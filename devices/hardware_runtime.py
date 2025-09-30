"""
Hardware Runtime Configuration
Defines which hardware target the application should use
"""

# Target hardware configuration - loaded from config.txt
# To change hardware: edit config.txt and set TARGET_HARDWARE=WAVESHARE_1_3 or GEEKPI_3_5
def load_target_hardware():
    """Load target hardware from config.txt"""
    try:
        with open("config.txt", "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith("TARGET_HARDWARE="):
                    return line.split("=", 1)[1].strip()
    except OSError:
        pass
    return "GEEKPI_3_5"  # Default fallback

TARGET_HARDWARE = load_target_hardware()

# Available hardware targets
SUPPORTED_HARDWARE = [
    "WAVESHARE_1_3",  # Waveshare Pico-LCD-1.3 (240x240)
    "GEEKPI_3_5",     # GeeekPi GPIO Module with 3.5" display (320x480)
    "WAVESHARE_ESP32_S3_AMOLED",  # ESP32-S3-Touch-AMOLED-2.06 watch (410x502)
    "PICOCALC",       # PicoCalc handheld with 4" 320x320 IPS, QWERTY keyboard
    # Add more hardware configurations here as needed
    # "CUSTOM_BOARD",
    # "ANOTHER_DISPLAY",
]

def get_hardware_config():
    """
    Import and return the hardware configuration for the target device
    Returns the hardware configuration module
    """
    import sys
    sys.path.append('devices')
    
    if TARGET_HARDWARE == "WAVESHARE_1_3":
        # Import the specific hardware config
        import waveshare_1_3 as hw
        return {
            "DEVICE_NAME": hw.DEVICE_NAME,
            "DEVICE_ID": hw.DEVICE_ID,
            "JOYSTICK": hw.JOYSTICK,
            "BUTTONS": hw.BUTTONS,
            "SPI": hw.SPI,
            "DISPLAY": hw.DISPLAY,
            "BATTERY": hw.BATTERY,
            "CAPABILITIES": hw.CAPABILITIES,
            "PERFORMANCE": hw.PERFORMANCE
        }
    elif TARGET_HARDWARE == "GEEKPI_3_5":
        # Import GeeekPi configuration
        import geekpi_3_5 as hw
        return {
            "DEVICE_NAME": hw.DEVICE_NAME,
            "DEVICE_ID": hw.DEVICE_ID,
            "JOYSTICK": hw.JOYSTICK,
            "BUTTONS": hw.BUTTONS,
            "SPI": hw.SPI,
            "DISPLAY": hw.DISPLAY,
            "TOUCH": hw.TOUCH if hasattr(hw, 'TOUCH') else None,
            "PERIPHERALS": hw.PERIPHERALS if hasattr(hw, 'PERIPHERALS') else None,
            "BATTERY": hw.BATTERY,
            "CAPABILITIES": hw.CAPABILITIES,
            "PERFORMANCE": hw.PERFORMANCE
        }
    elif TARGET_HARDWARE == "WAVESHARE_ESP32_S3_AMOLED":
        # Import ESP32-S3 AMOLED watch configuration
        import waveshare_esp32_s3_amoled as hw
        config = hw.get_hardware_config()
        # Ensure all required keys are present
        return {
            "DEVICE_NAME": config["DEVICE_NAME"],
            "DEVICE_ID": config["DEVICE_TYPE"],
            "JOYSTICK": config["JOYSTICK"],
            "BUTTONS": config["BUTTONS"],
            "SPI": config.get("SPI", {}),
            "DISPLAY": config["DISPLAY"],
            "TOUCH": config["TOUCH"],
            "IMU": config.get("IMU"),
            "RTC": config.get("RTC"),
            "POWER": config.get("POWER"),
            "STORAGE": config.get("STORAGE"),
            "WIRELESS": config.get("WIRELESS"),
            "BATTERY": {"ENABLED": True, "VOLTAGE": 3.7, "ADC_PIN": None},
            "CAPABILITIES": config.get("WATCH_FEATURES", {}),
            "PERFORMANCE": config["PERFORMANCE"]
        }
    elif TARGET_HARDWARE == "PICOCALC":
        # Import PicoCalc handheld configuration
        import picocalc_handheld as hw
        config = hw.get_hardware_config()
        return {
            "DEVICE_NAME": config["DEVICE_NAME"],
            "DEVICE_ID": config["DEVICE_TYPE"],
            "JOYSTICK": config["JOYSTICK"],
            "BUTTONS": config["BUTTONS"],
            "SPI": config["SPI"],
            "DISPLAY": config["DISPLAY"],
            "KEYBOARD": config["KEYBOARD"],
            "AUDIO": config.get("AUDIO"),
            "STORAGE": config.get("STORAGE"),
            "POWER": config.get("POWER"),
            "GPIO": config.get("GPIO"),
            "USB": config.get("USB"),
            "LED": config.get("LED"),
            "BATTERY": config["POWER"]["BATTERY"] if config.get("POWER") else {"ENABLED": False},
            "CAPABILITIES": config["CAPABILITIES"],
            "PERFORMANCE": config["PERFORMANCE"]
        }
    else:
        raise ValueError(f"Unsupported hardware target: {TARGET_HARDWARE}")

def validate_hardware_config():
    """
    Validate that the current hardware configuration is supported
    """
    if TARGET_HARDWARE not in SUPPORTED_HARDWARE:
        raise ValueError(f"Hardware '{TARGET_HARDWARE}' is not in supported list: {SUPPORTED_HARDWARE}")
    
    try:
        config = get_hardware_config()
        print(f"✓ Hardware configuration loaded: {config['DEVICE_NAME']}")
        return True
    except Exception as e:
        print(f"✗ Failed to load hardware configuration: {e}")
        return False