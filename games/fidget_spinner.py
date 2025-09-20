"""
Fidget Spinner - Ultra realistic physics-based fidget spinner
Features: Momentum, friction, visual blur effects, realistic spinning physics
"""

import time
import math
from lib.st7789 import Color

class FidgetSpinner:
    def __init__(self, display, joystick, buttons):
        """Initialize the fidget spinner app"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        # Spinner physics
        self.angle = 0.0  # Current rotation angle (radians)
        self.angular_velocity = 0.0  # Current spinning speed (rad/s)
        self.max_velocity = 50.0  # Maximum spinning speed
        self.friction_coefficient = 0.985  # Energy loss per frame (realistic friction)
        self.spin_impulse = 8.0  # Impulse added per button press
        self.min_velocity = 0.05  # Below this, spinner stops
        
        # Visual properties
        self.center_x = 120
        self.center_y = 120
        self.bearing_radius = 15  # Center bearing size
        self.weight_radius = 25   # Weight/arm size
        self.arm_length = 65      # Distance from center to weights
        
        # Animation and effects
        self.last_update = time.ticks_ms()
        self.spin_count = 0
        self.total_spins = 0.0
        self.last_angle = 0.0
        
        # Visual effects
        self.blur_trails = []  # For motion blur effect
        self.max_trails = 8
        
        # Performance tracking
        self.max_speed_reached = 0.0
        self.current_rpm = 0.0
        
    def init(self):
        """Initialize app when opened"""
        self.angle = 0.0
        self.angular_velocity = 0.0
        self.spin_count = 0
        self.total_spins = 0.0
        self.max_speed_reached = 0.0
        self.blur_trails = []
        self.draw_screen()
        
    def apply_spin_impulse(self):
        """Apply spin impulse when A is pressed"""
        # Add energy to the spinner
        self.angular_velocity += self.spin_impulse
        
        # Cap at maximum velocity (realistic limit)
        if self.angular_velocity > self.max_velocity:
            self.angular_velocity = self.max_velocity
            
        # Track max speed for stats
        if self.angular_velocity > self.max_speed_reached:
            self.max_speed_reached = self.angular_velocity
            
    def update_physics(self, delta_time):
        """Update spinner physics with realistic friction"""
        if abs(self.angular_velocity) < self.min_velocity:
            self.angular_velocity = 0.0
            return
            
        # Apply friction (exponential decay for realism)
        self.angular_velocity *= self.friction_coefficient
        
        # Update angle
        self.angle += self.angular_velocity * delta_time
        
        # Keep angle in bounds
        while self.angle >= 2 * math.pi:
            self.angle -= 2 * math.pi
            self.total_spins += 1
            
        # Calculate RPM for display
        self.current_rpm = abs(self.angular_velocity) * 60 / (2 * math.pi)
        
    def update_blur_trails(self):
        """Update motion blur trails for realistic visual effect"""
        if abs(self.angular_velocity) > 1.0:  # Only create trails when spinning fast
            # Add current angle to trail
            trail_data = {
                'angle': self.angle,
                'intensity': min(255, int(abs(self.angular_velocity) * 5))
            }
            self.blur_trails.append(trail_data)
            
            # Remove old trails
            if len(self.blur_trails) > self.max_trails:
                self.blur_trails.pop(0)
        else:
            # Clear trails when spinning slowly
            self.blur_trails = []
            
    def draw_spinner(self):
        """Draw the fidget spinner with realistic 3D effect"""
        # Draw motion blur trails first
        for i, trail in enumerate(self.blur_trails):
            alpha = (i + 1) / len(self.blur_trails)  # Fade effect
            intensity = int(trail['intensity'] * alpha * 0.3)
            
            if intensity > 20:  # Only draw visible trails
                trail_color = Color.rgb565(intensity, intensity, intensity + 10)
                self.draw_spinner_shape(trail['angle'], trail_color, alpha * 0.7)
        
        # Determine main color based on speed
        if self.angular_velocity > 30:
            main_color = Color.RED  # Super fast - red hot!
        elif self.angular_velocity > 20:
            main_color = Color.ORANGE  # Fast - orange
        elif self.angular_velocity > 10:
            main_color = Color.YELLOW  # Medium - yellow
        elif self.angular_velocity > 2:
            main_color = Color.CYAN  # Slow - cyan
        else:
            main_color = Color.WHITE  # Very slow/stopped - white
            
        # Draw main spinner
        self.draw_spinner_shape(self.angle, main_color, 1.0)
        
        # Draw center bearing (always visible)
        self.display.fill_circle(self.center_x, self.center_y, self.bearing_radius, Color.DARK_GRAY)
        self.display.circle(self.center_x, self.center_y, self.bearing_radius, Color.WHITE)
        self.display.fill_circle(self.center_x, self.center_y, self.bearing_radius - 5, Color.BLACK)
        
    def draw_spinner_shape(self, angle, color, alpha=1.0):
        """Draw the spinner shape at given angle"""
        # Calculate positions of three weights (120 degrees apart)
        for i in range(3):
            weight_angle = angle + (i * 2 * math.pi / 3)
            
            # Calculate weight position
            weight_x = self.center_x + int(self.arm_length * math.cos(weight_angle))
            weight_y = self.center_y + int(self.arm_length * math.sin(weight_angle))
            
            # Draw arm (connecting line)
            arm_color = Color.rgb565(
                int(128 * alpha), 
                int(128 * alpha), 
                int(140 * alpha)
            ) if alpha < 1.0 else Color.GRAY
            
            self.display.line(self.center_x, self.center_y, weight_x, weight_y, arm_color)
            
            # Draw weight with 3D effect
            if alpha >= 0.7:  # Only draw full weights for main spinner
                # Outer weight
                self.display.fill_circle(weight_x, weight_y, self.weight_radius, color)
                
                # Inner detail
                inner_color = Color.WHITE if color != Color.WHITE else Color.LIGHT_GRAY
                self.display.fill_circle(weight_x, weight_y, self.weight_radius - 8, inner_color)
                
                # Center hole
                self.display.fill_circle(weight_x, weight_y, 8, Color.BLACK)
                self.display.circle(weight_x, weight_y, 8, Color.DARK_GRAY)
                
    def draw_hud(self):
        """Draw HUD with spinner stats"""
        # Background for HUD
        self.display.fill_rect(5, 5, 230, 35, Color.rgb565(20, 25, 30))
        self.display.rect(5, 5, 230, 35, Color.GRAY)
        
        # RPM display
        rpm_text = f"RPM: {int(self.current_rpm)}"
        self.display.text(rpm_text, 10, 10, Color.CYAN)
        
        # Speed indicator
        speed_text = f"Speed: {self.angular_velocity:.1f}"
        self.display.text(speed_text, 10, 20, Color.YELLOW)
        
        # Total spins
        spins_text = f"Spins: {int(self.total_spins)}"
        self.display.text(spins_text, 120, 10, Color.GREEN)
        
        # Max speed reached
        max_text = f"Max: {self.max_speed_reached:.1f}"
        self.display.text(max_text, 120, 20, Color.ORANGE)
        
        # Spin level indicator
        level = min(10, int(self.angular_velocity / 5))
        level_text = f"Level: {level}/10"
        self.display.text(level_text, 10, 30, Color.WHITE)
        
        # Performance bar
        bar_width = int((self.angular_velocity / self.max_velocity) * 100)
        if bar_width > 0:
            bar_color = Color.RED if bar_width > 80 else Color.ORANGE if bar_width > 50 else Color.GREEN
            self.display.fill_rect(130, 32, bar_width, 6, bar_color)
        self.display.rect(130, 32, 100, 6, Color.WHITE)
        
    def draw_instructions(self):
        """Draw control instructions"""
        if self.angular_velocity < 1.0:  # Only show when stopped/slow
            self.display.fill_rect(30, 200, 180, 35, Color.rgb565(15, 20, 25))
            self.display.rect(30, 200, 180, 35, Color.GRAY)
            
            self.display.text("🅰️ SPIN FASTER!", 60, 210, Color.WHITE)
            self.display.text("🅱️ Exit", 100, 220, Color.GRAY)
        else:
            # Show physics info when spinning
            friction_pct = int((1 - self.friction_coefficient) * 10000) / 100
            physics_text = f"Friction: {friction_pct}%"
            self.display.text(physics_text, 70, 210, Color.DARK_GRAY)
            
    def draw_screen(self):
        """Draw the complete fidget spinner interface"""
        # Clear screen with black background
        self.display.fill(Color.BLACK)
            
        # Draw main spinner
        self.draw_spinner()
        
        # Draw HUD
        self.draw_hud()
        
        # Draw instructions
        self.draw_instructions()
        
        # Add title
        title = "FIDGET SPINNER"
        title_x = (240 - len(title) * 8) // 2
        self.display.text(title, title_x, 50, Color.LIGHT_GRAY)
        
        self.display.display()
        
    def update(self):
        """Main update loop"""
        current_time = time.ticks_ms()
        delta_time = time.ticks_diff(current_time, self.last_update) / 1000.0
        self.last_update = current_time
        
        # Update button states
        self.buttons.update()
        
        # Handle input
        if self.buttons.is_pressed('A'):
            self.apply_spin_impulse()
            
        # Physics update
        self.update_physics(delta_time)
        
        # Visual effects update
        self.update_blur_trails()
        
        # Redraw screen
        self.draw_screen()
        
        # Exit check
        if self.buttons.is_pressed('B'):
            return False
            
        return True
        
    def cleanup(self):
        """Cleanup when exiting app"""
        pass