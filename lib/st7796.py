"""
ST7796 Display Driver for MicroPython
320x480 pixels, 16-bit color (RGB565)
Compatible with 3.5" TFT displays
"""

from micropython import const
import framebuf
import ustruct as struct
import time
import gc

# ST7796 commands
_SWRESET = const(0x01)  # Software Reset
_SLPOUT = const(0x11)   # Sleep Out
_COLMOD = const(0x3A)   # Pixel Format Set
_MADCTL = const(0x36)   # Memory Access Control
_CASET = const(0x2A)    # Column Address Set
_PASET = const(0x2B)    # Page Address Set
_RAMWR = const(0x2C)    # Memory Write
_INVON = const(0x21)    # Display Inversion On
_INVOFF = const(0x20)   # Display Inversion Off
_DISPON = const(0x29)   # Display On
_DISPOFF = const(0x28)  # Display Off

# Memory Access Control bits
_MADCTL_MY = const(0x80)   # Row Address Order
_MADCTL_MX = const(0x40)   # Column Address Order
_MADCTL_MV = const(0x20)   # Row/Column Exchange
_MADCTL_ML = const(0x10)   # Vertical Refresh Order
_MADCTL_BGR = const(0x08)  # BGR Order
_MADCTL_MH = const(0x04)   # Horizontal Refresh Order

# Color definitions (RGB565)
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
    LIGHT_GRAY = const(0xC618)
    DARK_GRAY = const(0x4208)
    BROWN = const(0xA145)
    PINK = const(0xF81F)
    
    @staticmethod
    def rgb565(r, g, b):
        """Convert RGB888 to RGB565"""
        return ((r & 0xF8) << 8) | ((g & 0xFC) << 3) | (b >> 3)

