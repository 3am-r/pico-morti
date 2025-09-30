"""
CO5300 AMOLED Display Driver for ESP32-S3-Touch-AMOLED-2.06
410×502 resolution, 16.7M colors, QSPI interface
High contrast, wide viewing angle, fast response
"""

from micropython import const
import framebuf
import time
from machine import Pin, SPI

# CO5300 Command definitions
_CMD_NOP = const(0x00)
_CMD_SWRESET = const(0x01)  # Software Reset
_CMD_RDDID = const(0x04)     # Read Display ID
_CMD_RDDST = const(0x09)     # Read Display Status
_CMD_RDDPM = const(0x0A)     # Read Display Power Mode
_CMD_RDDMADCTL = const(0x0B) # Read Display MADCTL
_CMD_RDDCOLMOD = const(0x0C) # Read Display Pixel Format
_CMD_RDDIM = const(0x0D)     # Read Display Image Format
_CMD_RDDSM = const(0x0E)     # Read Display Signal Mode
_CMD_SLPIN = const(0x10)     # Sleep In
_CMD_SLPOUT = const(0x11)    # Sleep Out
_CMD_PTLON = const(0x12)     # Partial Mode On
_CMD_NORON = const(0x13)     # Normal Display Mode On
_CMD_INVOFF = const(0x20)    # Display Inversion Off
_CMD_INVON = const(0x21)     # Display Inversion On
_CMD_DISPOFF = const(0x28)   # Display Off
_CMD_DISPON = const(0x29)    # Display On
_CMD_CASET = const(0x2A)     # Column Address Set
_CMD_RASET = const(0x2B)     # Row Address Set
_CMD_RAMWR = const(0x2C)     # Memory Write
_CMD_RAMRD = const(0x2E)     # Memory Read
_CMD_PTLAR = const(0x30)     # Partial Area
_CMD_MADCTL = const(0x36)    # Memory Access Control
_CMD_COLMOD = const(0x3A)    # Pixel Format Set
_CMD_BRIGHTNESS = const(0x51) # Write Display Brightness
_CMD_CTRL_DISPLAY = const(0x53) # Write CTRL Display
_CMD_READ_ID1 = const(0xDA)  # Read ID1
_CMD_READ_ID2 = const(0xDB)  # Read ID2
_CMD_READ_ID3 = const(0xDC)  # Read ID3

# MADCTL bits
_MADCTL_MY = const(0x80)  # Row Address Order
_MADCTL_MX = const(0x40)  # Column Address Order
_MADCTL_MV = const(0x20)  # Row/Column Exchange
_MADCTL_ML = const(0x10)  # Vertical Refresh Order
_MADCTL_RGB = const(0x00) # RGB Order
_MADCTL_BGR = const(0x08) # BGR Order

# Color definitions for AMOLED (24-bit RGB888)
class AMOLEDColor:
    BLACK = const(0x000000)
    WHITE = const(0xFFFFFF)
    RED = const(0xFF0000)
    GREEN = const(0x00FF00)
    BLUE = const(0x0000FF)
    YELLOW = const(0xFFFF00)
    CYAN = const(0x00FFFF)
    MAGENTA = const(0xFF00FF)
    ORANGE = const(0xFF8000)
    PURPLE = const(0x8000FF)
    GRAY = const(0x808080)
    DARK_GRAY = const(0x404040)
    LIGHT_GRAY = const(0xC0C0C0)

    # AMOLED optimized colors (pure colors save power)
    AMOLED_RED = const(0xFF0000)    # Pure red
    AMOLED_GREEN = const(0x00FF00)  # Pure green
    AMOLED_BLUE = const(0x0000FF)   # Pure blue
    AMOLED_BLACK = const(0x000000)  # True black (pixels off)

    @staticmethod
    def rgb888_to_rgb565(color24):
        """Convert 24-bit RGB888 to 16-bit RGB565 for memory efficiency"""
        r = (color24 >> 16) & 0xFF
        g = (color24 >> 8) & 0xFF
        b = color24 & 0xFF
        return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

    @staticmethod
    def rgb565_to_rgb888(color16):
        """Convert 16-bit RGB565 to 24-bit RGB888"""
        r = (color16 >> 11) & 0x1F
        g = (color16 >> 5) & 0x3F
        b = color16 & 0x1F
        return (r << 19) | (g << 10) | (b << 3)

