"""
Elemental Sandbox - Interactive Physics Simulation
A reactive particle physics playground where elements interact dynamically
"""

import time
import machine
import random
import math
from lib.st7789 import Color

class Particle:
    """Base particle class with physics properties"""
    def __init__(self, x, y, particle_type, velocity_x=0, velocity_y=0):
        self.x = x
        self.y = y
        self.type = particle_type
        self.velocity_x = velocity_x
        self.velocity_y = velocity_y
        self.age = 0
        self.max_age = 1000  # Default lifespan
        self.temperature = 20  # Base temperature
        self.size = 1
        self.active = True
        
        # Type-specific properties
        if particle_type == "spark":
            self.color = Color.YELLOW
            self.temperature = 800
            self.max_age = 300
            self.gravity = -0.02  # Slight upward drift
            self.size = 1
        elif particle_type == "fire":
            self.color = Color.RED
            self.temperature = 1000
            self.max_age = 200
            self.gravity = -0.05  # Rises
            self.size = 2
        elif particle_type == "water":
            self.color = Color.BLUE
            self.temperature = 10
            self.max_age = 500
            self.gravity = 0.15  # Falls
            self.size = 1
        elif particle_type == "gas":
            self.color = Color.GREEN
            self.temperature = 20
            self.max_age = 400
            self.gravity = -0.08  # Rises strongly
            self.size = 3
        elif particle_type == "steam":
            self.color = Color.WHITE
            self.temperature = 100
            self.max_age = 150
            self.gravity = -0.1  # Rises
            self.size = 2
        elif particle_type == "ash":
            self.color = Color.GRAY
            self.temperature = 20
            self.max_age = 2000
            self.gravity = 0.05  # Falls slowly
            self.size = 1
        elif particle_type == "ember":
            self.color = Color.ORANGE
            self.temperature = 600
            self.max_age = 400
            self.gravity = 0.03  # Falls but glows
            self.size = 1
            
    def update(self):
        """Update particle physics"""
        if not self.active:
            return
            
        # Apply gravity
        self.velocity_y += self.gravity
        
        # Apply velocity
        self.x += self.velocity_x
        self.y += self.velocity_y
        
        # Apply drag/friction
        self.velocity_x *= 0.98
        self.velocity_y *= 0.98
        
        # Age the particle
        self.age += 1
        
        # Boundary checking with wrapping for some types
        if self.x < 0:
            if self.type in ["gas", "steam"]:
                self.x = 240  # Wrap around
            else:
                self.x = 0
                self.velocity_x *= -0.5
        elif self.x > 240:
            if self.type in ["gas", "steam"]:
                self.x = 0  # Wrap around  
            else:
                self.x = 240
                self.velocity_x *= -0.5
                
        if self.y < 0:
            if self.type in ["gas", "steam"]:
                self.active = False  # Dissipate at top
            else:
                self.y = 0
                self.velocity_y *= -0.3
        elif self.y > 240:
            self.y = 240
            self.velocity_y *= -0.3
            
        # Check if particle should die
        if self.age >= self.max_age:
            self.active = False
            
        # Temperature cooling
        if self.temperature > 20:
            self.temperature -= 1
            
    def draw(self, display):
        """Draw the particle"""
        if not self.active:
            return
            
        # Apply flickering effect for fire types
        if self.type in ["spark", "fire", "ember"]:
            if random.randint(0, 10) < 2:  # 20% chance to flicker
                return
                
        # Apply transparency based on age for some types
        alpha_factor = 1.0
        if self.type in ["steam", "gas"]:
            alpha_factor = 1.0 - (self.age / self.max_age)
            if alpha_factor < 0.3:
                return  # Too transparent to see
                
        # Draw particle based on size
        x, y = int(self.x), int(self.y)
        if self.size == 1:
            display.pixel(x, y, self.color)
        elif self.size == 2:
            display.fill_rect(x, y, 2, 2, self.color)
        elif self.size == 3:
            display.fill_rect(x-1, y-1, 3, 3, self.color)

