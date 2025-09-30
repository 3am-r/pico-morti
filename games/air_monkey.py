"""
Enhanced AirMonkey Game - Advanced platformer with difficulty settings
Features: Save progress, left/right movement, double jump, difficulty modes
"""

import time
import random
import json
from lib.st7789 import Color

class AirMonkey:
    def __init__(self, display, joystick, buttons):
        """Initialize enhanced AirMonkey game"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        # Game state
        self.game_state = "menu"  # "menu", "difficulty", "playing", "level_complete", "game_over", "paused"
        self.difficulty = "medium"  # "easy", "medium", "hard"
        self.score = 0
        self.level = 1
        self.lives = 3
        self.high_score = 0
        
        # Save/Load progress
        self.save_available = False
        self.load_save_data()
        
        # Monkey properties
        self.monkey_x = 50
        self.monkey_y = 180
        self.monkey_vel_x = 0
        self.monkey_vel_y = 0
        self.monkey_on_ground = True
        self.monkey_width = 16
        self.monkey_height = 12
        self.facing_right = True
        
        # Jump mechanics
        self.jump_count = 0
        self.max_jumps = 2  # Allow double jump
        self.jump_strength = -6  # Reduced first jump strength
        self.double_jump_strength = -10  # Higher second jump strength
        self.last_jump_time = 0
        
        # Movement physics
        self.gravity = 0.5
        self.move_speed = 3
        self.max_vel_x = 5
        self.friction = 0.8
        self.ground_y = 180
        
        # Bananas and obstacles
        self.bananas = []
        self.obstacles = []
        self.power_ups = []
        self.banana_width = 8
        self.banana_height = 12
        self.banana_spawn_timer = 0
        
        # Level settings (will be adjusted by difficulty)
        self.bananas_collected = 0
        self.bananas_needed = 5
        self.time_limit = 30000
        self.level_start_time = 0
        self.banana_spawn_rate = 60
        
        # Visual effects
        self.jump_particles = []
        self.collect_effects = []
        self.trail_positions = []
        
        # Menu selection
        self.menu_option = 0
        self.difficulty_option = 1  # Default to medium
        
    def load_save_data(self):
        """Load saved progress"""
        try:
            with open("/stores/airmonkey_save.json", "r") as f:
                data = json.load(f)
                self.high_score = data.get("high_score", 0)
                
                # Check for saved game
                if "saved_game" in data:
                    self.save_available = True
                    self.saved_level = data["saved_game"].get("level", 1)
                    self.saved_score = data["saved_game"].get("score", 0)
                    self.saved_lives = data["saved_game"].get("lives", 3)
                    self.saved_difficulty = data["saved_game"].get("difficulty", "medium")
        except:
            self.high_score = 0
            self.save_available = False
            
    def save_game_progress(self):
        """Save current game progress"""
        try:
            save_data = {
                "high_score": max(self.high_score, self.score),
                "saved_game": {
                    "level": self.level,
                    "score": self.score,
                    "lives": self.lives,
                    "difficulty": self.difficulty
                }
            }
            with open("/stores/airmonkey_save.json", "w") as f:
                json.dump(save_data, f)
            self.save_available = True
        except Exception as e:
            print(f"Save error: {e}")
            
    def clear_save(self):
        """Clear saved game"""
        try:
            save_data = {"high_score": self.high_score}
            with open("/stores/airmonkey_save.json", "w") as f:
                json.dump(save_data, f)
            self.save_available = False
        except:
            pass
            
    def init(self):
        """Initialize game when opened"""
        self.game_state = "menu"
        self.menu_option = 0
        self.draw_screen()
        
    def apply_difficulty_settings(self):
        """Apply difficulty modifiers"""
        if self.difficulty == "easy":
            self.lives = 5
            self.gravity = 0.4
            self.jump_strength = -5  # Small first jump
            self.double_jump_strength = -11  # Higher second jump
            self.move_speed = 3.5
            self.time_multiplier = 1.5
            self.banana_spawn_multiplier = 1.3
            self.score_multiplier = 0.8
            self.obstacle_chance = 0.1
        elif self.difficulty == "medium":
            self.lives = 3
            self.gravity = 0.5
            self.jump_strength = -6  # Small first jump
            self.double_jump_strength = -10  # Higher second jump
            self.move_speed = 3
            self.time_multiplier = 1.0
            self.banana_spawn_multiplier = 1.0
            self.score_multiplier = 1.0
            self.obstacle_chance = 0.2
        else:  # hard
            self.lives = 2
            self.gravity = 0.6
            self.jump_strength = -7  # Small first jump
            self.double_jump_strength = -9  # Higher second jump
            self.move_speed = 2.5
            self.time_multiplier = 0.7
            self.banana_spawn_multiplier = 0.8
            self.score_multiplier = 1.5
            self.obstacle_chance = 0.3
            
    def reset_level(self):
        """Reset level-specific variables"""
        self.monkey_x = 50
        self.monkey_y = self.ground_y
        self.monkey_vel_x = 0
        self.monkey_vel_y = 0
        self.monkey_on_ground = True
        self.jump_count = 0
        self.facing_right = True
        
        self.bananas = []
        self.obstacles = []
        self.power_ups = []
        self.bananas_collected = 0
        self.banana_spawn_timer = 0
        self.jump_particles = []
        self.collect_effects = []
        self.trail_positions = []
        
        # Dynamic difficulty based on level
        base_needed = 5
        level_bonus = (self.level - 1) * 2
        self.bananas_needed = base_needed + level_bonus
        
        # Time limit with difficulty adjustment
        base_time = 30000
        time_reduction = (self.level - 1) * 2000
        self.time_limit = int(max(15000, base_time - time_reduction) * self.time_multiplier)
        
        # Spawn rate with difficulty adjustment
        base_rate = 60
        rate_reduction = (self.level - 1) * 5
        self.banana_spawn_rate = int(max(25, base_rate - rate_reduction) * self.banana_spawn_multiplier)
        
        self.level_start_time = time.ticks_ms()
        
    def draw_screen(self):
        """Draw the appropriate screen"""
        self.display.fill(Color.BLACK)
        
        if self.game_state == "menu":
            self.draw_menu()
        elif self.game_state == "difficulty":
            self.draw_difficulty_select()
        elif self.game_state == "playing":
            self.draw_game()
        elif self.game_state == "paused":
            self.draw_pause_menu()
        elif self.game_state == "level_complete":
            self.draw_level_complete()
        elif self.game_state == "game_over":
            self.draw_game_over()
            
        self.display.display()
        
    def draw_menu(self):
        """Draw enhanced main menu"""
        # Title
        self.display.text("AIRMONKEY", 75, 20, Color.YELLOW)
        self.display.text("EVOLVED", 85, 35, Color.ORANGE)
        
        # High score
        self.display.text(f"High Score: {self.high_score}", 65, 55, Color.CYAN)
        
        # Menu options
        options = []
        if self.save_available:
            options.append(f"Continue (Lv {self.saved_level})")
        options.append("New Game")
        options.append("Instructions")
        
        y_pos = 85
        for i, option in enumerate(options):
            color = Color.WHITE if i == self.menu_option else Color.GRAY
            if i == self.menu_option:
                self.display.text(">", 50, y_pos, Color.YELLOW)
            self.display.text(option, 65, y_pos, color)
            y_pos += 20
            
        # Monkey animation
        frame = (time.ticks_ms() // 500) % 2
        monkey_y = 150 + (frame * 5)
        self.display.text("   o", 110, monkey_y, Color.ORANGE)
        self.display.text("  /|\\", 105, monkey_y + 10, Color.ORANGE)
        self.display.text("  / \\", 105, monkey_y + 20, Color.ORANGE)
        
        # Controls hint
        self.display.text("Joy:Select A:Start", 60, 200, Color.GRAY)
        self.display.text("B:Exit", 95, 215, Color.GRAY)
        
    def draw_difficulty_select(self):
        """Draw difficulty selection screen"""
        self.display.text("SELECT DIFFICULTY", 55, 30, Color.CYAN)
        
        difficulties = [
            ("Easy", "5 lives, slower pace", Color.GREEN),
            ("Medium", "3 lives, balanced", Color.YELLOW),
            ("Hard", "2 lives, fast & tough", Color.RED)
        ]
        
        y_pos = 70
        for i, (name, desc, color) in enumerate(difficulties):
            if i == self.difficulty_option:
                self.display.fill_rect(30, y_pos - 2, 180, 35, Color.DARK_GRAY)
                self.display.text(">", 35, y_pos, color)
                
            self.display.text(name, 50, y_pos, color)
            self.display.text(desc, 50, y_pos + 15, Color.GRAY)
            y_pos += 40
            
        # Score multipliers
        self.display.text("Score multipliers:", 60, 190, Color.WHITE)
        self.display.text("Easy:x0.8 Med:x1.0 Hard:x1.5", 25, 205, Color.CYAN)
        
        self.display.text("Joy:Select A:Start", 60, 225, Color.GRAY)
        
    def draw_game(self):
        """Draw game screen with enhanced graphics"""
        # Simple sky background (solid color to fix visual glitches)
        self.display.fill_rect(0, 0, 240, self.ground_y + 12, Color.CYAN)
            
        # Ground
        self.display.fill_rect(0, self.ground_y + 12, 240, 240 - self.ground_y - 12, Color.GREEN)
        self.display.fill_rect(0, self.ground_y + 15, 240, 2, Color.GREEN)
        
        # Draw obstacles
        for obstacle in self.obstacles:
            self.draw_obstacle(obstacle)
            
        # Draw power-ups
        for power_up in self.power_ups:
            self.draw_power_up(power_up)
            
        # Draw trail effect for monkey
        for i, pos in enumerate(self.trail_positions):
            alpha = i / len(self.trail_positions)
            self.display.fill_rect(int(pos[0] + 6), int(pos[1] + 4), 4, 4, Color.ORANGE)
            
        # Draw monkey
        self.draw_enhanced_monkey()
        
        # Draw bananas
        for banana in self.bananas:
            self.draw_banana(banana['x'], banana['y'])
            
        # Draw effects
        self.draw_effects()
        
        # HUD
        self.draw_hud()
        
    def draw_enhanced_monkey(self):
        """Draw monkey with direction and animation"""
        x, y = int(self.monkey_x), int(self.monkey_y)
        
        # Add to trail
        self.trail_positions.append((x, y))
        if len(self.trail_positions) > 3:
            self.trail_positions.pop(0)
            
        # Flip based on direction
        if self.facing_right:
            # Head
            self.display.fill_rect(x + 6, y, 4, 4, Color.ORANGE)
            # Body
            self.display.fill_rect(x + 4, y + 4, 8, 6, Color.ORANGE)
            # Arms
            self.display.fill_rect(x + 2, y + 5, 2, 3, Color.ORANGE)
            self.display.fill_rect(x + 12, y + 5, 2, 3, Color.ORANGE)
            # Tail
            self.display.fill_rect(x, y + 6, 3, 2, Color.ORANGE)
        else:
            # Head
            self.display.fill_rect(x + 6, y, 4, 4, Color.ORANGE)
            # Body
            self.display.fill_rect(x + 4, y + 4, 8, 6, Color.ORANGE)
            # Arms
            self.display.fill_rect(x + 2, y + 5, 2, 3, Color.ORANGE)
            self.display.fill_rect(x + 12, y + 5, 2, 3, Color.ORANGE)
            # Tail
            self.display.fill_rect(x + 13, y + 6, 3, 2, Color.ORANGE)
            
        # Legs animation
        if self.monkey_on_ground:
            if abs(self.monkey_vel_x) > 0.5:  # Walking
                frame = (time.ticks_ms() // 100) % 2
                if frame == 0:
                    self.display.fill_rect(x + 5, y + 10, 2, 2, Color.ORANGE)
                    self.display.fill_rect(x + 9, y + 10, 2, 2, Color.ORANGE)
                else:
                    self.display.fill_rect(x + 4, y + 10, 2, 2, Color.ORANGE)
                    self.display.fill_rect(x + 10, y + 10, 2, 2, Color.ORANGE)
            else:  # Standing
                self.display.fill_rect(x + 5, y + 10, 2, 2, Color.ORANGE)
                self.display.fill_rect(x + 9, y + 10, 2, 2, Color.ORANGE)
        else:  # Jumping
            self.display.fill_rect(x + 6, y + 9, 4, 2, Color.ORANGE)
            
    def draw_obstacle(self, obstacle):
        """Draw obstacles"""
        x, y = int(obstacle['x']), int(obstacle['y'])
        if obstacle['type'] == 'spike':
            # Draw spike triangle
            for i in range(8):
                self.display.fill_rect(x + i, y + 8 - i, 16 - i*2, 1, Color.RED)
                
    def draw_power_up(self, power_up):
        """Draw power-ups"""
        x, y = int(power_up['x']), int(power_up['y'])
        if power_up['type'] == 'shield':
            self.display.circle(x + 6, y + 6, 6, Color.BLUE)
        elif power_up['type'] == 'speed':
            self.display.text(">", x, y, Color.GREEN)
            self.display.text(">", x + 5, y, Color.GREEN)
            
    def draw_pause_menu(self):
        """Draw pause menu"""
        # Darken background
        for y in range(0, 240, 2):
            self.display.fill_rect(0, y, 240, 1, Color.DARK_GRAY)
            
        # Menu box
        self.display.fill_rect(40, 60, 160, 120, Color.BLACK)
        self.display.rect(40, 60, 160, 120, Color.WHITE)
        
        self.display.text("PAUSED", 90, 80, Color.YELLOW)
        
        self.display.text("A: Resume", 75, 110, Color.WHITE)
        self.display.text("X: Save & Exit", 60, 130, Color.CYAN)
        self.display.text("B: Exit to Menu", 55, 150, Color.GRAY)
        
    def draw_hud(self):
        """Draw enhanced HUD"""
        # Score with multiplier indicator
        score_text = f"Score:{int(self.score)}"
        if self.score_multiplier != 1.0:
            score_text += f"x{self.score_multiplier}"
        self.display.text(score_text, 5, 5, Color.WHITE)
        
        # Level
        self.display.text(f"Lv:{self.level}", 120, 5, Color.CYAN)
        
        # Lives as hearts
        for i in range(self.lives):
            self.display.text("♥", 180 + i * 10, 5, Color.RED)
            
        # Bananas progress bar
        progress_width = int((self.bananas_collected / self.bananas_needed) * 60)
        self.display.rect(5, 20, 62, 8, Color.YELLOW)
        if progress_width > 0:
            self.display.fill_rect(6, 21, progress_width, 6, Color.YELLOW)
        self.display.text(f"{self.bananas_collected}/{self.bananas_needed}", 70, 20, Color.YELLOW)
        
        # Time with warning
        elapsed = time.ticks_diff(time.ticks_ms(), self.level_start_time)
        remaining = max(0, self.time_limit - elapsed)
        seconds = remaining // 1000
        
        time_color = Color.RED if seconds < 5 else Color.WHITE
        if seconds < 10:
            # Flash warning
            if (time.ticks_ms() // 500) % 2:
                self.display.text(f"Time:{seconds}s", 160, 20, time_color)
        else:
            self.display.text(f"Time:{seconds}s", 160, 20, time_color)
            
        # Jump indicator
        if self.jump_count < self.max_jumps:
            self.display.text(f"Jumps:{self.max_jumps - self.jump_count}", 5, 35, Color.CYAN)
            
    def draw_banana(self, x, y):
        """Draw animated banana"""
        # Rotate animation
        frame = (time.ticks_ms() // 200) % 4
        
        if frame == 0:
            self.display.fill_rect(int(x), int(y), 8, 12, Color.YELLOW)
        elif frame == 1:
            self.display.fill_rect(int(x) + 1, int(y), 6, 12, Color.YELLOW)
        elif frame == 2:
            self.display.fill_rect(int(x) + 2, int(y), 4, 12, Color.YELLOW)
        else:
            self.display.fill_rect(int(x) + 1, int(y), 6, 12, Color.YELLOW)
            
    def draw_effects(self):
        """Draw visual effects"""
        # Jump particles
        for particle in self.jump_particles:
            if particle['life'] > 0:
                self.display.fill_rect(int(particle['x']), int(particle['y']), 2, 2, Color.WHITE)
                
        # Collection effects
        for effect in self.collect_effects:
            if effect['life'] > 0:
                color = Color.YELLOW if effect['life'] > 10 else Color.WHITE
                self.display.circle(int(effect['x']), int(effect['y']), effect['life'] // 4, color)
                
    def draw_level_complete(self):
        """Draw level complete screen"""
        self.display.fill_rect(30, 60, 180, 120, Color.GREEN)
        self.display.rect(30, 60, 180, 120, Color.WHITE)
        
        self.display.text("LEVEL COMPLETE!", 55, 80, Color.WHITE)
        
        self.display.text(f"Level {self.level} done!", 75, 105, Color.YELLOW)
        self.display.text(f"Score: {int(self.score)}", 85, 125, Color.CYAN)
        
        # Time bonus
        elapsed = time.ticks_diff(time.ticks_ms(), self.level_start_time)
        time_bonus = int(max(0, (self.time_limit - elapsed) / 100) * self.score_multiplier)
        self.display.text(f"Time bonus: +{time_bonus}", 65, 145, Color.GREEN)
        
        self.display.text("A:Continue X:Save", 55, 165, Color.GRAY)
        
    def draw_game_over(self):
        """Draw game over screen"""
        self.display.fill_rect(20, 50, 200, 140, Color.RED)
        self.display.rect(20, 50, 200, 140, Color.WHITE)
        
        self.display.text("GAME OVER", 80, 70, Color.WHITE)
        
        self.display.text(f"Final Score: {int(self.score)}", 65, 100, Color.YELLOW)
        self.display.text(f"Level reached: {self.level}", 65, 120, Color.CYAN)
        
        # Check high score
        if self.score > self.high_score:
            self.display.text("NEW HIGH SCORE!", 65, 140, Color.GREEN)
            self.high_score = int(self.score)
            self.save_game_progress()
        else:
            self.display.text(f"High: {self.high_score}", 85, 140, Color.GRAY)
            
        self.display.text("A:Retry B:Menu", 70, 165, Color.GRAY)
        
    def update_physics(self):
        """Update enhanced physics with left/right movement"""
        # Apply gravity
        if not self.monkey_on_ground:
            self.monkey_vel_y += self.gravity
            
        # Apply friction to horizontal movement
        if self.monkey_on_ground:
            self.monkey_vel_x *= self.friction
            
        # Update position
        self.monkey_x += self.monkey_vel_x
        self.monkey_y += self.monkey_vel_y
        
        # Keep monkey on screen (horizontal wrapping)
        if self.monkey_x < 0:
            self.monkey_x = 0
            self.monkey_vel_x = 0
        elif self.monkey_x > 240 - self.monkey_width:
            self.monkey_x = 240 - self.monkey_width
            self.monkey_vel_x = 0
            
        # Ground collision
        if self.monkey_y >= self.ground_y:
            self.monkey_y = self.ground_y
            self.monkey_vel_y = 0
            if not self.monkey_on_ground:
                # Just landed
                self.create_jump_particles(self.monkey_x + 8, self.monkey_y + 12)
                self.jump_count = 0  # Reset jump count
            self.monkey_on_ground = True
        else:
            self.monkey_on_ground = False
            
    def handle_movement_input(self):
        """Handle left/right movement with joystick"""
        # Horizontal movement
        if not self.joystick.left_pin.value():
            self.monkey_vel_x = max(-self.max_vel_x, self.monkey_vel_x - self.move_speed)
            self.facing_right = False
        elif not self.joystick.right_pin.value():
            self.monkey_vel_x = min(self.max_vel_x, self.monkey_vel_x + self.move_speed)
            self.facing_right = True
            
    def handle_jump_input(self):
        """Handle jump and double jump"""
        current_time = time.ticks_ms()
        
        # Prevent jump spam
        if time.ticks_diff(current_time, self.last_jump_time) < 200:
            return
            
        if self.buttons.is_pressed('A'):
            if self.monkey_on_ground:
                # First jump from ground
                self.monkey_vel_y = self.jump_strength
                self.monkey_on_ground = False
                self.jump_count = 1
                self.create_jump_particles(self.monkey_x + 8, self.monkey_y + 12)
                self.last_jump_time = current_time
            elif self.jump_count < self.max_jumps:
                # Double jump in air
                self.monkey_vel_y = self.double_jump_strength
                self.jump_count += 1
                self.create_jump_particles(self.monkey_x + 8, self.monkey_y + 8)
                self.last_jump_time = current_time
                
    def create_jump_particles(self, x, y):
        """Create jump/landing particles"""
        for i in range(8):
            self.jump_particles.append({
                'x': x + random.randint(-10, 10),
                'y': y + random.randint(-5, 5),
                'vel_x': random.uniform(-1, 1),
                'vel_y': random.uniform(-2, 0),
                'life': 20
            })
            
    def create_collect_effect(self, x, y):
        """Create collection effect"""
        for i in range(12):
            self.collect_effects.append({
                'x': x + 4,
                'y': y + 6,
                'life': 25
            })
            
    def update_effects(self):
        """Update visual effects"""
        # Update particles
        for particle in self.jump_particles[:]:
            particle['life'] -= 1
            particle['x'] += particle['vel_x']
            particle['y'] += particle['vel_y']
            particle['vel_y'] += 0.2
            if particle['life'] <= 0:
                self.jump_particles.remove(particle)
                
        # Update collection effects
        for effect in self.collect_effects[:]:
            effect['life'] -= 1
            if effect['life'] <= 0:
                self.collect_effects.remove(effect)
                
    def spawn_banana(self):
        """Spawn bananas with obstacle chance"""
        # Regular banana
        banana = {
            'x': 240,
            'y': random.randint(80, self.ground_y - 20),
            'speed': random.uniform(1.5, 3.5 + self.level * 0.2)
        }
        self.bananas.append(banana)
        
        # Chance to spawn obstacle (based on difficulty)
        if random.random() < self.obstacle_chance and self.level > 1:
            obstacle = {
                'x': 240 + random.randint(50, 100),
                'y': self.ground_y,
                'type': 'spike',
                'speed': random.uniform(1.0, 2.5)
            }
            self.obstacles.append(obstacle)
            
    def update_bananas(self):
        """Update bananas and obstacles"""
        # Update bananas
        for banana in self.bananas[:]:
            banana['x'] -= banana['speed']
            
            if banana['x'] < -self.banana_width:
                self.bananas.remove(banana)
                continue
                
            # Collision with monkey
            monkey_rect = (self.monkey_x, self.monkey_y, self.monkey_width, self.monkey_height)
            banana_rect = (banana['x'], banana['y'], self.banana_width, self.banana_height)
            
            if self.check_collision(monkey_rect, banana_rect):
                self.bananas.remove(banana)
                self.bananas_collected += 1
                self.score += (10 + self.level * 5) * self.score_multiplier
                self.create_collect_effect(banana['x'], banana['y'])
                
        # Update obstacles
        for obstacle in self.obstacles[:]:
            obstacle['x'] -= obstacle['speed']
            
            if obstacle['x'] < -16:
                self.obstacles.remove(obstacle)
                continue
                
            # Collision with monkey
            monkey_rect = (self.monkey_x, self.monkey_y, self.monkey_width, self.monkey_height)
            obstacle_rect = (obstacle['x'], obstacle['y'] - 8, 16, 8)
            
            if self.check_collision(monkey_rect, obstacle_rect):
                # Hit obstacle!
                self.lives -= 1
                self.obstacles.remove(obstacle)
                self.create_jump_particles(self.monkey_x + 8, self.monkey_y + 8)
                
                if self.lives <= 0:
                    self.game_state = "game_over"
                    
    def check_collision(self, rect1, rect2):
        """Check rectangle collision"""
        x1, y1, w1, h1 = rect1
        x2, y2, w2, h2 = rect2
        
        return (x1 < x2 + w2 and x1 + w1 > x2 and
                y1 < y2 + h2 and y1 + h1 > y2)
                
    def check_level_completion(self):
        """Check if level is complete"""
        if self.bananas_collected >= self.bananas_needed:
            # Calculate time bonus
            elapsed = time.ticks_diff(time.ticks_ms(), self.level_start_time)
            time_bonus = int(max(0, (self.time_limit - elapsed) / 100) * self.score_multiplier)
            self.score += time_bonus
            self.game_state = "level_complete"
            return
            
        # Check time limit
        elapsed = time.ticks_diff(time.ticks_ms(), self.level_start_time)
        if elapsed >= self.time_limit:
            self.lives -= 1
            if self.lives <= 0:
                self.game_state = "game_over"
            else:
                self.reset_level()
                
    def update(self):
        """Update game logic"""
        if self.game_state == "menu":
            direction = self.joystick.get_direction_slow()
            
            # Navigate menu
            if direction == 'UP':
                max_options = 2 if self.save_available else 1
                self.menu_option = max(0, self.menu_option - 1)
                self.draw_screen()
            elif direction == 'DOWN':
                max_options = 2 if self.save_available else 1
                self.menu_option = min(max_options, self.menu_option + 1)
                self.draw_screen()
                
            if self.buttons.is_pressed('A'):
                if self.save_available and self.menu_option == 0:
                    # Continue saved game
                    self.level = self.saved_level
                    self.score = self.saved_score
                    self.lives = self.saved_lives
                    self.difficulty = self.saved_difficulty
                    self.apply_difficulty_settings()
                    self.reset_level()
                    self.game_state = "playing"
                elif (self.save_available and self.menu_option == 1) or (not self.save_available and self.menu_option == 0):
                    # New game
                    self.game_state = "difficulty"
                    self.difficulty_option = 1
                elif self.menu_option == 2 or (not self.save_available and self.menu_option == 1):
                    # Instructions (just flash them)
                    self.display.fill(Color.BLACK)
                    self.display.text("HOW TO PLAY", 75, 30, Color.YELLOW)
                    self.display.text("Joy: Move left/right", 40, 60, Color.WHITE)
                    self.display.text("A: Jump (2x for double)", 30, 80, Color.WHITE)
                    self.display.text("Collect bananas!", 60, 100, Color.YELLOW)
                    self.display.text("Avoid obstacles!", 60, 120, Color.RED)
                    self.display.text("Beat the timer!", 65, 140, Color.CYAN)
                    self.display.text("Press any button", 60, 180, Color.GRAY)
                    self.display.display()
                    time.sleep_ms(200)
                    while not self.buttons.is_pressed('A') and not self.buttons.is_pressed('B'):
                        time.sleep_ms(50)
                self.draw_screen()
                time.sleep_ms(200)
                
        elif self.game_state == "difficulty":
            direction = self.joystick.get_direction_slow()
            
            if direction == 'UP':
                self.difficulty_option = max(0, self.difficulty_option - 1)
                self.draw_screen()
            elif direction == 'DOWN':
                self.difficulty_option = min(2, self.difficulty_option + 1)
                self.draw_screen()
                
            if self.buttons.is_pressed('A'):
                self.difficulty = ["easy", "medium", "hard"][self.difficulty_option]
                self.apply_difficulty_settings()
                self.score = 0
                self.level = 1
                self.reset_level()
                self.game_state = "playing"
                self.clear_save()  # Clear any previous save
                time.sleep_ms(200)
            elif self.buttons.is_pressed('B'):
                # Go back to menu
                self.game_state = "menu"
                time.sleep_ms(200)
                
        elif self.game_state == "playing":
            # Check for pause
            if self.buttons.is_pressed('Y'):
                self.game_state = "paused"
                self.draw_screen()
                time.sleep_ms(200)
                return True
                
            # Movement input
            self.handle_movement_input()
            
            # Jump input
            self.handle_jump_input()
            
            # Update physics
            self.update_physics()
            self.update_effects()
            self.update_bananas()
            
            # Spawn bananas
            self.banana_spawn_timer += 1
            if self.banana_spawn_timer >= self.banana_spawn_rate:
                self.spawn_banana()
                self.banana_spawn_timer = 0
                
            # Check completion
            self.check_level_completion()
            
            self.draw_screen()
            
        elif self.game_state == "paused":
            if self.buttons.is_pressed('A'):
                self.game_state = "playing"
                time.sleep_ms(200)
            elif self.buttons.is_pressed('X'):
                # Save and exit
                self.save_game_progress()
                return False
            elif self.buttons.is_pressed('B'):
                # Exit without saving
                self.game_state = "menu"
                time.sleep_ms(200)
                
        elif self.game_state == "level_complete":
            if self.buttons.is_pressed('A'):
                self.level += 1
                self.reset_level()
                self.game_state = "playing"
                time.sleep_ms(200)
            elif self.buttons.is_pressed('X'):
                # Save progress
                self.save_game_progress()
                self.game_state = "menu"
                time.sleep_ms(200)
                
        elif self.game_state == "game_over":
            if self.buttons.is_pressed('A'):
                # Retry from level 1
                self.score = 0
                self.level = 1
                self.apply_difficulty_settings()
                self.reset_level()
                self.game_state = "playing"
                time.sleep_ms(200)
            elif self.buttons.is_pressed('B'):
                self.game_state = "menu"
                time.sleep_ms(200)
                
        # Check for exit
        if self.buttons.is_pressed('B') and self.game_state not in ["paused", "game_over", "difficulty"]:
            if self.game_state == "playing":
                self.game_state = "paused"
                self.draw_screen()
            else:
                return False
                
        return True
        
    def cleanup(self):
        """Cleanup when exiting game"""
        pass