"""
Boot configuration for Pico-LCD-1.3 application
Adds lib folder to system path and performs initial setup
"""

import sys
import gc

# Add lib folder to system path
if '/lib' not in sys.path:
    sys.path.append('/lib')

if '/apps' not in sys.path:
    sys.path.append('/apps')

if '/games' not in sys.path:
    sys.path.append('/games')

if '/stores' not in sys.path:
    sys.path.append('/stores')

# Enable garbage collection
gc.enable()

# Pre-import essential modules to speed up main.py
try:
    import machine
    import time
    from machine import Pin, SPI
except ImportError as e:
    print(f"Boot error: {e}")

print("Boot sequence complete")
print("Starting application...")