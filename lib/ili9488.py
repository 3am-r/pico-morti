"""
ILI9488 Display Driver for PicoCalc
320×320 4-inch IPS display with SPI interface
Optimized for ClockworkPi v2.0 mainboard
"""

from micropython import const
import framebuf
import time
from machine import Pin

# ILI9488 Command definitions
_CMD_NOP = const(0x00)
_CMD_SWRESET = const(0x01)  # Software Reset
_CMD_RDDID = const(0x04)     # Read Display ID
_CMD_RDDST = const(0x09)     # Read Display Status
_CMD_RDMODE = const(0x0A)    # Read Display Power Mode
_CMD_RDMADCTL = const(0x0B)  # Read Display MADCTL
_CMD_RDPIXFMT = const(0x0C)  # Read Display Pixel Format
_CMD_RDIMGFMT = const(0x0D)  # Read Display Image Format
_CMD_RDSELFDIAG = const(0x0F) # Read Display Self-Diagnostic
_CMD_SLPIN = const(0x10)     # Sleep In
_CMD_SLPOUT = const(0x11)    # Sleep Out
_CMD_PTLON = const(0x12)     # Partial Mode ON
_CMD_NORON = const(0x13)     # Normal Display Mode ON
_CMD_RDID4 = const(0xD3)     # Read ID4
_CMD_INVOFF = const(0x20)    # Display Inversion OFF
_CMD_INVON = const(0x21)     # Display Inversion ON
_CMD_GAMMASET = const(0x26)  # Gamma Set
_CMD_DISPOFF = const(0x28)   # Display OFF
_CMD_DISPON = const(0x29)    # Display ON
_CMD_CASET = const(0x2A)     # Column Address Set
_CMD_PASET = const(0x2B)     # Page Address Set
_CMD_RAMWR = const(0x2C)     # Memory Write
_CMD_RAMRD = const(0x2E)     # Memory Read
_CMD_PTLAR = const(0x30)     # Partial Area
_CMD_VSCRDEF = const(0x33)   # Vertical Scrolling Definition
_CMD_MADCTL = const(0x36)    # Memory Access Control
_CMD_VSCRSADD = const(0x37)  # Vertical Scrolling Start Address
_CMD_PIXFMT = const(0x3A)    # Interface Pixel Format
_CMD_RAMWRCONT = const(0x3C) # Write Memory Continue
_CMD_RAMRDCONT = const(0x3E) # Read Memory Continue
_CMD_WRDISBV = const(0x51)   # Write Display Brightness
_CMD_RDDISBV = const(0x52)   # Read Display Brightness
_CMD_WRCTRLD = const(0x53)   # Write CTRL Display

# ILI9488 Extended Commands
_CMD_IFMODE = const(0xB0)    # Interface Mode Control
_CMD_FRMCTR1 = const(0xB1)   # Frame Control (Normal Mode)
_CMD_FRMCTR2 = const(0xB2)   # Frame Control (Idle Mode)
_CMD_FRMCTR3 = const(0xB3)   # Frame Control (Partial Mode)
_CMD_INVCTR = const(0xB4)    # Display Inversion Control
_CMD_DFUNCTR = const(0xB6)   # Display Function Control
_CMD_PWCTR1 = const(0xC0)    # Power Control 1
_CMD_PWCTR2 = const(0xC1)    # Power Control 2
_CMD_PWCTR3 = const(0xC2)    # Power Control 3
_CMD_PWCTR4 = const(0xC3)    # Power Control 4
_CMD_PWCTR5 = const(0xC4)    # Power Control 5
_CMD_VMCTR1 = const(0xC5)    # VCOM Control
_CMD_RDID1 = const(0xDA)     # Read ID 1
_CMD_RDID2 = const(0xDB)     # Read ID 2
_CMD_RDID3 = const(0xDC)     # Read ID 3
_CMD_GMCTRP1 = const(0xE0)   # Positive Gamma Control
_CMD_GMCTRN1 = const(0xE1)   # Negative Gamma Control
_CMD_IMGFUNC = const(0xE9)   # Image Function Control
_CMD_ADJCTR3 = const(0xF7)   # Adjustment Control 3

# MADCTL bits
_MADCTL_MY = const(0x80)  # Row Address Order
_MADCTL_MX = const(0x40)  # Column Address Order
_MADCTL_MV = const(0x20)  # Row/Column Exchange
_MADCTL_ML = const(0x10)  # Vertical Refresh Order
_MADCTL_RGB = const(0x00) # RGB Order
_MADCTL_BGR = const(0x08) # BGR Order
_MADCTL_MH = const(0x04)  # Horizontal Refresh Order

# Color definitions (RGB565)
class Color:
    BLACK = const(0x0000)
    WHITE = const(0xFFFF)
    RED = const(0xF800)
    GREEN = const(0x07E0)
    BLUE = const(0x001F)
    YELLOW = const(0xFFE0)
    CYAN = const(0x07FF)
    MAGENTA = const(0xF81F)
    ORANGE = const(0xFC00)
    PURPLE = const(0x8010)
    GRAY = const(0x8410)
    DARK_GRAY = const(0x4208)
    LIGHT_GRAY = const(0xC618)

