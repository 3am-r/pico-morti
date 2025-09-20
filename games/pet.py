"""
XPet - Virtual Pet Game
Classic pet raising experience on Pico-LCD-1.3
"""

import time
import random
from lib.st7789 import Color

class XPet:
    def __init__(self, display, joystick, buttons):
        """Initialize XPet game"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        # Pet states
        self.pet = {
            "name": "XZarabino",
            "age": 0,  # in minutes
            "hunger": 50,  # 0-100 (100 = very hungry)
            "happiness": 50,  # 0-100 (100 = very happy)
            "health": 100,  # 0-100 (100 = perfect health)
            "energy": 75,  # 0-100 (100 = full energy)
            "cleanliness": 75,  # 0-100 (100 = very clean)
            "stage": "egg",  # egg, baby, child, teen, adult
            "is_sleeping": False,
            "is_sick": False,
            "illness_type": None,  # specific illness type
            "poop_count": 0,
            "birth_time": time.ticks_ms(),
            "weight": 50,  # 30-100 (optimal: 40-60)
            "nutrition": 75,  # 0-100 (nutritional health)
            "mood": 50,  # 0-100 (overall emotional state)
            "last_fed": 0,  # time since last feeding
            "last_played": 0,  # time since last play
            "care_quality": 50,  # overall care score affecting evolution
            "personality": "balanced",  # affects stat preferences
            "sleep_cycle": 0,  # natural sleep/wake cycle (0-23 hour equivalent)
            "circadian_rhythm": 12,  # preferred sleep time
            "loneliness": 0,  # 0-100 (increases when not played with)
            "stress": 0,  # 0-100 (affects all other stats)
            "natural_sleep": False  # distinguishes from manual sleep
        }
        
        # Animation frame
        self.animation_frame = 0
        self.last_update = time.ticks_ms()
        self.last_stat_decrease = time.ticks_ms()
        
        # Menu state
        self.menu_open = False
        self.menu_selection = 0
        self.menu_options = ["Feed", "Play", "Clean", "Medicine", "Sleep", "Stats"]
        
        # Feeding menu state
        self.feeding_menu = False
        self.feeding_selection = 0
        self.meal_options = [
            {"name": "Bread", "hunger": -15, "nutrition": 5, "weight": 3},
            {"name": "Fruit", "hunger": -10, "nutrition": 10, "weight": 1},
            {"name": "Meal", "hunger": -25, "nutrition": 15, "weight": 5},
            {"name": "Snack", "hunger": -5, "nutrition": 0, "weight": 2},
            {"name": "Treat", "hunger": -8, "nutrition": 3, "weight": 4}
        ]
        
        # Load saved pet if exists
        self.load_pet()
        
    def init(self):
        """Initialize app when opened"""
        self.menu_open = False
        self.menu_selection = 0
        self.draw_screen()
        
    def load_pet(self):
        """Load saved pet data"""
        try:
            with open("xpet.dat", "r") as f:
                lines = f.readlines()
                if lines:
                    data = lines[0].strip().split(",")
                    if len(data) >= 10:
                        self.pet["name"] = data[0]
                        self.pet["age"] = int(data[1])
                        self.pet["hunger"] = int(data[2])
                        self.pet["happiness"] = int(data[3])
                        self.pet["health"] = int(data[4])
                        self.pet["energy"] = int(data[5])
                        self.pet["cleanliness"] = int(data[6])
                        self.pet["stage"] = data[7]
                        self.pet["is_sleeping"] = data[8] == "True"
                        self.pet["poop_count"] = int(data[9])
        except:
            # New pet
            pass
            
    def save_pet(self):
        """Save pet data"""
        try:
            with open("xpet.dat", "w") as f:
                data = [
                    self.pet["name"],
                    str(self.pet["age"]),
                    str(self.pet["hunger"]),
                    str(self.pet["happiness"]),
                    str(self.pet["health"]),
                    str(self.pet["energy"]),
                    str(self.pet["cleanliness"]),
                    self.pet["stage"],
                    str(self.pet["is_sleeping"]),
                    str(self.pet["poop_count"])
                ]
                f.write(",".join(data) + "\n")
        except Exception as e:
            print(f"Save error: {e}")
            
    def update_stats(self):
        """Update pet statistics over time"""
        current_time = time.ticks_ms()
        
        # Update age (every minute)
        age_diff = time.ticks_diff(current_time, self.pet["birth_time"]) // 60000
        if age_diff > self.pet["age"]:
            self.pet["age"] = age_diff
            self.check_evolution()
            
        # Decrease stats over time (every 30 seconds)
        if time.ticks_diff(current_time, self.last_stat_decrease) > 30000:
            self.last_stat_decrease = current_time
            
            if not self.pet["is_sleeping"]:
                self.pet["hunger"] = min(100, self.pet["hunger"] + 2)
                self.pet["energy"] = max(0, self.pet["energy"] - 3)
                self.pet["cleanliness"] = max(0, self.pet["cleanliness"] - 2)
                
                # Happiness decreases if needs aren't met
                if self.pet["hunger"] > 70:
                    self.pet["happiness"] = max(0, self.pet["happiness"] - 5)
                if self.pet["cleanliness"] < 30:
                    self.pet["happiness"] = max(0, self.pet["happiness"] - 3)
                    
                # Health affected by overall condition
                if self.pet["hunger"] > 80 or self.pet["cleanliness"] < 20:
                    self.pet["health"] = max(0, self.pet["health"] - 2)
                    
                # Random poop generation
                if random.randint(0, 100) < 10:
                    self.pet["poop_count"] = min(3, self.pet["poop_count"] + 1)
                    
            else:
                # Sleeping restores energy
                self.pet["energy"] = min(100, self.pet["energy"] + 5)
                
            # Check if pet gets sick
            if self.pet["health"] < 30 and not self.pet["is_sick"]:
                self.pet["is_sick"] = random.randint(0, 100) < 30
                
    def check_evolution(self):
        """Check if pet should evolve"""
        age = self.pet["age"]
        
        if self.pet["stage"] == "egg" and age >= 2:
            self.pet["stage"] = "baby"
        elif self.pet["stage"] == "baby" and age >= 10:
            self.pet["stage"] = "child"
        elif self.pet["stage"] == "child" and age >= 30:
            self.pet["stage"] = "teen"
        elif self.pet["stage"] == "teen" and age >= 60:
            self.pet["stage"] = "adult"
            
    def draw_screen(self):
        """Draw the main XPet screen"""
        self.display.fill(Color.BLACK)
        
        if self.menu_open:
            self.draw_menu()
        else:
            self.draw_pet_view()
            
        self.display.display()
        
    def draw_pet_view(self):
        """Draw the pet and environment"""
        # Draw status bars at top
        self.draw_status_bars()
        
        # Draw pet sprite
        self.draw_pet_sprite()
        
        # Draw environment elements
        if self.pet["poop_count"] > 0:
            self.draw_poop()
            
        if self.pet["is_sick"]:
            self.draw_sick_indicator()
            
        if self.pet["is_sleeping"]:
            self.draw_sleep_indicator()
            
        # Instructions
        self.display.text("A:Menu B:Home", 70, 225, Color.GRAY)
        
    def draw_status_bars(self):
        """Draw status bars at top of screen"""
        # Pet name and age
        info_text = f"{self.pet['name']} Age:{self.pet['age']}m"
        self.display.text(info_text, 5, 5, Color.WHITE)
        
        # Mini status indicators
        y = 20
        stats = [
            ("H:", self.pet["hunger"], Color.ORANGE),  # Hunger (reversed - higher = hungrier)
            ("M:", self.pet["mood"], Color.YELLOW),      # Mood
            ("E:", self.pet["energy"], Color.GREEN),  # Energy
        ]
        
        x = 5
        for label, value, color in stats:
            self.display.text(label, x, y, Color.WHITE)
            # Draw mini bar
            bar_width = 30
            bar_x = x + 16
            self.display.rect(bar_x, y, bar_width, 6, Color.GRAY)
            fill_width = int((value / 100) * (bar_width - 2))
            if label == "H:":  # Hunger bar reversed
                fill_width = int(((100 - value) / 100) * (bar_width - 2))
            self.display.fill_rect(bar_x + 1, y + 1, fill_width, 4, color)
            x += 75
            
    def draw_pet_sprite(self):
        """Draw the pet sprite based on stage and state"""
        center_x = 120
        center_y = 120
        
        if self.pet["stage"] == "egg":
            self.draw_egg(center_x, center_y)
        elif self.pet["stage"] == "baby":
            self.draw_baby(center_x, center_y)
        elif self.pet["stage"] == "child":
            self.draw_child(center_x, center_y)
        elif self.pet["stage"] == "teen":
            self.draw_teen(center_x, center_y)
        else:  # adult
            self.draw_adult(center_x, center_y)
            
    def draw_egg(self, x, y):
        """Draw egg sprite"""
        # Wobble animation
        wobble = 2 if self.animation_frame % 2 == 0 else -2
        
        # Egg shape
        self.display.fill_circle(x + wobble, y, 20, Color.WHITE)
        self.display.fill_circle(x + wobble, y - 10, 18, Color.WHITE)
        
        # Crack pattern
        if self.pet["age"] >= 1:
            self.display.line(x - 5, y, x + 5, y - 3, Color.BLACK)
            self.display.line(x + 5, y - 3, x, y + 3, Color.BLACK)
            
    def draw_baby(self, x, y):
        """Draw baby pet sprite"""
        # Simple round body
        bounce = -3 if self.animation_frame % 2 == 0 else 0
        
        # Body
        self.display.fill_circle(x, y + bounce, 15, Color.CYAN)
        
        # Eyes
        self.display.fill_circle(x - 5, y - 3 + bounce, 2, Color.BLACK)
        self.display.fill_circle(x + 5, y - 3 + bounce, 2, Color.BLACK)
        
        # Mouth
        if self.pet["happiness"] > 50:
            # Happy mouth
            self.display.line(x - 3, y + 3 + bounce, x + 3, y + 3 + bounce, Color.BLACK)
        else:
            # Sad mouth
            self.display.line(x - 3, y + 5 + bounce, x + 3, y + 3 + bounce, Color.BLACK)
            
    def draw_child(self, x, y):
        """Draw child pet sprite"""
        # Walking animation
        walk = 3 if self.animation_frame % 4 < 2 else -3
        
        # Body
        self.display.fill_rect(x - 12, y - 10, 24, 20, Color.GREEN)
        
        # Head
        self.display.fill_circle(x, y - 15, 10, Color.GREEN)
        
        # Eyes
        self.display.fill_circle(x - 4, y - 15, 2, Color.BLACK)
        self.display.fill_circle(x + 4, y - 15, 2, Color.BLACK)
        
        # Legs
        self.display.fill_rect(x - 8 + walk, y + 10, 5, 8, Color.GREEN)
        self.display.fill_rect(x + 3 - walk, y + 10, 5, 8, Color.GREEN)
        
    def draw_teen(self, x, y):
        """Draw teen pet sprite"""
        # Body
        self.display.fill_rect(x - 15, y - 12, 30, 25, Color.MAGENTA)
        
        # Head
        self.display.fill_rect(x - 12, y - 25, 24, 15, Color.MAGENTA)
        
        # Eyes
        self.display.fill_rect(x - 8, y - 20, 4, 4, Color.BLACK)
        self.display.fill_rect(x + 4, y - 20, 4, 4, Color.BLACK)
        
        # Arms
        arm_swing = 5 if self.animation_frame % 2 == 0 else -5
        self.display.fill_rect(x - 20, y - 5 + arm_swing, 5, 10, Color.MAGENTA)
        self.display.fill_rect(x + 15, y - 5 - arm_swing, 5, 10, Color.MAGENTA)
        
        # Legs
        self.display.fill_rect(x - 10, y + 13, 8, 10, Color.MAGENTA)
        self.display.fill_rect(x + 2, y + 13, 8, 10, Color.MAGENTA)
        
    def draw_adult(self, x, y):
        """Draw adult pet sprite"""
        # Larger, more detailed sprite
        # Body
        self.display.fill_rect(x - 20, y - 15, 40, 30, Color.BLUE)
        
        # Head
        self.display.fill_circle(x, y - 25, 15, Color.BLUE)
        
        # Eyes
        self.display.fill_circle(x - 6, y - 25, 3, Color.WHITE)
        self.display.fill_circle(x + 6, y - 25, 3, Color.WHITE)
        self.display.fill_circle(x - 6, y - 25, 2, Color.BLACK)
        self.display.fill_circle(x + 6, y - 25, 2, Color.BLACK)
        
        # Mouth based on mood
        if self.pet["happiness"] > 70:
            # Big smile
            self.display.line(x - 8, y - 15, x - 5, y - 12, Color.BLACK)
            self.display.line(x - 5, y - 12, x + 5, y - 12, Color.BLACK)
            self.display.line(x + 5, y - 12, x + 8, y - 15, Color.BLACK)
        elif self.pet["happiness"] > 30:
            # Neutral
            self.display.line(x - 5, y - 13, x + 5, y - 13, Color.BLACK)
        else:
            # Sad
            self.display.line(x - 5, y - 10, x - 8, y - 13, Color.BLACK)
            self.display.line(x + 5, y - 10, x + 8, y - 13, Color.BLACK)
            
        # Arms and legs
        self.display.fill_rect(x - 25, y - 5, 8, 15, Color.BLUE)
        self.display.fill_rect(x + 17, y - 5, 8, 15, Color.BLUE)
        self.display.fill_rect(x - 15, y + 15, 10, 12, Color.BLUE)
        self.display.fill_rect(x + 5, y + 15, 10, 12, Color.BLUE)
        
    def draw_poop(self):
        """Draw poop indicators"""
        for i in range(self.pet["poop_count"]):
            x = 30 + i * 30
            y = 180
            # Simple poop shape
            self.display.fill_circle(x, y, 5, Color.ORANGE)
            self.display.fill_circle(x, y - 3, 4, Color.ORANGE)
            self.display.fill_circle(x, y - 5, 3, Color.ORANGE)
            
    def draw_sick_indicator(self):
        """Draw sick indicator"""
        # Skull icon
        x, y = 200, 50
        self.display.fill_circle(x, y, 6, Color.RED)
        self.display.fill_rect(x - 4, y + 3, 8, 4, Color.RED)
        # Eyes
        self.display.pixel(x - 2, y - 2, Color.BLACK)
        self.display.pixel(x + 2, y - 2, Color.BLACK)
        
    def draw_sleep_indicator(self):
        """Draw sleep Z's"""
        if self.animation_frame % 10 < 5:
            x, y = 150, 80
            self.display.text("Z", x, y, Color.BLUE)
            self.display.text("z", x + 10, y - 5, Color.BLUE)
            self.display.text("z", x + 20, y - 10, Color.BLUE)
            
    def draw_menu(self):
        """Draw action menu"""
        # Menu background
        self.display.fill_rect(20, 40, 200, 160, Color.DARK_GRAY)
        self.display.rect(20, 40, 200, 160, Color.WHITE)
        
        # Title
        self.display.text("ACTIONS", 85, 50, Color.YELLOW)
        
        # Menu options
        y = 70
        for i, option in enumerate(self.menu_options):
            if i == self.menu_selection:
                self.display.fill_rect(30, y - 2, 180, 20, Color.WHITE)
                self.display.text(option, 35, y, Color.BLACK)
            else:
                self.display.text(option, 35, y, Color.WHITE)
            y += 22
            
        # Instructions
        self.display.text("Joy:Nav A:Select B:Back", 30, 210, Color.GRAY)
        
    def handle_action(self, action):
        """Handle menu actions"""
        if action == "Feed":
            self.feeding_menu = True
            self.feeding_selection = 0
            self.draw_feeding_menu()
            
        elif action == "Play":
            if self.pet["energy"] > 20:
                self.pet["happiness"] = min(100, self.pet["happiness"] + 25)
                self.pet["energy"] = max(0, self.pet["energy"] - 15)
                self.show_action_animation("play")
            else:
                self.show_message("Too tired!")
                
        elif action == "Clean":
            self.pet["poop_count"] = 0
            self.pet["cleanliness"] = 100
            self.pet["happiness"] = min(100, self.pet["happiness"] + 5)
            self.show_action_animation("clean")
            
        elif action == "Medicine":
            if self.pet["is_sick"]:
                self.pet["is_sick"] = False
                self.pet["health"] = min(100, self.pet["health"] + 30)
                self.show_action_animation("medicine")
            else:
                self.show_message("Not sick!")
                
        elif action == "Sleep":
            self.pet["is_sleeping"] = not self.pet["is_sleeping"]
            if self.pet["is_sleeping"]:
                self.show_message("Sleeping...")
            else:
                self.show_message("Wake up!")
                
        elif action == "Stats":
            self.show_stats()
            
    def show_action_animation(self, action_type):
        """Show animation for actions"""
        self.display.fill(Color.BLACK)
        
        if action_type == "feed":
            # Food icon
            for i in range(3):
                self.display.fill_circle(120, 100, 10 + i * 5, Color.YELLOW)
                self.display.display()
                time.sleep_ms(200)
                
        elif action_type == "play":
            # Ball bouncing
            for i in range(4):
                y = 100 + abs(i - 2) * 20
                self.display.fill(Color.BLACK)
                self.display.fill_circle(120, y, 8, Color.RED)
                self.display.display()
                time.sleep_ms(150)
                
        elif action_type == "clean":
            # Sparkles
            for _ in range(5):
                self.display.fill(Color.BLACK)
                for _ in range(10):
                    x = random.randint(80, 160)
                    y = random.randint(80, 140)
                    self.display.pixel(x, y, Color.WHITE)
                self.display.display()
                time.sleep_ms(100)
                
        elif action_type == "medicine":
            # Cross symbol
            self.display.fill_rect(110, 90, 20, 40, Color.RED)
            self.display.fill_rect(100, 100, 40, 20, Color.RED)
            self.display.display()
            time.sleep_ms(500)
            
    def show_message(self, message):
        """Show temporary message"""
        x = (240 - len(message) * 8) // 2
        self.display.fill_rect(x - 10, 110, len(message) * 8 + 20, 20, Color.BLACK)
        self.display.rect(x - 10, 110, len(message) * 8 + 20, 20, Color.WHITE)
        self.display.text(message, x, 115, Color.WHITE)
        self.display.display()
        time.sleep_ms(1000)
        
    def show_stats(self):
        """Show detailed stats screen"""
        self.display.fill(Color.BLACK)
        
        # Title
        self.display.text("PET STATS", 75, 10, Color.CYAN)
        
        # Enhanced stats display
        stats = [
            (f"Name: {self.pet['name']}", Color.WHITE),
            (f"Age: {self.pet['age']}m Stage: {self.pet['stage']}", Color.YELLOW),
            (f"Health: {self.pet['health']}% Care: {self.pet['care_quality']}%", Color.RED),
            (f"Hunger: {self.pet['hunger']}% Weight: {self.pet['weight']}", Color.ORANGE),
            (f"Mood: {self.pet['mood']}% Happy: {self.pet['happiness']}%", Color.GREEN),
            (f"Energy: {self.pet['energy']}% Clean: {self.pet['cleanliness']}%", Color.BLUE),
            (f"Nutrition: {self.pet['nutrition']}%", Color.PURPLE),
            (f"Fed: {self.pet['last_fed']}t Play: {self.pet['last_played']}t", Color.GRAY),
        ]
        
        # Show illness if present
        if self.pet["is_sick"]:
            illness_text = f"Illness: {self.pet['illness_type'] or 'unknown'}"
            stats.append((illness_text, Color.RED))
            
        # Show weight status
        if self.pet["weight"] < 40:
            stats.append(("Status: Underweight", Color.ORANGE))
        elif self.pet["weight"] > 70:
            stats.append(("Status: Overweight", Color.ORANGE))
        else:
            stats.append(("Status: Healthy Weight", Color.GREEN))
        
        y = 30
        for stat, color in stats:
            self.display.text(stat, 10, y, color)
            y += 18
            
        self.display.text("Press B to go back", 50, 220, Color.GRAY)
        self.display.display()
        
        # Wait specifically for B button only
        while True:
            # Only check B button for exit
            if self.buttons.is_held('B'):
                break
            
            # Small delay to prevent CPU overload
            time.sleep_ms(100)
                
        # Debounce to prevent immediate re-entry
        time.sleep_ms(300)
            
    def apply_food_effects(self, food):
        """Apply food effects to pet stats"""
        self.pet["hunger"] = max(0, min(100, self.pet["hunger"] + food["hunger"]))
        self.pet["nutrition"] = max(0, min(100, self.pet["nutrition"] + food["nutrition"]))
        self.pet["weight"] = max(30, min(100, self.pet["weight"] + food["weight"]))
        self.pet["mood"] = max(0, min(100, self.pet["mood"] + food["mood"]))
        
        # Bonus happiness for well-fed pet
        if self.pet["hunger"] < 30:
            self.pet["happiness"] = min(100, self.pet["happiness"] + 5)
            
    def draw_feeding_menu(self):
        """Draw the feeding submenu"""
        self.display.fill(Color.BLACK)
        
        # Menu background
        self.display.fill_rect(15, 30, 210, 180, Color.DARK_GRAY)
        self.display.rect(15, 30, 210, 180, Color.WHITE)
        
        # Title
        self.display.text("CHOOSE FOOD", 75, 40, Color.YELLOW)
        
        # Food options with effects preview
        y = 60
        for i, meal in enumerate(self.meal_options):
            if i == self.feeding_selection:
                self.display.fill_rect(25, y - 2, 200, 32, Color.WHITE)
                text_color = Color.BLACK
            else:
                text_color = Color.WHITE
                
            # Food name
            self.display.text(meal["name"], 30, y, text_color)
            
            # Effects preview
            effects = f"H:{meal['hunger']:+} N:{meal['nutrition']:+} W:{meal['weight']:+}"
            self.display.text(effects, 30, y + 12, Color.GRAY if i != self.feeding_selection else Color.DARK_GRAY)
            y += 35
            
        # Instructions
        self.display.text("Joy:Nav A:Feed B:Back", 30, 195, Color.GRAY)
        self.display.display()
            
    def update(self):
        """Update XPet game"""
        # Update animation frame
        if time.ticks_diff(time.ticks_ms(), self.last_update) > 500:
            self.last_update = time.ticks_ms()
            self.animation_frame = (self.animation_frame + 1) % 60
            
            # Update pet stats
            self.update_stats()
            
            # Redraw if not in menu
            if not self.menu_open:
                self.draw_screen()
                
        if self.menu_open:
            # Handle menu navigation - use slow response for menus
            direction = self.joystick.get_direction_slow()
            
            if direction == 'UP':
                self.menu_selection = max(0, self.menu_selection - 1)
                self.draw_screen()
            elif direction == 'DOWN':
                self.menu_selection = min(len(self.menu_options) - 1, self.menu_selection + 1)
                self.draw_screen()
                
            # Select action
            if self.buttons.is_pressed('A'):
                action = self.menu_options[self.menu_selection]
                self.handle_action(action)
                self.menu_open = False
                self.draw_screen()
                time.sleep_ms(200)
                
            # Close menu
            if self.buttons.is_pressed('B'):
                self.menu_open = False
                self.draw_screen()
                time.sleep_ms(200)
        elif self.feeding_menu:
            # Handle feeding menu navigation
            direction = self.joystick.get_direction_slow()
            
            if direction == 'UP':
                self.feeding_selection = max(0, self.feeding_selection - 1)
                self.draw_feeding_menu()
            elif direction == 'DOWN':
                self.feeding_selection = min(len(self.meal_options) - 1, self.feeding_selection + 1)
                self.draw_feeding_menu()
                
            # Select food
            if self.buttons.is_pressed('A'):
                meal = self.meal_options[self.feeding_selection]
                self.pet["hunger"] = max(0, self.pet["hunger"] + meal["hunger"])
                self.pet["nutrition"] = max(0, min(100, self.pet["nutrition"] + meal["nutrition"]))
                self.pet["weight"] = max(30, min(100, self.pet["weight"] + meal["weight"]))
                self.pet["happiness"] = min(100, self.pet["happiness"] + 5)
                self.feeding_menu = False
                self.show_action_animation("feed")
                self.draw_screen()
                time.sleep_ms(200)
                
            # Close feeding menu
            if self.buttons.is_pressed('B'):
                self.feeding_menu = False
                self.draw_screen()
                time.sleep_ms(200)
        else:
            # In main view, no joystick navigation needed
            # Open menu
            if self.buttons.is_pressed('A'):
                self.menu_open = True
                self.menu_selection = 0
                self.draw_screen()
                time.sleep_ms(200)
                
        # Save periodically
        if time.ticks_ms() % 10000 == 0:
            self.save_pet()
            
        # Check for exit (only if not in any menu)
        if self.buttons.is_pressed('B') and not self.menu_open and not self.feeding_menu:
            return False
            
        return True
        
    def cleanup(self):
        """Cleanup when exiting app"""
        self.save_pet()