"""
Mindful Launcher - Intent-driven application launcher
Revolutionary UX that captures user intent before showing apps
"""

import time
import sys
sys.path.append('..')  # Add parent directory to access app_info
from lib.st7789 import Color
from launcher_utils import LauncherUtils
from app_info import AppInfo

class MindfulLauncher:
    """Intent-driven launcher focusing on user goals rather than app grids"""
    
    def __init__(self, apps, display, joystick, buttons):
        self.apps = apps
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        # Launcher state
        self.launcher_mode = "intent"  # intent, flow, apps, browse
        self.selected_intent = 0
        self.selected_flow_step = 0
        self.current_intent = None
        self.current_app_index = 0
        
        # Load intents from centralized registry
        self.intents = AppInfo.INTENTS
        
        # Daily themes for anti-boredom
        self.daily_themes = [
            {"primary": Color.BLUE, "secondary": Color.CYAN, "accent": Color.WHITE},
            {"primary": Color.GREEN, "secondary": Color.YELLOW, "accent": Color.WHITE},
            {"primary": Color.PURPLE, "secondary": Color.MAGENTA, "accent": Color.WHITE},
            {"primary": Color.ORANGE, "secondary": Color.RED, "accent": Color.WHITE}
        ]
        
        # Get daily theme based on day
        day_of_year = time.localtime()[7]  # Day of year
        self.current_theme = self.daily_themes[day_of_year % len(self.daily_themes)]
        
    def init(self):
        """Initialize mindful launcher"""
        self.launcher_mode = "intent"
        self.selected_intent = 0
        self.current_app_index = 0
        self.draw_screen()
        
    def get_suggested_intent(self):
        """Get suggested intent based on time and usage patterns"""
        analytics = LauncherUtils.get_analytics()
        hour = time.localtime()[3]
        
        # Time-based suggestions
        if 6 <= hour < 12:  # Morning
            return 0  # Get Stuff Done
        elif 12 <= hour < 17:  # Afternoon
            return 1  # Check In
        elif 17 <= hour < 21:  # Evening
            return 2  # Take a Break
        else:  # Night
            return 3  # Spiritual
            
    def detect_user_context(self):
        """Detect user context for suggestions"""
        hour = time.localtime()[3]
        
        if 6 <= hour < 10:
            return "morning"
        elif 10 <= hour < 14:
            return "productive"
        elif 14 <= hour < 18:
            return "afternoon"
        elif 18 <= hour < 22:
            return "evening"
        else:
            return "night"
            
    def draw_screen(self):
        """Draw the mindful launcher interface"""
        self.display.fill(Color.BLACK)
        
        if self.launcher_mode == "intent":
            self.draw_intent_capture()
        elif self.launcher_mode == "flow":
            self.draw_flow_guidance()
        elif self.launcher_mode == "apps":
            self.draw_app_grid()
        elif self.launcher_mode == "browse":
            self.draw_browse_mode()
            
        self.display.display()
            
    def draw_intent_capture(self):
        """Draw the intent capture screen - modern, beautiful design"""
        suggested_intent = self.get_suggested_intent()
        context = self.detect_user_context()
        
        # Simple dark background (no flickering)
        self.display.fill(Color.BLACK)
        
        # Clean header - positioned based on screen height
        header_y = max(8, (self.display.height - 400) // 4)
        
        welcome_text = "How can I help you today?"
        welcome_x = (self.display.width - len(welcome_text) * 8) // 2
        self.display.text(welcome_text, welcome_x, header_y, Color.WHITE)
        
        # Time-based contextual subtitle
        time_greetings = {
            "morning": "Good morning!",
            "productive": "Ready to focus?", 
            "afternoon": "Afternoon check-in",
            "evening": "Evening wind-down",
            "night": "Peaceful night"
        }
        subtitle = time_greetings.get(context, "Let's be mindful")
        sub_x = (self.display.width - len(subtitle) * 8) // 2
        self.display.text(subtitle, sub_x, header_y + 17, Color.CYAN)
        
        # Modern card-based intent layout - center vertically
        content_height = len(self.intents) * 40  # approximate content height
        start_y = header_y + 50
        card_height = 35
        card_spacing = 5
        card_width = self.display.width - 30  # Leave 15px margin on each side
        
        for i, intent in enumerate(self.intents):
            y_pos = start_y + i * (card_height + card_spacing)
            
            # Card background and selection highlighting
            if i == self.selected_intent:
                # Selected intent - highlighted border
                self.display.rect(15, y_pos, card_width, card_height, intent["color"])
                text_color = intent["color"]
                desc_color = Color.WHITE
            elif i == suggested_intent:
                # Suggested intent - subtle border
                self.display.rect(15, y_pos, card_width, card_height, Color.rgb565(60, 70, 80))
                text_color = intent["color"]
                desc_color = Color.LIGHT_GRAY
            else:
                # Normal intent - no border
                text_color = Color.LIGHT_GRAY
                desc_color = Color.GRAY
            
            # Simple letter indicator instead of emoji
            letter = intent['name'][0]  # First letter of intent name
            self.display.text(letter, 25, y_pos + 8, text_color)
            
            # Intent name - bold and clear
            self.display.text(intent['name'], 45, y_pos + 5, text_color)
            
            # Description - smaller, elegant
            self.display.text(intent["description"], 45, y_pos + 18, desc_color)
            
            # Suggested indicator
            if i == suggested_intent and i != self.selected_intent:
                self.display.text("*", card_width - 25, y_pos + 8, Color.YELLOW)
        
        # Modern footer design
        footer_y = 200
        
        # Browse option
        browse_text = "Browse All Apps"
        browse_x = (self.display.width - len(browse_text) * 8) // 2
        self.display.text(browse_text, browse_x, footer_y + 5, Color.GRAY)
        
        # Instructions
        instructions = "Up/Down:Select  A:Go  Y:Browse"
        inst_x = (self.display.width - len(instructions) * 8) // 2
        self.display.text(instructions, inst_x, footer_y + 20, Color.DARK_GRAY)
        
    def draw_flow_guidance(self):
        """Draw flow guidance - modern coaching interface"""
        intent = self.current_intent
        flow_questions = intent["flow"]
        current_question = flow_questions[self.selected_flow_step]
        
        # Simple dark background (no flickering)
        self.display.fill(Color.BLACK)
        
        # Elegant header with intent context
        title = f"{intent['name']} Journey"
        title_x = (self.display.width - len(title) * 8) // 2
        self.display.text(title, title_x, 8, Color.WHITE)
        
        # Progress indicator
        progress_text = f"Step {self.selected_flow_step + 1} of {len(flow_questions)}"
        prog_x = (self.display.width - len(progress_text) * 8) // 2
        self.display.text(progress_text, prog_x, 25, Color.LIGHT_GRAY)
        
        # Progress bar
        bar_width = 180
        bar_x = (self.display.width - bar_width) // 2
        progress_pct = (self.selected_flow_step + 1) / len(flow_questions)
        self.display.fill_rect(bar_x, 35, bar_width, 6, Color.rgb565(40, 45, 55))
        self.display.fill_rect(bar_x, 35, int(bar_width * progress_pct), 6, Color.WHITE)
        
        # Question card with breathing space
        card_y = 60
        self.display.fill_rect(20, card_y, 200, 60, Color.rgb565(35, 40, 50))
        self.display.rect(20, card_y, 200, 60, Color.WHITE)
        
        # Question text with better formatting
        if len(current_question) > 25:
            # Split long questions into two lines
            words = current_question.split()
            mid = len(words) // 2
            line1 = " ".join(words[:mid])
            line2 = " ".join(words[mid:])
            
            line1_x = (self.display.width - len(line1) * 8) // 2
            line2_x = (self.display.width - len(line2) * 8) // 2
            self.display.text(line1, line1_x, card_y + 15, Color.WHITE)
            self.display.text(line2, line2_x, card_y + 30, Color.WHITE)
        else:
            question_x = (self.display.width - len(current_question) * 8) // 2
            self.display.text(current_question, question_x, card_y + 22, Color.WHITE)
        
        # Flow navigation dots - modern style
        dot_y = 130
        dot_start_x = (self.display.width - len(flow_questions) * 16) // 2
        for i, _ in enumerate(flow_questions):
            x = dot_start_x + i * 16
            if i == self.selected_flow_step:
                self.display.fill_rect(x, dot_y, 12, 8, Color.WHITE)
                self.display.fill_rect(x + 1, dot_y + 1, 10, 6, intent["color"])
            elif i < self.selected_flow_step:
                self.display.fill_rect(x, dot_y, 12, 8, Color.GREEN)
                self.display.text("X", x + 2, dot_y, Color.WHITE)
            else:
                self.display.rect(x, dot_y, 12, 8, Color.GRAY)
                
        # Motivational boost
        motivation_texts = [
            "Take your time",
            "You're doing great", 
            "Almost there",
            "Stay present"
        ]
        motivation = motivation_texts[self.selected_flow_step % len(motivation_texts)]
        mot_x = (self.display.width - len(motivation) * 8) // 2
        motivation_y = self.display.height // 2 + 20  # Position in middle area
        self.display.text(motivation, mot_x, motivation_y, Color.CYAN)
        
        # Modern instructions footer - positioned at bottom of screen
        footer_y = self.display.height - 25
        
        # App suggestions section - responsive positioning
        suggestions_y = footer_y - 70
        suggestions_width = self.display.width - 30
        self.display.fill_rect(15, suggestions_y, suggestions_width, 45, Color.rgb565(25, 30, 40))
        self.display.text("Recommended:", 25, suggestions_y + 5, Color.YELLOW)
        
        relevant_apps = LauncherUtils.get_intent_apps(self.apps, intent)[:3]
        
        for i, app in enumerate(relevant_apps):
            app_names, _ = LauncherUtils.get_app_display_info()
            name = app_names.get(app.__class__.__name__, app.__class__.__name__[:6])
            app_x = 25 + i * 65
            # App pill design
            pill_y = suggestions_y + 20
            self.display.fill_rect(app_x, pill_y, 60, 18, Color.rgb565(40, 45, 55))
            self.display.rect(app_x, pill_y, 60, 18, Color.GRAY)
            name_x = app_x + (60 - len(name) * 8) // 2
            self.display.text(name, name_x, pill_y + 5, Color.WHITE)
        
        # Draw footer
        self.display.fill_rect(0, footer_y, self.display.width, 20, Color.rgb565(15, 20, 30))
        instructions = "Left/Right:Navigate  A:Choose  B:Back"
        inst_x = (self.display.width - len(instructions) * 8) // 2
        self.display.text(instructions, inst_x, footer_y + 5, Color.GRAY)
        
    def draw_app_grid(self):
        """Draw filtered app grid for current intent"""
        # Get apps for current intent
        if hasattr(self, 'current_intent') and self.current_intent:
            apps_to_show = LauncherUtils.get_intent_apps(self.apps, self.current_intent)
            title = f"{self.current_intent['name']}"
        else:
            apps_to_show = self.apps
            title = "ALL APPS"
            
        # Use utility function to draw grid
        instruction_y = LauncherUtils.draw_app_grid(
            self.display, apps_to_show, self.current_app_index, title
        )
        
        # Instructions
        self.display.text("Joystick:Move A:Open", 45, instruction_y, Color.GRAY)
        self.display.text("B:Back", 95, instruction_y + 15, Color.GRAY)
        
    def draw_browse_mode(self):
        """Draw browse mode showing all apps in grid"""
        # Use utility function to draw all apps
        instruction_y = LauncherUtils.draw_app_grid(
            self.display, self.apps, self.current_app_index, "BROWSE ALL APPS"
        )
        
        # Instructions
        self.display.text("Joystick:Move A:Open", 45, instruction_y, Color.GRAY)
        self.display.text("B:Intents", 85, instruction_y + 15, Color.GRAY)
        
    def handle_input(self):
        """Handle input based on current mode"""
        # Update input devices
        self.buttons.update()
        
        # Delegate to mode-specific handlers first
        if self.launcher_mode == "intent":
            result = self.handle_intent_input()
        elif self.launcher_mode == "flow":
            result = self.handle_flow_input()
        elif self.launcher_mode == "apps":
            result = self.handle_app_grid_input()
        elif self.launcher_mode == "browse":
            result = self.handle_browse_input()
        else:
            result = "continue"
            
        return result
            
    def handle_intent_input(self):
        """Handle input during intent selection"""
        moved = False
        
        # Navigate intents
        if not self.joystick.up_pin.value() and not moved:
            self.selected_intent = (self.selected_intent - 1) % len(self.intents)
            moved = True
        elif not self.joystick.down_pin.value() and not moved:
            self.selected_intent = (self.selected_intent + 1) % len(self.intents)
            moved = True
            
        if moved:
            self.draw_screen()
            time.sleep_ms(150)
            
        # Select intent
        if self.buttons.is_pressed('A'):
            intent = self.intents[self.selected_intent]
            self.current_intent = intent
            self.selected_flow_step = 0
            self.launcher_mode = "flow"
            LauncherUtils.log_intent_selection(intent["name"])
            self.draw_screen()
            time.sleep_ms(200)
            
        # Quick access to browse mode
        if self.buttons.is_pressed('Y'):
            self.launcher_mode = "browse"
            self.current_app_index = 0  # Reset to first app
            self.draw_screen()
            time.sleep_ms(200)
            
        # Button B - Sleep mode with direct pin reading for immediate response
        if not self.buttons.buttons['B'].pin.value():  # Button pressed (inverted logic due to pull-up)
            # Small delay to avoid bouncing, but much shorter than normal debounce
            time.sleep_ms(50)
            if not self.buttons.buttons['B'].pin.value():  # Still pressed after delay
                return "sleep"
            
        return "continue"
            
    def handle_flow_input(self):
        """Handle input during flow guidance"""
        # Navigate flow steps
        if not self.joystick.left_pin.value():
            if self.selected_flow_step > 0:
                self.selected_flow_step -= 1
                self.draw_screen()
                time.sleep_ms(150)
        elif not self.joystick.right_pin.value():
            if self.selected_flow_step < len(self.current_intent["flow"]) - 1:
                self.selected_flow_step += 1
                self.draw_screen()
                time.sleep_ms(150)
                
        # Choose app for this intent
        if self.buttons.is_pressed('A'):
            self.launcher_mode = "apps"
            self.current_app_index = 0  # Reset to first app
            self.draw_screen()
            time.sleep_ms(200)
            
        # Go back to intent selection
        if self.buttons.is_pressed('B'):
            self.launcher_mode = "intent"
            self.draw_screen()
            time.sleep_ms(200)
            
        return "continue"
            
    def handle_app_grid_input(self):
        """Handle input in app grid (filtered by intent)"""
        # Get relevant apps for current intent
        if hasattr(self, 'current_intent') and self.current_intent:
            relevant_apps = LauncherUtils.get_intent_apps(self.apps, self.current_intent)
        else:
            relevant_apps = self.apps
            
        # Use utility function for navigation
        new_index, moved = LauncherUtils.handle_grid_navigation(
            self.joystick, relevant_apps, self.current_app_index
        )
        
        if moved:
            self.current_app_index = new_index
            self.draw_screen()
            time.sleep_ms(150)
            
        # Open selected app
        if self.buttons.is_pressed('A'):
            app = relevant_apps[self.current_app_index]
            LauncherUtils.log_app_usage(app.__class__.__name__)
            return ("launch_app", app)
            
        # Go back to flow
        if self.buttons.is_pressed('B'):
            self.launcher_mode = "flow"
            self.draw_screen()
            time.sleep_ms(200)
            
        return "continue"
            
    def handle_browse_input(self):
        """Handle input in browse mode (all apps)"""
        # Use utility function for navigation
        new_index, moved = LauncherUtils.handle_grid_navigation(
            self.joystick, self.apps, self.current_app_index
        )
        
        if moved:
            self.current_app_index = new_index
            self.draw_screen()
            time.sleep_ms(150)
            
        # Open app
        if self.buttons.is_pressed('A'):
            app = self.apps[self.current_app_index]
            LauncherUtils.log_app_usage(app.__class__.__name__)
            return ("launch_app", app)
            
        # Go back to intent mode  
        if self.buttons.is_pressed('B'):
            self.launcher_mode = "intent"
            self.draw_screen()
            time.sleep_ms(200)
            
        return "continue"