class CO5300_AMOLED:
    """Driver for CO5300 AMOLED display controller"""

    def __init__(self, spi, width, height, reset, dc, cs, rotation=0, buffer_size=0):
        """
        Initialize CO5300 AMOLED display

        Args:
            spi: SPI bus instance
            width: Display width (410 for this device)
            height: Display height (502 for this device)
            reset: Reset pin
            dc: Data/Command pin
            cs: Chip Select pin
            rotation: Display rotation (0, 90, 180, 270)
            buffer_size: Frame buffer size (0 for no buffer)
        """
        self.spi = spi
        self.width = width
        self.height = height
        self.reset = reset
        self.dc = dc
        self.cs = cs
        self.rotation = rotation
        self.buffer_size = buffer_size

        # Initialize pins
        self.cs.init(Pin.OUT, value=1)
        self.dc.init(Pin.OUT, value=0)
        if self.reset:
            self.reset.init(Pin.OUT, value=1)

        # Create frame buffer if requested
        if buffer_size:
            import gc
            gc.collect()
            # Use RGB565 for memory efficiency
            self.buffer = bytearray(buffer_size)
            self.framebuf = framebuf.FrameBuffer(self.buffer, width, height, framebuf.RGB565)
        else:
            self.buffer = None
            self.framebuf = None

        # Display state
        self.brightness = 100
        self.inverted = False
        self.sleeping = False

        # Initialize display
        self.init_display()

    def init_display(self):
        """Initialize the CO5300 AMOLED display"""
        # Hardware reset
        if self.reset:
            self.reset.value(1)
            time.sleep_ms(10)
            self.reset.value(0)
            time.sleep_ms(10)
            self.reset.value(1)
            time.sleep_ms(120)

        # Software reset
        self.write_cmd(_CMD_SWRESET)
        time.sleep_ms(150)

        # Sleep out
        self.write_cmd(_CMD_SLPOUT)
        time.sleep_ms(120)

        # Set pixel format to 24-bit RGB888 (for AMOLED quality)
        self.write_cmd(_CMD_COLMOD)
        self.write_data(bytearray([0x77]))  # 24-bit/pixel

        # Set memory access control
        self.write_cmd(_CMD_MADCTL)
        madctl = 0
        if self.rotation == 0:
            madctl = _MADCTL_MX | _MADCTL_BGR
            self._width = self.width
            self._height = self.height
        elif self.rotation == 90:
            madctl = _MADCTL_MV | _MADCTL_BGR
            self._width = self.height
            self._height = self.width
        elif self.rotation == 180:
            madctl = _MADCTL_MY | _MADCTL_BGR
            self._width = self.width
            self._height = self.height
        elif self.rotation == 270:
            madctl = _MADCTL_MX | _MADCTL_MY | _MADCTL_MV | _MADCTL_BGR
            self._width = self.height
            self._height = self.width
        self.write_data(bytearray([madctl]))

        # Set column and row address
        self.set_window(0, 0, self._width - 1, self._height - 1)

        # Normal display mode
        self.write_cmd(_CMD_NORON)

        # Display on
        self.write_cmd(_CMD_DISPON)
        time.sleep_ms(10)

        # Set initial brightness
        self.set_brightness(self.brightness)

        # Clear screen to black (AMOLED power saving)
        self.fill(AMOLEDColor.BLACK)

    def write_cmd(self, cmd):
        """Write command to display"""
        self.cs.value(0)
        self.dc.value(0)
        self.spi.write(bytearray([cmd]))
        self.cs.value(1)

    def write_data(self, data):
        """Write data to display"""
        self.cs.value(0)
        self.dc.value(1)
        self.spi.write(data)
        self.cs.value(1)

    def set_window(self, x0, y0, x1, y1):
        """Set drawing window"""
        # Column address set
        self.write_cmd(_CMD_CASET)
        self.write_data(bytearray([
            (x0 >> 8) & 0xFF,
            x0 & 0xFF,
            (x1 >> 8) & 0xFF,
            x1 & 0xFF
        ]))

        # Row address set
        self.write_cmd(_CMD_RASET)
        self.write_data(bytearray([
            (y0 >> 8) & 0xFF,
            y0 & 0xFF,
            (y1 >> 8) & 0xFF,
            y1 & 0xFF
        ]))

        # Write to RAM
        self.write_cmd(_CMD_RAMWR)

    def fill(self, color):
        """Fill entire display with color"""
        self.set_window(0, 0, self._width - 1, self._height - 1)

        # Convert to RGB888 bytes
        r = (color >> 16) & 0xFF
        g = (color >> 8) & 0xFF
        b = color & 0xFF

        # Create pixel data
        pixel = bytearray([r, g, b])
        chunk_size = 1024  # Write in chunks to avoid memory issues
        chunk = pixel * (chunk_size // 3)

        total_pixels = self._width * self._height
        pixels_written = 0

        self.cs.value(0)
        self.dc.value(1)

        while pixels_written < total_pixels:
            pixels_to_write = min(chunk_size // 3, total_pixels - pixels_written)
            if pixels_to_write == chunk_size // 3:
                self.spi.write(chunk)
            else:
                self.spi.write(pixel * pixels_to_write)
            pixels_written += pixels_to_write

        self.cs.value(1)

    def pixel(self, x, y, color):
        """Draw a pixel at x, y with given color"""
        if 0 <= x < self._width and 0 <= y < self._height:
            self.set_window(x, y, x, y)
            r = (color >> 16) & 0xFF
            g = (color >> 8) & 0xFF
            b = color & 0xFF
            self.write_data(bytearray([r, g, b]))

    def hline(self, x, y, width, color):
        """Draw horizontal line"""
        if y < 0 or y >= self._height:
            return
        x = max(0, x)
        width = min(width, self._width - x)
        if width > 0:
            self.set_window(x, y, x + width - 1, y)
            r = (color >> 16) & 0xFF
            g = (color >> 8) & 0xFF
            b = color & 0xFF
            pixel = bytearray([r, g, b])
            self.cs.value(0)
            self.dc.value(1)
            for _ in range(width):
                self.spi.write(pixel)
            self.cs.value(1)

    def vline(self, x, y, height, color):
        """Draw vertical line"""
        if x < 0 or x >= self._width:
            return
        y = max(0, y)
        height = min(height, self._height - y)
        if height > 0:
            self.set_window(x, y, x, y + height - 1)
            r = (color >> 16) & 0xFF
            g = (color >> 8) & 0xFF
            b = color & 0xFF
            pixel = bytearray([r, g, b])
            self.cs.value(0)
            self.dc.value(1)
            for _ in range(height):
                self.spi.write(pixel)
            self.cs.value(1)

    def rect(self, x, y, width, height, color):
        """Draw rectangle outline"""
        self.hline(x, y, width, color)
        self.hline(x, y + height - 1, width, color)
        self.vline(x, y, height, color)
        self.vline(x + width - 1, y, height, color)

    def fill_rect(self, x, y, width, height, color):
        """Fill rectangle with color"""
        x = max(0, min(x, self._width - 1))
        y = max(0, min(y, self._height - 1))
        width = min(width, self._width - x)
        height = min(height, self._height - y)

        if width > 0 and height > 0:
            self.set_window(x, y, x + width - 1, y + height - 1)
            r = (color >> 16) & 0xFF
            g = (color >> 8) & 0xFF
            b = color & 0xFF
            pixel = bytearray([r, g, b])
            total_pixels = width * height

            self.cs.value(0)
            self.dc.value(1)
            for _ in range(total_pixels):
                self.spi.write(pixel)
            self.cs.value(1)

    def set_brightness(self, level):
        """Set display brightness (0-100)"""
        self.brightness = max(0, min(100, level))
        # Convert percentage to 8-bit value
        brightness_value = int(self.brightness * 255 / 100)
        self.write_cmd(_CMD_BRIGHTNESS)
        self.write_data(bytearray([brightness_value]))

    def sleep(self):
        """Put display to sleep (low power mode)"""
        if not self.sleeping:
            self.write_cmd(_CMD_DISPOFF)
            time.sleep_ms(10)
            self.write_cmd(_CMD_SLPIN)
            self.sleeping = True

    def wake(self):
        """Wake display from sleep"""
        if self.sleeping:
            self.write_cmd(_CMD_SLPOUT)
            time.sleep_ms(120)
            self.write_cmd(_CMD_DISPON)
            self.sleeping = False

    def invert(self, invert=True):
        """Invert display colors"""
        self.inverted = invert
        self.write_cmd(_CMD_INVON if invert else _CMD_INVOFF)

    def display(self):
        """Update display (for compatibility with framebuf-based code)"""
        if self.framebuf:
            # Convert and send framebuffer to display
            self.set_window(0, 0, self._width - 1, self._height - 1)
            self.write_data(self.buffer)

    def power_save_mode(self, enable=True):
        """Enable AMOLED power saving features"""
        if enable:
            # Reduce brightness for power saving
            self.set_brightness(30)
            # Use pure black background (pixels off)
            # Enable partial mode if needed
        else:
            self.set_brightness(100)

# Compatibility layer for existing st7789 code
class Color(AMOLEDColor):
    """Compatibility wrapper for color definitions"""
    pass

def CO5300(spi, width, height, reset, dc, cs, backlight=None, rotation=0):
    """Factory function for CO5300 display (compatible with st7789 interface)"""
    return CO5300_AMOLED(spi, width, height, reset, dc, cs, rotation)