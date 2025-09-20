"""
ST7789 driver for MicroPython
Optimized for Waveshare Pico-LCD-1.3 (240x240 pixels)
"""

from micropython import const
import framebuf
import ustruct as struct
import time
import gc

# ST7789 commands
_SWRESET = const(0x01)
_SLPOUT = const(0x11)
_COLMOD = const(0x3A)
_MADCTL = const(0x36)
_CASET = const(0x2A)
_RASET = const(0x2B)
_RAMWR = const(0x2C)
_INVON = const(0x21)
_DISPON = const(0x29)

# Color modes
COLOR_MODE_65K = const(0x50)
COLOR_MODE_262K = const(0x60)
COLOR_MODE_12BIT = const(0x03)
COLOR_MODE_16BIT = const(0x05)
COLOR_MODE_18BIT = const(0x06)
COLOR_MODE_16M = const(0x07)

# Display orientation
MADCTL_MY = const(0x80)  # Row direction
MADCTL_MX = const(0x40)  # Column direction  
MADCTL_MV = const(0x20)  # Row/Column exchange
MADCTL_ML = const(0x10)  # Vertical refresh direction
MADCTL_BGR = const(0x08) # BGR color filter
MADCTL_MH = const(0x04)  # Horizontal refresh direction
MADCTL_RGB = const(0x00) # RGB color filter

