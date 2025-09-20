"""
Hardware Runtime Configuration
Defines which hardware target the application should use
"""

# Target hardware configuration
# Change this constant to switch between different hardware platforms
TARGET_HARDWARE = "WAVESHARE_1_3"

# Available hardware targets
SUPPORTED_HARDWARE = [
    "WAVESHARE_1_3",  # Waveshare Pico-LCD-1.3
    # Add more hardware configurations here as needed
    # "CUSTOM_BOARD", 
    # "ANOTHER_DISPLAY",
]

def get_hardware_config():
    """
    Import and return the hardware configuration for the target device
    Returns the hardware configuration module
    """
    if TARGET_HARDWARE == "WAVESHARE_1_3":
        # Import the specific hardware config - using absolute import for MicroPython compatibility
        import sys
        sys.path.append('devices')
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