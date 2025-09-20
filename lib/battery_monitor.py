"""
Battery Monitor for UPS Module
Reads battery percentage and status via I2C communication
Compatible with 5V I2C UPS modules for Raspberry Pi Pico
"""

import machine
import time

class BatteryMonitor:
    def __init__(self, sda_pin=0, scl_pin=1, i2c_addr=0x36):
        """
        Initialize battery monitor
        sda_pin: I2C SDA pin (default GPIO0 for Pico 2 WH)
        scl_pin: I2C SCL pin (default GPIO1 for Pico 2 WH) 
        i2c_addr: I2C address of UPS module (common addresses: 0x36, 0x6B)
        """
        self.i2c_addr = i2c_addr
        self.i2c = None
        self.last_reading = {'percentage': -1, 'voltage': 0.0, 'status': 'Unknown'}
        
        try:
            # Validate pin numbers
            if not (0 <= sda_pin <= 28 and 0 <= scl_pin <= 28):
                raise ValueError(f"Invalid pin numbers: SDA={sda_pin}, SCL={scl_pin}")
            
            # Determine I2C bus (0 or 1) based on pin numbers
            # I2C0: pins 0,1,4,5,8,9,12,13,16,17,20,21
            # I2C1: pins 2,3,6,7,10,11,14,15,18,19,26,27
            if sda_pin in [0, 4, 8, 12, 16, 20]:
                i2c_id = 0
            elif sda_pin in [2, 6, 10, 14, 18, 26]:
                i2c_id = 1
            else:
                # Try I2C0 as default
                i2c_id = 0
            
            # Initialize I2C with conservative frequency to avoid issues
            self.i2c = machine.I2C(i2c_id, 
                                  sda=machine.Pin(sda_pin), 
                                  scl=machine.Pin(scl_pin), 
                                  freq=100000)  # Use slower, more reliable frequency
            
            # Quick scan for devices (with timeout protection)
            devices = self.i2c.scan()
            
            if devices:
                print(f"I2C devices found on GP{sda_pin}/GP{scl_pin}: {[hex(addr) for addr in devices]}")
                
                if self.i2c_addr not in devices:
                    # Try common UPS module addresses
                    common_addresses = [0x36, 0x6B, 0x17, 0x55, 0x43]  # Added 0x43
                    for addr in common_addresses:
                        if addr in devices:
                            self.i2c_addr = addr
                            print(f"✅ Found potential UPS at {hex(addr)}")
                            break
                    else:
                        # No known addresses, but devices exist
                        # Use first device and see if it responds like a UPS
                        self.i2c_addr = devices[0]
                        print(f"⚠️ Unknown device at {hex(self.i2c_addr)}, testing...")
            else:
                # No devices found on this I2C bus
                self.i2c = None
                    
        except Exception as e:
            # Don't print errors for invalid pin configurations
            if "bad SCL pin" not in str(e) and "bad SDA pin" not in str(e):
                print(f"I2C init error GP{sda_pin}/GP{scl_pin}: {e}")
            self.i2c = None
            
    def read_battery_percentage(self):
        """Read battery percentage from UPS module"""
        if not self.i2c:
            return -1
            
        try:
            # Different UPS modules use different register layouts
            # Try common methods with device-specific handling
            
            # Special handling for device at 0x43
            if self.i2c_addr == 0x43:
                # This device might be a sensor or different type of I2C device
                # Try gentle probing with minimal data requests
                try:
                    # Some devices at 0x43 might be sensors that need specific commands
                    # Try reading status register first
                    data = self.i2c.readfrom_mem(self.i2c_addr, 0x00, 1)
                    value = data[0]
                    if 0 <= value <= 100:
                        return value
                except:
                    pass
                    
                try:
                    # Try different register for 0x43 devices
                    data = self.i2c.readfrom_mem(self.i2c_addr, 0x01, 1)
                    value = data[0]
                    if 0 <= value <= 100:
                        return value
                except:
                    pass
                    
                # If direct register reads fail, this might not be a UPS
                return -1
            
            # Standard UPS module methods
            # Method 1: Single register read (common for many UPS modules)
            try:
                data = self.i2c.readfrom(self.i2c_addr, 1)
                percentage = data[0]
                if 0 <= percentage <= 100:
                    return percentage
            except Exception as e:
                # EIO errors are common with incompatible devices
                if "EIO" in str(e):
                    return -1
                pass
                
            # Method 2: Register-based read (0x0E is common for battery percentage)
            try:
                data = self.i2c.readfrom_mem(self.i2c_addr, 0x0E, 1)
                percentage = data[0]
                if 0 <= percentage <= 100:
                    return percentage
            except Exception as e:
                if "EIO" in str(e):
                    return -1
                pass
                
            # Method 3: Try register 0x04 (another common location)
            try:
                data = self.i2c.readfrom_mem(self.i2c_addr, 0x04, 1)
                percentage = data[0]
                if 0 <= percentage <= 100:
                    return percentage
            except Exception as e:
                if "EIO" in str(e):
                    return -1
                pass
                
            # Method 4: Try multi-byte read and parse
            try:
                data = self.i2c.readfrom(self.i2c_addr, 2)
                # Some modules store percentage in first byte, status in second
                percentage = data[0]
                if 0 <= percentage <= 100:
                    return percentage
            except Exception as e:
                if "EIO" in str(e):
                    return -1
                pass
                
            return -1  # Unable to read
            
        except Exception as e:
            # Don't spam with EIO errors - these are expected for non-UPS devices
            if "EIO" not in str(e):
                print(f"Battery read error: {e}")
            return -1
            
    def read_battery_voltage(self):
        """Read battery voltage from UPS module"""
        if not self.i2c:
            return 0.0
            
        try:
            # Try reading voltage from common registers
            # Method 1: Register 0x02-0x03 (16-bit voltage)
            try:
                data = self.i2c.readfrom_mem(self.i2c_addr, 0x02, 2)
                voltage_raw = (data[0] << 8) | data[1]
                voltage = voltage_raw * 0.00125  # Common conversion factor
                if 2.5 <= voltage <= 5.5:  # Reasonable range
                    return voltage
            except:
                pass
                
            # Method 2: Register 0x08-0x09 
            try:
                data = self.i2c.readfrom_mem(self.i2c_addr, 0x08, 2)
                voltage_raw = (data[0] << 8) | data[1]
                voltage = voltage_raw * 0.001
                if 2.5 <= voltage <= 5.5:
                    return voltage
            except:
                pass
                
            return 0.0
            
        except Exception as e:
            print(f"Voltage read error: {e}")
            return 0.0
            
    def get_charging_status(self):
        """Get charging status from UPS module"""
        if not self.i2c:
            return "Unknown"
            
        try:
            # Try reading status register
            try:
                data = self.i2c.readfrom_mem(self.i2c_addr, 0x01, 1)
                status_byte = data[0]
                
                # Common status bit interpretations
                if status_byte & 0x01:  # Bit 0: Charging
                    return "Charging"
                elif status_byte & 0x02:  # Bit 1: Full
                    return "Full"
                elif status_byte & 0x04:  # Bit 2: Discharging
                    return "Discharging"
                else:
                    return "Unknown"
            except:
                pass
                
            # Alternative: infer from voltage and percentage
            voltage = self.read_battery_voltage()
            percentage = self.read_battery_percentage()
            
            if percentage >= 95:
                return "Full"
            elif voltage > 4.0:  # Likely charging if voltage is high
                return "Charging"
            else:
                return "Discharging"
                
        except Exception as e:
            print(f"Status read error: {e}")
            return "Unknown"
            
    def get_battery_info(self):
        """Get complete battery information with timeout protection"""
        if not self.i2c:
            return {'percentage': -1, 'voltage': 0.0, 'status': 'No UPS', 'available': False}
            
        try:
            # Quick timeout protection - don't hang the main app
            start_time = time.ticks_ms()
            
            percentage = self.read_battery_percentage()
            
            # Check timeout
            if time.ticks_diff(time.ticks_ms(), start_time) > 1000:  # 1 second max
                return {'percentage': -1, 'voltage': 0.0, 'status': 'Timeout', 'available': False}
            
            voltage = self.read_battery_voltage()
            status = self.get_charging_status()
            
            # Update cache only if we got valid data
            if percentage >= 0:
                self.last_reading['percentage'] = percentage
            if voltage > 0:
                self.last_reading['voltage'] = voltage
            self.last_reading['status'] = status
            
            return {
                'percentage': percentage if percentage >= 0 else self.last_reading['percentage'],
                'voltage': voltage if voltage > 0 else self.last_reading['voltage'],
                'status': status,
                'available': percentage >= 0 or voltage > 0
            }
            
        except Exception as e:
            print(f"Battery info error: {e}")
            return {'percentage': -1, 'voltage': 0.0, 'status': 'Error', 'available': False}
        
    def get_battery_icon(self, percentage):
        """Get battery icon based on percentage"""
        if percentage < 0:
            return "?"
        elif percentage >= 90:
            return "█████"  # Full
        elif percentage >= 70:
            return "████░"  # High
        elif percentage >= 50:
            return "███░░"  # Medium
        elif percentage >= 30:
            return "██░░░"  # Low
        elif percentage >= 10:
            return "█░░░░"  # Very low
        else:
            return "░░░░░"  # Critical
            
    def is_battery_critical(self, percentage):
        """Check if battery is at critical level"""
        return 0 <= percentage <= 15
        
    def is_battery_low(self, percentage):
        """Check if battery is at low level"""
        return 0 <= percentage <= 25
        
    def scan_for_ups_module(self):
        """Scan I2C bus for UPS modules and try to identify them"""
        if not self.i2c:
            return []
            
        devices = self.i2c.scan()
        ups_candidates = []
        
        for addr in devices:
            try:
                # Try to read a byte to see if it responds like a UPS module
                data = self.i2c.readfrom(addr, 1)
                value = data[0]
                
                # UPS modules often return percentage (0-100) or status values
                if 0 <= value <= 100:
                    ups_candidates.append(addr)
                    print(f"Possible UPS module at {hex(addr)}: value={value}")
                    
            except:
                continue
                
        return ups_candidates