class ILI9488:
    """Driver for ILI9488 display controller"""

    def __init__(self, spi, width, height, reset, dc, cs, backlight=None, rotation=0):
        """
        Initialize ILI9488 display

        Args:
            spi: SPI bus instance
            width: Display width (320 for PicoCalc)
            height: Display height (320 for PicoCalc)
            reset: Reset pin
            dc: Data/Command pin
            cs: Chip Select pin
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
        self.cs.init(Pin.OUT, value=1)
        self.dc.init(Pin.OUT, value=0)
        if self.reset:
            self.reset.init(Pin.OUT, value=1)
        if self.backlight:
            self.backlight.init(Pin.OUT, value=1)

        # Create frame buffer for double buffering
        import gc
        gc.collect()
        self.buffer = bytearray(self.width * self.height * 2)  # RGB565
        self.framebuf = framebuf.FrameBuffer(
            self.buffer, self.width, self.height, framebuf.RGB565
        )

        # Initialize display
        self.init_display()

    def init_display(self):
        """Initialize the ILI9488 display"""
        # Hardware reset
        if self.reset:
            self.reset.value(1)
            time.sleep_ms(5)
            self.reset.value(0)
            time.sleep_ms(20)
            self.reset.value(1)
            time.sleep_ms(150)

        # Software reset
        self.write_cmd(_CMD_SWRESET)
        time.sleep_ms(150)

        # Power control
        self.write_cmd(_CMD_PWCTR1)
        self.write_data(bytearray([0x17, 0x15]))  # VRH, VRL

        self.write_cmd(_CMD_PWCTR2)
        self.write_data(bytearray([0x41]))  # VGH, VGL

        self.write_cmd(_CMD_VMCTR1)
        self.write_data(bytearray([0x00, 0x12, 0x80]))  # VCOM Control

        # Memory access control
        self.write_cmd(_CMD_MADCTL)
        madctl = 0
        if self.rotation == 0:
            madctl = _MADCTL_MX | _MADCTL_BGR
        elif self.rotation == 90:
            madctl = _MADCTL_MV | _MADCTL_BGR
        elif self.rotation == 180:
            madctl = _MADCTL_MY | _MADCTL_BGR
        elif self.rotation == 270:
            madctl = _MADCTL_MX | _MADCTL_MY | _MADCTL_MV | _MADCTL_BGR
        self.write_data(bytearray([madctl]))

        # Pixel format
        self.write_cmd(_CMD_PIXFMT)
        self.write_data(bytearray([0x55]))  # 16-bit RGB565

        # Frame rate control
        self.write_cmd(_CMD_FRMCTR1)
        self.write_data(bytearray([0xA0]))  # 60Hz

        # Display function control
        self.write_cmd(_CMD_DFUNCTR)
        self.write_data(bytearray([0x02, 0x02, 0x3B]))

        # Gamma correction
        self.write_cmd(_CMD_GMCTRP1)
        self.write_data(bytearray([
            0x00, 0x03, 0x09, 0x08, 0x16, 0x0A, 0x3F, 0x78,
            0x4C, 0x09, 0x0A, 0x08, 0x16, 0x1A, 0x0F
        ]))

        self.write_cmd(_CMD_GMCTRN1)
        self.write_data(bytearray([
            0x00, 0x16, 0x19, 0x03, 0x0F, 0x05, 0x32, 0x45,
            0x46, 0x04, 0x0E, 0x0D, 0x35, 0x37, 0x0F
        ]))

        # Exit sleep mode
        self.write_cmd(_CMD_SLPOUT)
        time.sleep_ms(120)

        # Display on
        self.write_cmd(_CMD_DISPON)
        time.sleep_ms(25)

        # Clear screen
        self.fill(Color.BLACK)

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

        # Page address set
        self.write_cmd(_CMD_PASET)
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
        self.framebuf.fill(color)
        self.display()

    def pixel(self, x, y, color):
        """Draw a pixel"""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.framebuf.pixel(x, y, color)

    def hline(self, x, y, width, color):
        """Draw horizontal line"""
        self.framebuf.hline(x, y, width, color)

    def vline(self, x, y, height, color):
        """Draw vertical line"""
        self.framebuf.vline(x, y, height, color)

    def line(self, x0, y0, x1, y1, color):
        """Draw line between two points"""
        self.framebuf.line(x0, y0, x1, y1, color)

    def rect(self, x, y, width, height, color):
        """Draw rectangle outline"""
        self.framebuf.rect(x, y, width, height, color)

    def fill_rect(self, x, y, width, height, color):
        """Fill rectangle with color"""
        self.framebuf.fill_rect(x, y, width, height, color)

    def circle(self, x, y, radius, color):
        """Draw circle outline"""
        for angle in range(0, 360, 2):
            import math
            px = int(x + radius * math.cos(math.radians(angle)))
            py = int(y + radius * math.sin(math.radians(angle)))
            self.pixel(px, py, color)

    def text(self, string, x, y, color):
        """Draw text at position"""
        self.framebuf.text(string, x, y, color)

    def display(self):
        """Update display with frame buffer contents"""
        self.set_window(0, 0, self.width - 1, self.height - 1)
        self.write_data(self.buffer)

    def set_brightness(self, level):
        """Set display brightness using PWM backlight"""
        if self.backlight:
            from machine import PWM
            pwm = PWM(self.backlight)
            pwm.freq(1000)
            duty = int((level / 100) * 65535)
            pwm.duty_u16(duty)

    def sleep(self):
        """Put display to sleep"""
        self.write_cmd(_CMD_DISPOFF)
        time.sleep_ms(10)
        self.write_cmd(_CMD_SLPIN)

    def wake(self):
        """Wake display from sleep"""
        self.write_cmd(_CMD_SLPOUT)
        time.sleep_ms(120)
        self.write_cmd(_CMD_DISPON)