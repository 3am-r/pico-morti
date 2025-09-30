"""
Haptics/LED Abstraction Library
Provides haptic feedback with graceful fallback to LED indicators
"""

import time
from machine import Pin, PWM, Timer

class Haptics:
    def __init__(self, motor_pin=None, led_pin=None, fallback_led=25):
        """Initialize haptics with optional motor and LED pins"""
        self.motor = None
        self.led = None
        self.fallback_led = None
        self.has_motor = False
        self.has_led = False

        try:
            if motor_pin is not None:
                self.motor = PWM(Pin(motor_pin))
                self.motor.freq(1000)
                self.motor.duty_u16(0)
                self.has_motor = True
                print(f"Haptic motor initialized on pin {motor_pin}")
        except Exception as e:
            print(f"Haptic motor not available: {e}")

        try:
            if led_pin is not None:
                self.led = Pin(led_pin, Pin.OUT)
                self.led.value(0)
                self.has_led = True
                print(f"Haptic LED initialized on pin {led_pin}")
            elif not self.has_motor:
                self.fallback_led = Pin(fallback_led, Pin.OUT)
                self.fallback_led.value(0)
                self.has_led = True
                print(f"Using onboard LED (pin {fallback_led}) for haptic feedback")
        except Exception as e:
            print(f"LED feedback not available: {e}")

        self.active_timer = None
        self.pattern_timer = None
        self.pattern_index = 0
        self.pattern_data = []

    def tap(self, strength=1.0):
        """Single tap feedback"""
        if not self._has_output():
            return

        strength = max(0.0, min(1.0, strength))
        duration_ms = int(30 * (0.5 + strength * 0.5))

        if self.has_motor:
            duty = int(65535 * strength * 0.7)
            self.motor.duty_u16(duty)
            self._schedule_stop(duration_ms)
        elif self.has_led or self.fallback_led:
            self._led_on()
            self._schedule_stop(duration_ms)

    def pulse(self, duration_ms, strength=1.0):
        """Pulse feedback for specified duration"""
        if not self._has_output():
            return

        strength = max(0.0, min(1.0, strength))
        duration_ms = max(10, min(1000, duration_ms))

        if self.has_motor:
            duty = int(65535 * strength * 0.5)
            self.motor.duty_u16(duty)
            self._schedule_stop(duration_ms)
        elif self.has_led or self.fallback_led:
            self._led_pulse(duration_ms)

    def celebrate(self):
        """Celebration pattern - multiple quick pulses"""
        if not self._has_output():
            return

        pattern = [
            (50, 1.0),
            (50, 0),
            (50, 0.8),
            (50, 0),
            (100, 1.0),
            (100, 0),
            (50, 0.5),
            (50, 0),
            (50, 0.5),
        ]

        self._play_pattern(pattern)

    def success(self):
        """Success feedback pattern"""
        if not self._has_output():
            return

        pattern = [
            (100, 0.7),
            (50, 0),
            (150, 1.0),
        ]

        self._play_pattern(pattern)

    def error(self):
        """Error feedback pattern"""
        if not self._has_output():
            return

        pattern = [
            (200, 1.0),
            (100, 0),
            (200, 1.0),
        ]

        self._play_pattern(pattern)

    def warning(self):
        """Warning feedback pattern"""
        if not self._has_output():
            return

        pattern = [
            (150, 0.5),
            (100, 0),
            (150, 0.5),
            (100, 0),
            (150, 0.5),
        ]

        self._play_pattern(pattern)

    def heartbeat(self):
        """Heartbeat pattern"""
        if not self._has_output():
            return

        pattern = [
            (100, 0.8),
            (100, 0),
            (100, 1.0),
            (300, 0),
        ]

        self._play_pattern(pattern)

    def bounce(self, strength=1.0):
        """Bounce feedback - quick tap with decay"""
        if not self._has_output():
            return

        strength = max(0.0, min(1.0, strength))

        if self.has_motor:
            duty_start = int(65535 * strength)
            self.motor.duty_u16(duty_start)

            for i in range(5):
                time.sleep_ms(20)
                duty = int(duty_start * (1 - i * 0.2))
                self.motor.duty_u16(duty)

            self.motor.duty_u16(0)
        else:
            self.tap(strength)

    def ripple(self, waves=3, strength=0.7):
        """Ripple effect - diminishing waves"""
        if not self._has_output():
            return

        pattern = []
        for i in range(waves):
            wave_strength = strength * (1 - i * 0.3)
            pattern.extend([
                (50, wave_strength),
                (100, 0),
            ])

        self._play_pattern(pattern)

    def _play_pattern(self, pattern):
        """Play a haptic pattern"""
        self._stop_pattern()
        self.pattern_data = pattern
        self.pattern_index = 0
        self._pattern_step()

    def _pattern_step(self):
        """Execute one step of the pattern"""
        if self.pattern_index >= len(self.pattern_data):
            self._stop_pattern()
            return

        duration_ms, strength = self.pattern_data[self.pattern_index]
        self.pattern_index += 1

        if strength > 0:
            if self.has_motor:
                duty = int(65535 * strength * 0.7)
                self.motor.duty_u16(duty)
            elif self.has_led or self.fallback_led:
                self._led_on()
        else:
            if self.has_motor:
                self.motor.duty_u16(0)
            elif self.has_led or self.fallback_led:
                self._led_off()

        self.pattern_timer = Timer(-1)
        self.pattern_timer.init(
            period=duration_ms,
            mode=Timer.ONE_SHOT,
            callback=lambda t: self._pattern_step()
        )

    def _stop_pattern(self):
        """Stop any running pattern"""
        if self.pattern_timer:
            self.pattern_timer.deinit()
            self.pattern_timer = None

        if self.has_motor:
            self.motor.duty_u16(0)
        if self.has_led or self.fallback_led:
            self._led_off()

    def _led_on(self):
        """Turn LED on"""
        if self.led:
            self.led.value(1)
        elif self.fallback_led:
            self.fallback_led.value(1)

    def _led_off(self):
        """Turn LED off"""
        if self.led:
            self.led.value(0)
        elif self.fallback_led:
            self.fallback_led.value(0)

    def _led_pulse(self, duration_ms):
        """Pulse LED for duration"""
        self._led_on()
        self._schedule_stop(duration_ms)

    def _schedule_stop(self, delay_ms):
        """Schedule stopping output after delay"""
        if self.active_timer:
            self.active_timer.deinit()

        self.active_timer = Timer(-1)
        self.active_timer.init(
            period=delay_ms,
            mode=Timer.ONE_SHOT,
            callback=lambda t: self._stop_output()
        )

    def _stop_output(self):
        """Stop all outputs"""
        if self.has_motor and self.motor:
            self.motor.duty_u16(0)
        if self.has_led and self.led:
            self.led.value(0)
        if self.fallback_led:
            self.fallback_led.value(0)

    def _has_output(self):
        """Check if any output is available"""
        return self.has_motor or self.has_led or self.fallback_led is not None

    def cleanup(self):
        """Clean up resources"""
        self._stop_pattern()
        if self.active_timer:
            self.active_timer.deinit()
            self.active_timer = None

        if self.has_motor:
            self.motor.duty_u16(0)
            self.motor.deinit()

        if self.has_led:
            self.led.value(0)

        if self.fallback_led:
            self.fallback_led.value(0)


def get_haptics():
    """Factory function to get appropriate haptics for hardware"""
    try:
        from devices.hardware_runtime import get_hardware_config
        hw_config = get_hardware_config()

        motor_pin = hw_config.get("HAPTICS", {}).get("MOTOR_PIN")
        led_pin = hw_config.get("HAPTICS", {}).get("LED_PIN")

        if not motor_pin and not led_pin:
            onboard_led = hw_config.get("PERIPHERALS", {}).get("ONBOARD_LED", 25)
            return Haptics(motor_pin=None, led_pin=None, fallback_led=onboard_led)

        return Haptics(motor_pin=motor_pin, led_pin=led_pin)

    except Exception as e:
        print(f"Using default haptics configuration: {e}")
        return Haptics(motor_pin=None, led_pin=None, fallback_led=25)