# Test and diagnostic functions
def test_battery_monitor():
    """Test battery monitor functionality"""
    print("Testing Battery Monitor...")
    
    # Try different I2C configurations for Pico 2 WH
    configs = [
        {'sda': 0, 'scl': 1},   # Most common for UPS hats
        {'sda': 2, 'scl': 3},   # Alternative
        {'sda': 4, 'scl': 5},   # Common alternative
        {'sda': 6, 'scl': 7},   # Another option
        {'sda': 8, 'scl': 9},   # Another option
        {'sda': 12, 'scl': 13}, # Alternative
        {'sda': 16, 'scl': 17}, # Alternative
        {'sda': 20, 'scl': 21}, # Alternative
    ]
    
    for config in configs:
        print(f"\nTrying I2C config: SDA={config['sda']}, SCL={config['scl']}")
        
        try:
            monitor = BatteryMonitor(sda_pin=config['sda'], scl_pin=config['scl'])
            
            if monitor.i2c:
                info = monitor.get_battery_info()
                print(f"Battery info: {info}")
                
                if info['available']:
                    print("✅ Battery monitoring working!")
                    return monitor
                else:
                    print("❌ No valid battery data")
            else:
                print("❌ I2C initialization failed")
                
        except Exception as e:
            print(f"❌ Error: {e}")
            
    print("\n❌ No working battery monitor configuration found")
    return None

if __name__ == "__main__":
    test_battery_monitor()