"""
GT911 Capacitive Touch Controller Driver for MicroPython
I2C interface at address 0x5D
Supports up to 5 touch points
"""

from machine import Pin, I2C
import time
import struct

# GT911 Register addresses
GT911_REG_STATUS = const(0x814E)
GT911_REG_POINT_INFO = const(0x814F)
GT911_REG_POINT1_X_L = const(0x8150)
GT911_REG_CONFIG = const(0x8047)
GT911_REG_PRODUCT_ID = const(0x8140)
GT911_REG_FIRMWARE_VERSION = const(0x8144)

class GT911:
    def __init__(self, i2c_id=0, sda_pin=8, scl_pin=9, rst_pin=10, int_pin=11, addr=0x5D):
        """
        Initialize GT911 touch controller
        
        Args:
            i2c_id: I2C bus ID (0 or 1)
            sda_pin: I2C SDA pin
            scl_pin: I2C SCL pin
            rst_pin: Touch reset pin
            int_pin: Touch interrupt pin
            addr: I2C address (0x5D or 0x14)
        """
        self.addr = addr
        self.width = 320
        self.height = 480
        
        # Initialize pins
        self.rst = Pin(rst_pin, Pin.OUT)
        self.int = Pin(int_pin, Pin.IN, Pin.PULL_UP)
        
        # Initialize I2C
        self.i2c = I2C(i2c_id, 
                      sda=Pin(sda_pin),
                      scl=Pin(scl_pin),
                      freq=400000)
        
        # Reset sequence
        self.reset()
        
        # Check if device is responding
        self.initialized = self.check_device()
        
        if self.initialized:
            self.configure()
            print(f"GT911 initialized at address 0x{addr:02X}")
        else:
            print(f"GT911 not found at address 0x{addr:02X}")
    
    def reset(self):
        """Reset the touch controller"""
        # Reset sequence for I2C address 0x5D
        self.int.init(Pin.OUT)
        self.int.value(0)
        self.rst.value(0)
        time.sleep_ms(10)
        
        self.rst.value(1)
        time.sleep_ms(10)
        
        self.int.init(Pin.IN, Pin.PULL_UP)
        time.sleep_ms(50)
    
    def check_device(self):
        """Check if GT911 is present"""
        try:
            # Try to read product ID
            product_id = self.read_reg(GT911_REG_PRODUCT_ID, 4)
            if product_id:
                pid = ''.join(chr(b) for b in product_id if 32 <= b <= 126)
                if "911" in pid or "GT" in pid:
                    print(f"GT911 Product ID: {pid}")
                    return True
        except:
            pass
        
        # Try alternate address if primary fails
        if self.addr == 0x5D:
            self.addr = 0x14
            try:
                product_id = self.read_reg(GT911_REG_PRODUCT_ID, 4)
                if product_id:
                    print(f"GT911 found at alternate address 0x14")
                    return True
            except:
                self.addr = 0x5D  # Restore original
        
        return False
    
    def configure(self):
        """Configure the touch controller"""
        # Set resolution
        config = bytearray(186)  # GT911 config is 186 bytes
        
        # Basic configuration
        config[0] = 0x00  # Config version
        config[1] = self.width & 0xFF
        config[2] = (self.width >> 8) & 0xFF
        config[3] = self.height & 0xFF
        config[4] = (self.height >> 8) & 0xFF
        config[5] = 0x05  # Max touch points
        config[6] = 0x0D  # Switch 1 & 2
        
        # Write config (optional - GT911 usually works with default config)
        # self.write_reg(GT911_REG_CONFIG, config)
    
    def read_reg(self, reg, length):
        """Read register from GT911"""
        try:
            # Write register address (big-endian)
            self.i2c.writeto(self.addr, bytes([reg >> 8, reg & 0xFF]))
            # Read data
            return self.i2c.readfrom(self.addr, length)
        except:
            return None
    
    def write_reg(self, reg, data):
        """Write register to GT911"""
        try:
            # Combine register address and data
            buf = bytearray(2 + len(data))
            buf[0] = reg >> 8
            buf[1] = reg & 0xFF
            buf[2:] = data
            self.i2c.writeto(self.addr, buf)
            return True
        except:
            return False
    
    def read_touches(self):
        """
        Read current touch points
        
        Returns:
            List of touch points, each as dict with 'x', 'y', 'id', 'size'
            Empty list if no touches
        """
        if not self.initialized:
            return []
        
        touches = []
        
        try:
            # Read touch status
            status = self.read_reg(GT911_REG_STATUS, 1)
            if not status:
                return []
            
            # Check if screen is touched and get number of points
            num_points = status[0] & 0x0F
            
            if num_points == 0 or num_points > 5:
                # Clear the status register
                self.write_reg(GT911_REG_STATUS, bytes([0x00]))
                return []
            
            # Read touch data (8 bytes per point)
            touch_data = self.read_reg(GT911_REG_POINT1_X_L, num_points * 8)
            if not touch_data:
                return []
            
            # Parse touch points
            for i in range(num_points):
                offset = i * 8
                x = touch_data[offset] | (touch_data[offset + 1] << 8)
                y = touch_data[offset + 2] | (touch_data[offset + 3] << 8)
                size = touch_data[offset + 4] | (touch_data[offset + 5] << 8)
                track_id = touch_data[offset + 6]
                
                # Validate coordinates
                if 0 <= x <= self.width and 0 <= y <= self.height:
                    touches.append({
                        'x': x,
                        'y': y,
                        'id': track_id,
                        'size': size
                    })
            
            # Clear the status register
            self.write_reg(GT911_REG_STATUS, bytes([0x00]))
            
        except Exception as e:
            print(f"GT911 read error: {e}")
        
        return touches
    
    def get_touch(self):
        """
        Get first touch point (simplified interface)
        
        Returns:
            Tuple (x, y) if touched, None if not touched
        """
        touches = self.read_touches()
        if touches:
            return (touches[0]['x'], touches[0]['y'])
        return None
    
    def is_touched(self):
        """Check if screen is currently being touched"""
        touches = self.read_touches()
        return len(touches) > 0
    
    def wait_for_touch(self, timeout=None):
        """
        Wait for a touch event
        
        Args:
            timeout: Timeout in milliseconds (None = wait forever)
            
        Returns:
            Tuple (x, y) if touched, None if timeout
        """
        start_time = time.ticks_ms()
        
        while True:
            touch = self.get_touch()
            if touch:
                return touch
            
            if timeout and time.ticks_diff(time.ticks_ms(), start_time) > timeout:
                return None
            
            time.sleep_ms(10)