class ST7796:
    def __init__(self, spi, width, height, reset, dc, cs=None, backlight=None, rotation=0):
        """
        Initialize ST7796 display
        
        Args:
            spi: SPI interface
            width: Display width (320 for portrait, 480 for landscape)
            height: Display height (480 for portrait, 320 for landscape)
            reset: Reset pin
            dc: Data/Command pin
            cs: Chip Select pin (optional)
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
            
        # Create smaller framebuffer to save memory
        # For ST7796, we'll use direct drawing more often
        gc.collect()
        
        # Use a line buffer approach for better memory efficiency
        self.line_buffer = bytearray(self.width * 2)  # One line buffer
        self.use_framebuffer = False  # Disable framebuffer to save memory
        
        # No framebuffer to save memory - use direct drawing with bitmap font
        self.buffer = None
        self.framebuf = None
        print("ST7796: Using direct drawing to conserve memory")
        
        # Test pins before initialization
        print(f"ST7796: Testing pins...")
        print(f"ST7796: RST={reset}, DC={dc}, CS={cs}")
        
        # Test pin control
        self.reset.value(1)
        self.dc.value(1)
        if self.cs:
            self.cs.value(1)
        time.sleep_ms(100)
        
        self.reset.value(0)
        self.dc.value(0)
        if self.cs:
            self.cs.value(0)
        time.sleep_ms(100)
        
        print(f"ST7796: Pin test complete")
        
        # Initialize display
        print(f"ST7796: Initializing {width}x{height} display...")
        self.init_display()
        print("ST7796: Display initialization complete")
        
    def init_display(self):
        """Initialize the display with proper settings for ST7796"""
        # Hardware reset
        self.reset.value(0)
        time.sleep_ms(10)
        self.reset.value(1)
        time.sleep_ms(120)
        
        # ST7796 specific initialization sequence
        # Software reset
        self.write_cmd(0x01)  # SWRESET
        time.sleep_ms(120)
        
        # Sleep out
        self.write_cmd(0x11)  # SLPOUT
        time.sleep_ms(120)
        
        # Command Set Control
        self.write_cmd(0xF0)
        self.write_data(bytes([0xC3]))
        
        self.write_cmd(0xF0)
        self.write_data(bytes([0x96]))
        
        # Memory Data Access Control
        self.write_cmd(0x36)
        self.write_data(bytes([0x48]))  # Portrait mode, BGR
        
        # Pixel Format Set
        self.write_cmd(0x3A)
        self.write_data(bytes([0x55]))  # 16-bit RGB565
        
        # Display Function Control
        self.write_cmd(0xB6)
        self.write_data(bytes([0x80, 0x02, 0x3B]))
        
        # Power Control 1
        self.write_cmd(0xC1)
        self.write_data(bytes([0x13]))
        
        # Power Control 2
        self.write_cmd(0xC2)
        self.write_data(bytes([0xA7]))
        
        # VCOM Control
        self.write_cmd(0xC5)
        self.write_data(bytes([0x0E]))
        
        # Positive Gamma Control
        self.write_cmd(0xE0)
        self.write_data(bytes([0xF0, 0x09, 0x13, 0x12, 0x12, 0x2B, 0x3C, 0x44, 0x4B, 0x1B, 0x18, 0x17, 0x1D, 0x21]))
        
        # Negative Gamma Control
        self.write_cmd(0xE1)
        self.write_data(bytes([0xF0, 0x09, 0x13, 0x0C, 0x0D, 0x27, 0x3B, 0x44, 0x4D, 0x0B, 0x17, 0x17, 0x1D, 0x21]))
        
        # Command Set Control
        self.write_cmd(0xF0)
        self.write_data(bytes([0x3C]))
        
        self.write_cmd(0xF0)
        self.write_data(bytes([0x69]))
        
        # Normal Display Mode On
        self.write_cmd(0x13)
        
        # Display On
        self.write_cmd(0x29)
        time.sleep_ms(120)
        
        print("ST7796: Initialization complete - testing display...")
        
        # Test with colored rectangles
        self.fill_rect(0, 0, 160, 240, Color.RED)
        self.fill_rect(160, 0, 160, 240, Color.GREEN)
        time.sleep_ms(2000)
        
        # Clear to black
        self.fill(Color.BLACK)
        print("ST7796: Display test complete")
        
    def write_cmd(self, cmd):
        """Write command to display"""
        if self.cs:
            self.cs.value(0)
        self.dc.value(0)  # Command mode
        self.spi.write(bytes([cmd]))
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
            
    def set_rotation(self, rotation):
        """Set display rotation"""
        self.rotation = rotation
        madctl = 0x00
        
        if rotation == 0:  # Portrait
            madctl = _MADCTL_MX | _MADCTL_BGR
            self.width = 320
            self.height = 480
        elif rotation == 90:  # Landscape
            madctl = _MADCTL_MV | _MADCTL_BGR
            self.width = 480
            self.height = 320
        elif rotation == 180:  # Portrait flipped
            madctl = _MADCTL_MY | _MADCTL_BGR
            self.width = 320
            self.height = 480
        elif rotation == 270:  # Landscape flipped
            madctl = _MADCTL_MX | _MADCTL_MY | _MADCTL_MV | _MADCTL_BGR
            self.width = 480
            self.height = 320
            
        self.write_cmd(_MADCTL)
        self.write_data(bytes([madctl]))
        
    def set_window(self, x0, y0, x1, y1):
        """Set drawing window"""
        # Column address set
        self.write_cmd(_CASET)
        self.write_data(struct.pack('>HH', x0, x1))
        
        # Page address set
        self.write_cmd(_PASET)
        self.write_data(struct.pack('>HH', y0, y1))
        
        # Memory write
        self.write_cmd(_RAMWR)
        
    def fill(self, color):
        """Fill entire display with color"""
        # Direct drawing only
        self.set_window(0, 0, self.width - 1, self.height - 1)
        
        # Prepare color data
        color_data = struct.pack('>H', color)
        chunk = color_data * (self.width // 2)  # Half line for memory efficiency
        
        # Write in chunks
        for _ in range(self.height):
            self.write_data(chunk)
            self.write_data(chunk)
            
    def fill_rect(self, x, y, width, height, color):
        """Draw filled rectangle"""
        # Direct drawing with clipping
        if x < 0 or y < 0 or x + width > self.width or y + height > self.height:
            # Clip rectangle to display bounds
            x = max(0, x)
            y = max(0, y)
            width = min(width, self.width - x)
            height = min(height, self.height - y)
            
        if width > 0 and height > 0:
            self.set_window(x, y, x + width - 1, y + height - 1)
            
            # Prepare color data
            color_data = struct.pack('>H', color)
            chunk = color_data * width
            
            # Write rectangle
            for _ in range(height):
                self.write_data(chunk)
                
    def rect(self, x, y, width, height, color):
        """Draw rectangle outline"""
        # Top and bottom
        self.fill_rect(x, y, width, 1, color)
        self.fill_rect(x, y + height - 1, width, 1, color)
        # Left and right
        self.fill_rect(x, y, 1, height, color)
        self.fill_rect(x + width - 1, y, 1, height, color)
        
    def hline(self, x, y, length, color):
        """Draw horizontal line"""
        self.fill_rect(x, y, length, 1, color)
        
    def vline(self, x, y, length, color):
        """Draw vertical line"""
        self.fill_rect(x, y, 1, length, color)
        
    def line(self, x0, y0, x1, y1, color):
        """Draw line from (x0,y0) to (x1,y1) using Bresenham's algorithm"""
        dx = abs(x1 - x0)
        dy = abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        
        while True:
            self.pixel(x0, y0, color)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy
                
    def circle(self, x, y, radius, color):
        """Draw circle outline"""
        # Midpoint circle algorithm
        f = 1 - radius
        dx = 1
        dy = -2 * radius
        px = 0
        py = radius
        
        self.pixel(x, y + radius, color)
        self.pixel(x, y - radius, color)
        self.pixel(x + radius, y, color)
        self.pixel(x - radius, y, color)
        
        while px < py:
            if f >= 0:
                py -= 1
                dy += 2
                f += dy
            px += 1
            dx += 2
            f += dx
            
            self.pixel(x + px, y + py, color)
            self.pixel(x - px, y + py, color)
            self.pixel(x + px, y - py, color)
            self.pixel(x - px, y - py, color)
            self.pixel(x + py, y + px, color)
            self.pixel(x - py, y + px, color)
            self.pixel(x + py, y - px, color)
            self.pixel(x - py, y - px, color)
            
    def fill_circle(self, x, y, radius, color):
        """Draw filled circle"""
        for dy in range(-radius, radius + 1):
            dx = int((radius * radius - dy * dy) ** 0.5)
            self.hline(x - dx, y + dy, 2 * dx + 1, color)
            
    def text(self, string, x, y, color, bg=None, scale=1):
        """Draw text at position using simple bitmap font"""
        # Simple 5x8 bitmap font for basic ASCII characters
        # This is a minimal font to save memory
        font = {
            ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
            '!': [0x00, 0x00, 0x5F, 0x00, 0x00],
            '"': [0x00, 0x07, 0x00, 0x07, 0x00],
            '#': [0x14, 0x7F, 0x14, 0x7F, 0x14],
            '$': [0x24, 0x2A, 0x7F, 0x2A, 0x12],
            '%': [0x23, 0x13, 0x08, 0x64, 0x62],
            '&': [0x36, 0x49, 0x55, 0x22, 0x50],
            "'": [0x00, 0x05, 0x03, 0x00, 0x00],
            '(': [0x00, 0x1C, 0x22, 0x41, 0x00],
            ')': [0x00, 0x41, 0x22, 0x1C, 0x00],
            '*': [0x08, 0x2A, 0x1C, 0x2A, 0x08],
            '+': [0x08, 0x08, 0x3E, 0x08, 0x08],
            ',': [0x00, 0x50, 0x30, 0x00, 0x00],
            '-': [0x08, 0x08, 0x08, 0x08, 0x08],
            '.': [0x00, 0x60, 0x60, 0x00, 0x00],
            '/': [0x20, 0x10, 0x08, 0x04, 0x02],
            '0': [0x3E, 0x51, 0x49, 0x45, 0x3E],
            '1': [0x00, 0x42, 0x7F, 0x40, 0x00],
            '2': [0x42, 0x61, 0x51, 0x49, 0x46],
            '3': [0x21, 0x41, 0x45, 0x4B, 0x31],
            '4': [0x18, 0x14, 0x12, 0x7F, 0x10],
            '5': [0x27, 0x45, 0x45, 0x45, 0x39],
            '6': [0x3C, 0x4A, 0x49, 0x49, 0x30],
            '7': [0x01, 0x71, 0x09, 0x05, 0x03],
            '8': [0x36, 0x49, 0x49, 0x49, 0x36],
            '9': [0x06, 0x49, 0x49, 0x29, 0x1E],
            ':': [0x00, 0x36, 0x36, 0x00, 0x00],
            ';': [0x00, 0x56, 0x36, 0x00, 0x00],
            '<': [0x00, 0x08, 0x14, 0x22, 0x41],
            '=': [0x14, 0x14, 0x14, 0x14, 0x14],
            '>': [0x41, 0x22, 0x14, 0x08, 0x00],
            '?': [0x02, 0x01, 0x51, 0x09, 0x06],
            '@': [0x32, 0x49, 0x79, 0x41, 0x3E],
            'A': [0x7E, 0x11, 0x11, 0x11, 0x7E],
            'B': [0x7F, 0x49, 0x49, 0x49, 0x36],
            'C': [0x3E, 0x41, 0x41, 0x41, 0x22],
            'D': [0x7F, 0x41, 0x41, 0x22, 0x1C],
            'E': [0x7F, 0x49, 0x49, 0x49, 0x41],
            'F': [0x7F, 0x09, 0x09, 0x01, 0x01],
            'G': [0x3E, 0x41, 0x41, 0x51, 0x32],
            'H': [0x7F, 0x08, 0x08, 0x08, 0x7F],
            'I': [0x00, 0x41, 0x7F, 0x41, 0x00],
            'J': [0x20, 0x40, 0x41, 0x3F, 0x01],
            'K': [0x7F, 0x08, 0x14, 0x22, 0x41],
            'L': [0x7F, 0x40, 0x40, 0x40, 0x40],
            'M': [0x7F, 0x02, 0x04, 0x02, 0x7F],
            'N': [0x7F, 0x04, 0x08, 0x10, 0x7F],
            'O': [0x3E, 0x41, 0x41, 0x41, 0x3E],
            'P': [0x7F, 0x09, 0x09, 0x09, 0x06],
            'Q': [0x3E, 0x41, 0x51, 0x21, 0x5E],
            'R': [0x7F, 0x09, 0x19, 0x29, 0x46],
            'S': [0x46, 0x49, 0x49, 0x49, 0x31],
            'T': [0x01, 0x01, 0x7F, 0x01, 0x01],
            'U': [0x3F, 0x40, 0x40, 0x40, 0x3F],
            'V': [0x1F, 0x20, 0x40, 0x20, 0x1F],
            'W': [0x7F, 0x20, 0x18, 0x20, 0x7F],
            'X': [0x63, 0x14, 0x08, 0x14, 0x63],
            'Y': [0x03, 0x04, 0x78, 0x04, 0x03],
            'Z': [0x61, 0x51, 0x49, 0x45, 0x43],
            '[': [0x00, 0x00, 0x7F, 0x41, 0x41],
            '\\': [0x02, 0x04, 0x08, 0x10, 0x20],
            ']': [0x41, 0x41, 0x7F, 0x00, 0x00],
            '^': [0x04, 0x02, 0x01, 0x02, 0x04],
            '_': [0x40, 0x40, 0x40, 0x40, 0x40],
            '`': [0x00, 0x01, 0x02, 0x04, 0x00],
            'a': [0x20, 0x54, 0x54, 0x54, 0x78],
            'b': [0x7F, 0x48, 0x44, 0x44, 0x38],
            'c': [0x38, 0x44, 0x44, 0x44, 0x20],
            'd': [0x38, 0x44, 0x44, 0x48, 0x7F],
            'e': [0x38, 0x54, 0x54, 0x54, 0x18],
            'f': [0x08, 0x7E, 0x09, 0x01, 0x02],
            'g': [0x08, 0x14, 0x54, 0x54, 0x3C],
            'h': [0x7F, 0x08, 0x04, 0x04, 0x78],
            'i': [0x00, 0x44, 0x7D, 0x40, 0x00],
            'j': [0x20, 0x40, 0x44, 0x3D, 0x00],
            'k': [0x00, 0x7F, 0x10, 0x28, 0x44],
            'l': [0x00, 0x41, 0x7F, 0x40, 0x00],
            'm': [0x7C, 0x04, 0x18, 0x04, 0x78],
            'n': [0x7C, 0x08, 0x04, 0x04, 0x78],
            'o': [0x38, 0x44, 0x44, 0x44, 0x38],
            'p': [0x7C, 0x14, 0x14, 0x14, 0x08],
            'q': [0x08, 0x14, 0x14, 0x18, 0x7C],
            'r': [0x7C, 0x08, 0x04, 0x04, 0x08],
            's': [0x48, 0x54, 0x54, 0x54, 0x20],
            't': [0x04, 0x3F, 0x44, 0x40, 0x20],
            'u': [0x3C, 0x40, 0x40, 0x20, 0x7C],
            'v': [0x1C, 0x20, 0x40, 0x20, 0x1C],
            'w': [0x3C, 0x40, 0x30, 0x40, 0x3C],
            'x': [0x44, 0x28, 0x10, 0x28, 0x44],
            'y': [0x0C, 0x50, 0x50, 0x50, 0x3C],
            'z': [0x44, 0x64, 0x54, 0x4C, 0x44],
            '{': [0x00, 0x08, 0x36, 0x41, 0x00],
            '|': [0x00, 0x00, 0x7F, 0x00, 0x00],
            '}': [0x00, 0x41, 0x36, 0x08, 0x00],
            '~': [0x02, 0x01, 0x02, 0x04, 0x02],
        }
        
        char_width = 6  # 5 pixels + 1 spacing
        char_height = 8
        
        # Draw background if specified
        if bg is not None:
            text_width = len(string) * char_width * scale
            text_height = char_height * scale
            self.fill_rect(x, y, text_width, text_height, bg)
        
        # Draw each character
        for i, char in enumerate(string):
            if char in font:
                char_data = font[char]
                char_x = x + i * char_width * scale
                
                # Draw the bitmap
                for col in range(5):  # 5 columns in font
                    column_data = char_data[col]
                    for row in range(8):  # 8 rows in font
                        if column_data & (1 << row):
                            # Draw pixel(s) for this bit
                            if scale == 1:
                                self.pixel(char_x + col, y + row, color)
                            else:
                                # Draw scaled pixel
                                for sx in range(scale):
                                    for sy in range(scale):
                                        self.pixel(char_x + col * scale + sx, y + row * scale + sy, color)
                
    def display(self):
        """
        Update display (compatibility method)
        With direct drawing, this is a no-op since drawing is immediate
        """
        pass
    
    def clear(self):
        """Clear the display (fill with black)"""
        self.fill(Color.BLACK)
        
    def pixel(self, x, y, color):
        """Set pixel at x,y to color"""
        # Direct drawing only (no framebuffer)
        if 0 <= x < self.width and 0 <= y < self.height:
            self.set_window(x, y, x, y)
            self.write_data(struct.pack('>H', color))