class ST7789:
    def __init__(self, spi, width, height, reset, dc, cs=None, backlight=None, rotation=0):
        """
        Initialize ST7789 display driver
        
        Args:
            spi: SPI bus object
            width: Display width (240 for Pico-LCD-1.3)
            height: Display height (240 for Pico-LCD-1.3)
            reset: Reset pin
            dc: Data/Command pin
            cs: Chip select pin (optional)
            backlight: Backlight pin (optional)
            rotation: Display rotation (0, 90, 180, 270)
        """
        self.spi = spi
        self.width = width
        self.height = height
        self.reset = reset
        self.dc = dc
        self.cs = cs
        self.backlight = backlight
        self.rotation = rotation
        
        # Initialize pins
        self.reset.init(self.reset.OUT, value=1)
        self.dc.init(self.dc.OUT, value=0)
        if self.cs:
            self.cs.init(self.cs.OUT, value=1)
        if self.backlight:
            self.backlight.init(self.backlight.OUT, value=1)
            
        # Create framebuffer with memory optimization
        gc.collect()  # Force garbage collection before large allocation
        self.buffer = bytearray(self.width * self.height * 2)
        self.framebuf = framebuf.FrameBuffer(self.buffer, self.width, self.height, framebuf.RGB565)
        
        # Initialize display
        self.init_display()
        
    def init_display(self):
        """Initialize the display with proper settings"""
        # Hardware reset
        self.reset.value(0)
        time.sleep_ms(100)
        self.reset.value(1)
        time.sleep_ms(200)
        
        # Sleep out
        self.write_cmd(_SLPOUT)
        time.sleep_ms(500)
        
        # Color mode - 16bit color (RGB565)
        self.write_cmd(_COLMOD)
        self.write_data(bytearray([0x55]))  # 16-bit color
        
        # Memory data access control - set rotation
        self.write_cmd(_MADCTL)
        madctl = 0x00
        
        # Rotation settings for Waveshare Pico-LCD-1.3
        # For pad form factor: joystick on left, buttons on right, screen facing up
        if self.rotation == 0:
            madctl = 0x70  # MY | MV | MX - Screen upright, joystick left
        elif self.rotation == 90:
            madctl = 0x00  # Default
        elif self.rotation == 180:
            madctl = 0xB0  # MY | MV | ML
        elif self.rotation == 270:
            madctl = 0xC0  # MY | MX
            
        self.write_data(bytearray([madctl]))
        
        # Column and row address set
        self.write_cmd(_CASET)
        self.write_data(bytearray([0x00, 0x00, 0x00, 0xEF]))  # 0-239
        
        self.write_cmd(_RASET)
        self.write_data(bytearray([0x00, 0x00, 0x00, 0xEF]))  # 0-239
        
        # Inversion on (for proper colors on this display)
        self.write_cmd(_INVON)
        
        # Normal display mode on
        self.write_cmd(0x13)
        
        # Display on
        self.write_cmd(_DISPON)
        time.sleep_ms(100)
        
        # Clear display to black to remove noise
        self.clear(Color.BLACK)
        
    def write_cmd(self, cmd):
        """Write command to display"""
        if self.cs:
            self.cs.value(0)
        self.dc.value(0)
        self.spi.write(bytearray([cmd]))
        if self.cs:
            self.cs.value(1)
            
    def write_data(self, data):
        """Write data to display"""
        if self.cs:
            self.cs.value(0)
        self.dc.value(1)
        self.spi.write(data)
        if self.cs:
            self.cs.value(1)
            
    def set_window(self, x0, y0, x1, y1):
        """Set drawing window"""
        # Column address set
        self.write_cmd(_CASET)
        self.write_data(struct.pack(">HH", x0, x1))
        
        # Row address set
        self.write_cmd(_RASET)
        self.write_data(struct.pack(">HH", y0, y1))
        
        # Write to RAM
        self.write_cmd(_RAMWR)
        
    def display(self):
        """Update display with framebuffer contents"""
        self.set_window(0, 0, self.width - 1, self.height - 1)
        self.write_data(self.buffer)
        
    def clear(self, color=0x0000):
        """Clear display with specified color"""
        self.fill(color)
        self.display()
        
    def pixel(self, x, y, color):
        """Set pixel at x,y to color"""
        self.framebuf.pixel(x, y, color)
        
    def fill(self, color):
        """Fill entire display with color"""
        self.framebuf.fill(color)
        
    def text(self, string, x, y, color, bg=None):
        """Draw text at position"""
        if bg is not None:
            # Draw background rectangle for text
            for char in string:
                self.fill_rect(x, y, 8, 8, bg)
                x += 8
            x -= len(string) * 8
        self.framebuf.text(string, x, y, color)
        
    def hline(self, x, y, length, color):
        """Draw horizontal line"""
        self.framebuf.hline(x, y, length, color)
        
    def vline(self, x, y, length, color):
        """Draw vertical line"""
        self.framebuf.vline(x, y, length, color)
        
    def line(self, x0, y0, x1, y1, color):
        """Draw line from (x0,y0) to (x1,y1)"""
        self.framebuf.line(x0, y0, x1, y1, color)
        
    def rect(self, x, y, width, height, color):
        """Draw rectangle outline"""
        self.framebuf.rect(x, y, width, height, color)
        
    def fill_rect(self, x, y, width, height, color):
        """Draw filled rectangle"""
        self.framebuf.fill_rect(x, y, width, height, color)
        
    def circle(self, x, y, radius, color):
        """Draw circle outline"""
        # Midpoint circle algorithm
        f = 1 - radius
        ddf_x = 1
        ddf_y = -2 * radius
        x1 = 0
        y1 = radius
        
        self.pixel(x, y + radius, color)
        self.pixel(x, y - radius, color)
        self.pixel(x + radius, y, color)
        self.pixel(x - radius, y, color)
        
        while x1 < y1:
            if f >= 0:
                y1 -= 1
                ddf_y += 2
                f += ddf_y
            x1 += 1
            ddf_x += 2
            f += ddf_x
            
            self.pixel(x + x1, y + y1, color)
            self.pixel(x - x1, y + y1, color)
            self.pixel(x + x1, y - y1, color)
            self.pixel(x - x1, y - y1, color)
            self.pixel(x + y1, y + x1, color)
            self.pixel(x - y1, y + x1, color)
            self.pixel(x + y1, y - x1, color)
            self.pixel(x - y1, y - x1, color)
            
    def fill_circle(self, x, y, radius, color):
        """Draw filled circle"""
        # Draw horizontal lines to fill circle
        for y1 in range(-radius, radius + 1):
            x1 = int((radius * radius - y1 * y1) ** 0.5)
            self.hline(x - x1, y + y1, 2 * x1 + 1, color)
            
    def set_backlight(self, value):
        """Set backlight on/off or PWM value"""
        if self.backlight:
            if isinstance(value, bool):
                self.backlight.value(1 if value else 0)
            else:
                # For PWM control, value should be 0-65535
                # Requires PWM setup on backlight pin
                pass

# Color definitions (RGB565 format)
class Color:
    BLACK = const(0x0000)
    WHITE = const(0xFFFF)
    RED = const(0xF800)
    GREEN = const(0x07E0)
    BLUE = const(0x001F)
    CYAN = const(0x07FF)
    MAGENTA = const(0xF81F)
    YELLOW = const(0xFFE0)
    ORANGE = const(0xFD20)
    PURPLE = const(0x8010)
    GRAY = const(0x8410)
    DARK_GRAY = const(0x4208)
    LIGHT_GRAY = const(0xC618)
    
    @staticmethod
    def rgb565(r, g, b):
        """Convert RGB888 to RGB565"""
        return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)