class ElementalSandbox:
    def __init__(self, display, joystick, buttons):
        """Initialize Elemental Sandbox"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        # Simulation state
        self.particles = []
        self.cursor_x = 120
        self.cursor_y = 120
        self.cursor_size = 3
        
        # Interaction state
        self.last_button_time = {"A": 0, "X": 0, "Y": 0}
        self.button_cooldown = 100  # ms between button presses
        
        # Visual effects
        self.screen_heat = 0  # Overall screen temperature for effects
        self.last_update = 0
        
        # Performance tracking
        self.max_particles = 150  # Limit for performance
        
    def init(self):
        """Initialize app when opened"""
        self.particles = []
        self.cursor_x = 120
        self.cursor_y = 120
        self.screen_heat = 0
        
        # Start with a few gentle sparks
        for _ in range(3):
            self.add_particle(
                random.randint(50, 190),
                random.randint(100, 200),
                "spark",
                random.uniform(-0.5, 0.5),
                random.uniform(-0.2, 0.2)
            )
            
        self.draw_screen()
        
    def add_particle(self, x, y, particle_type, vel_x=0, vel_y=0):
        """Add a new particle to the simulation"""
        if len(self.particles) >= self.max_particles:
            # Remove oldest inactive particle
            for i, particle in enumerate(self.particles):
                if not particle.active:
                    del self.particles[i]
                    break
            else:
                # Remove oldest particle if all are active
                del self.particles[0]
                
        particle = Particle(x, y, particle_type, vel_x, vel_y)
        self.particles.append(particle)
        
    def update_cursor(self):
        """Update cursor position based on joystick"""
        direction = self.joystick.get_direction()
        
        if direction == 'UP':
            self.cursor_y = max(self.cursor_size, self.cursor_y - 3)
        elif direction == 'DOWN':
            self.cursor_y = min(240 - self.cursor_size, self.cursor_y + 3)
        elif direction == 'LEFT':
            self.cursor_x = max(self.cursor_size, self.cursor_x - 3)
        elif direction == 'RIGHT':
            self.cursor_x = min(240 - self.cursor_size, self.cursor_x + 3)
            
    def handle_button_input(self):
        """Handle button presses for particle creation"""
        current_time = time.ticks_ms()
        
        # Update button states (required for new button system)
        self.buttons.update()
        
        # A Button - Spark/Fire
        if (self.buttons.is_pressed('A') and 
            time.ticks_diff(current_time, self.last_button_time["A"]) > self.button_cooldown):
            
            self.last_button_time["A"] = current_time
            
            # Create spark particles
            for _ in range(3):
                self.add_particle(
                    self.cursor_x + random.randint(-5, 5),
                    self.cursor_y + random.randint(-5, 5),
                    "spark",
                    random.uniform(-1, 1),
                    random.uniform(-1, 1)
                )
                
        # X Button - Water
        if (self.buttons.is_pressed('X') and 
            time.ticks_diff(current_time, self.last_button_time["X"]) > self.button_cooldown):
            
            self.last_button_time["X"] = current_time
            
            # Create water stream
            for i in range(5):
                self.add_particle(
                    self.cursor_x + random.randint(-3, 3),
                    self.cursor_y,
                    "water",
                    random.uniform(-0.5, 0.5),
                    random.uniform(0.5, 2.0)  # Downward velocity
                )
                
        # Y Button - Gas
        if (self.buttons.is_pressed('Y') and 
            time.ticks_diff(current_time, self.last_button_time["Y"]) > self.button_cooldown):
            
            self.last_button_time["Y"] = current_time
            
            # Create gas cloud
            for _ in range(8):
                self.add_particle(
                    self.cursor_x + random.randint(-10, 10),
                    self.cursor_y + random.randint(-5, 5),
                    "gas",
                    random.uniform(-0.8, 0.8),
                    random.uniform(-0.5, 0.2)
                )
                
    def check_particle_interactions(self):
        """Check for particle interactions and reactions"""
        for i, particle1 in enumerate(self.particles):
            if not particle1.active:
                continue
                
            for j, particle2 in enumerate(self.particles[i+1:], i+1):
                if not particle2.active:
                    continue
                    
                # Calculate distance
                dx = particle1.x - particle2.x
                dy = particle1.y - particle2.y
                distance = math.sqrt(dx*dx + dy*dy)
                
                if distance < 8:  # Interaction radius
                    self.handle_interaction(particle1, particle2)
                    
    def handle_interaction(self, p1, p2):
        """Handle specific particle interactions"""
        # Spark + Gas = Fire explosion
        if ((p1.type == "spark" and p2.type == "gas") or 
            (p1.type == "gas" and p2.type == "spark")):
            
            # Create fire explosion
            explosion_x = (p1.x + p2.x) / 2
            explosion_y = (p1.y + p2.y) / 2
            
            for _ in range(12):
                self.add_particle(
                    explosion_x + random.randint(-15, 15),
                    explosion_y + random.randint(-15, 15),
                    "fire",
                    random.uniform(-2, 2),
                    random.uniform(-2, 2)
                )
                
            # Remove original particles
            p1.active = False
            p2.active = False
            self.screen_heat += 50
            
        # Fire + Gas = Bigger fire
        elif ((p1.type == "fire" and p2.type == "gas") or 
              (p1.type == "gas" and p2.type == "fire")):
              
            # Expand fire
            fire_x = p1.x if p1.type == "fire" else p2.x
            fire_y = p1.y if p1.type == "fire" else p2.y
            
            for _ in range(6):
                self.add_particle(
                    fire_x + random.randint(-8, 8),
                    fire_y + random.randint(-8, 8),
                    "fire",
                    random.uniform(-1, 1),
                    random.uniform(-1, 1)
                )
                
            if p2.type == "gas":
                p2.active = False
            self.screen_heat += 20
            
        # Water + Fire = Steam
        elif ((p1.type == "water" and p2.type == "fire") or 
              (p1.type == "fire" and p2.type == "water")):
              
            # Create steam
            steam_x = (p1.x + p2.x) / 2
            steam_y = (p1.y + p2.y) / 2
            
            for _ in range(4):
                self.add_particle(
                    steam_x + random.randint(-5, 5),
                    steam_y + random.randint(-5, 5),
                    "steam",
                    random.uniform(-0.5, 0.5),
                    random.uniform(-1, -0.2)
                )
                
            # Remove fire and water
            p1.active = False
            p2.active = False
            self.screen_heat -= 10
            
        # Water + Spark = Extinguish
        elif ((p1.type == "water" and p2.type == "spark") or 
              (p1.type == "spark" and p2.type == "water")):
              
            # Just extinguish
            p1.active = False
            p2.active = False
            
    def update_particles(self):
        """Update all particles"""
        for particle in self.particles:
            particle.update()
            
        # Remove inactive particles periodically
        if random.randint(0, 30) == 0:  # Every ~30 frames
            self.particles = [p for p in self.particles if p.active]
            
        # Cool down screen heat
        if self.screen_heat > 0:
            self.screen_heat -= 1
            
    def create_ash_from_fire(self):
        """Convert some fire particles to ash"""
        for particle in self.particles:
            if particle.type == "fire" and particle.age > 150:
                if random.randint(0, 20) == 0:  # 5% chance
                    particle.type = "ash"
                    particle.color = Color.GRAY
                    particle.temperature = 50
                    particle.gravity = 0.02
                    particle.max_age = 1000
                    
    def auto_spark_generation(self):
        """Automatically generate sparks to keep simulation alive"""
        if len([p for p in self.particles if p.active]) < 5:
            if random.randint(0, 100) == 0:  # 1% chance per frame
                self.add_particle(
                    random.randint(20, 220),
                    random.randint(180, 220),
                    "spark",
                    random.uniform(-0.3, 0.3),
                    random.uniform(-0.5, 0.1)
                )
                
    def draw_screen(self):
        """Draw the elemental sandbox"""
        # Clear screen with heat-based background
        if self.screen_heat > 100:
            self.display.fill(Color.RED)  # Hot background
        elif self.screen_heat > 50:
            bg_intensity = min(50, self.screen_heat - 50)
            bg_color = Color.rgb565(bg_intensity, 0, 0)  # Proper RGB565 reddish tint
            self.display.fill(bg_color)
        else:
            self.display.fill(Color.BLACK)
            
        # Draw all particles
        for particle in self.particles:
            particle.draw(self.display)
            
        # Draw cursor
        cursor_color = Color.WHITE
        if self.screen_heat > 80:
            cursor_color = Color.CYAN  # Cool cursor on hot background
            
        # Cursor crosshair
        self.display.hline(self.cursor_x - 5, self.cursor_y, 11, cursor_color)
        self.display.vline(self.cursor_x, self.cursor_y - 5, 11, cursor_color)
        self.display.rect(self.cursor_x - 2, self.cursor_y - 2, 5, 5, cursor_color)
        
        # Status indicators
        particle_count = len([p for p in self.particles if p.active])
        
        # Particle count indicator
        self.display.text(f"P:{particle_count}", 5, 5, Color.WHITE)
        
        # Heat indicator
        if self.screen_heat > 20:
            heat_bars = min(10, self.screen_heat // 10)
            for i in range(heat_bars):
                bar_color = Color.YELLOW if i < 5 else Color.RED
                self.display.fill_rect(200 + i * 3, 5, 2, 10, bar_color)
                
        # Control hints
        self.display.text("A:Spark X:Water Y:Gas", 30, 225, Color.GRAY)
        
        self.display.display()
        
    def update(self):
        """Main update loop"""
        current_time = time.ticks_ms()
        
        # Limit update rate for performance
        if time.ticks_diff(current_time, self.last_update) < 33:  # ~30 FPS
            return True
            
        self.last_update = current_time
        
        # Update cursor
        self.update_cursor()
        
        # Handle input
        self.handle_button_input()
        
        # Update physics
        self.update_particles()
        
        # Check interactions
        self.check_particle_interactions()
        
        # Special effects
        self.create_ash_from_fire()
        self.auto_spark_generation()
        
        # Draw everything
        self.draw_screen()
        
        # Exit check
        if self.buttons.is_pressed('B'):
            return False
            
        return True
        
    def cleanup(self):
        """Cleanup when exiting app"""
        self.particles.clear()