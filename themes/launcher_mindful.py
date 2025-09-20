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
        self.launcher_mode = "intent"  # intent, flow, recommendations, apps, browse
        self.selected_intent = 0
        self.selected_flow_step = 0
        self.current_intent = None
        self.current_app_index = 0
        
        # Check-in system state
        self.selected_check_in_option = 0
        self.check_in_responses = {}
        self.selected_app = 0
        
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
        
        # Reset check-in flow state
        self.selected_flow_step = 0
        self.selected_check_in_option = 0
        self.check_in_responses = {}
        self.selected_app = 0
        
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
        elif self.launcher_mode == "recommendations":
            self.draw_app_recommendations()
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
        
        
        # Instructions
        instructions = "U/D:Select  A:Go  Y:Browse"
        inst_x = (self.display.width - len(instructions) * 8) // 2
        self.display.text(instructions, inst_x, footer_y + 20, Color.DARK_GRAY)
        
    def draw_flow_guidance(self):
        """Draw contextual mindful check-in with direct app suggestions"""
        self.display.fill(Color.BLACK)
        
        # Get check-in questions and responses
        check_in_data = self.get_check_in_flow()
        current_step = check_in_data["steps"][self.selected_flow_step]
        
        # Header
        header_y = max(8, (self.display.height - 400) // 4)
        title = "Mindful Check-in"
        title_x = (self.display.width - len(title) * 8) // 2
        self.display.text(title, title_x, header_y, Color.WHITE)
        
        # Current question
        question = current_step["question"]
        question_x = (self.display.width - len(question) * 8) // 2
        self.display.text(question, question_x, header_y + 25, Color.CYAN)
        
        # Response options with selection
        options_start_y = header_y + 60
        for i, option in enumerate(current_step["options"]):
            y_pos = options_start_y + i * 35
            option_text = option["text"]
            
            # Highlight selected option
            if i == self.selected_check_in_option:
                # Selected - highlighted card
                card_width = self.display.width - 30
                self.display.fill_rect(15, y_pos, card_width, 30, Color.rgb565(60, 70, 80))
                self.display.rect(15, y_pos, card_width, 30, Color.WHITE)
                text_color = Color.WHITE
                desc_color = Color.LIGHT_GRAY
            else:
                # Normal option
                text_color = Color.LIGHT_GRAY
                desc_color = Color.GRAY
            
            # Option text
            self.display.text(option_text, 25, y_pos + 5, text_color)
            
            # Brief description
            if "desc" in option:
                self.display.text(option["desc"], 25, y_pos + 18, desc_color)
        
        # Instructions at bottom
        footer_y = self.display.height - 25
        instructions = "U/D:Select  A:Continue  B:Back"
        inst_x = (self.display.width - len(instructions) * 8) // 2
        self.display.text(instructions, inst_x, footer_y, Color.GRAY)
    
    def get_check_in_flow(self):
        """Get contextual check-in questions and app suggestions"""
        return {
            "steps": [
                {
                    "question": "How do you feel right now?",
                    "options": [
                        {"text": "Stressed/Overwhelmed", "desc": "Need to process & calm", "state": "stressed"},
                        {"text": "Calm & Focused", "desc": "Ready for productive work", "state": "focused"},
                        {"text": "Energized & Motivated", "desc": "Want to create & achieve", "state": "energized"},
                        {"text": "Tired/Low Energy", "desc": "Need gentle reflection", "state": "tired"}
                    ]
                },
                {
                    "question": "What's your main intention?",
                    "options": [
                        {"text": "Process thoughts", "desc": "Clear mental clutter", "intent": "process"},
                        {"text": "Plan & organize", "desc": "Structure my day/goals", "intent": "plan"},
                        {"text": "Reflect & grow", "desc": "Learn from experiences", "intent": "reflect"},
                        {"text": "Celebrate & appreciate", "desc": "Acknowledge wins", "intent": "celebrate"}
                    ]
                }
            ]
        }
    
    def get_suggested_apps_for_state(self, user_state, user_intent):
        """Get app suggestions based on user's emotional state and intention"""
        # Define app suggestions based on state + intent combinations
        suggestions = {
            ("stressed", "process"): ["WorryBox", "MicroJournal", "GratitudeProxy"],
            ("stressed", "plan"): ["EnergyDial", "ActivityTracker", "MicroJournal"],
            ("stressed", "reflect"): ["WorryBox", "MicroJournal", "GratitudeProxy"],
            ("stressed", "celebrate"): ["GratitudeProxy", "WinLogger", "MicroJournal"],
            
            ("focused", "process"): ["MicroJournal", "ActivityTracker", "EnergyDial"],
            ("focused", "plan"): ["ActivityTracker", "EnergyDial", "CountdownHub"],
            ("focused", "reflect"): ["MicroJournal", "GratitudeProxy", "ActivityTracker"],
            ("focused", "celebrate"): ["WinLogger", "GratitudeProxy", "MicroJournal"],
            
            ("energized", "process"): ["ActivityTracker", "EnergyDial", "MicroJournal"],
            ("energized", "plan"): ["ActivityTracker", "CountdownHub", "EnergyDial"],
            ("energized", "reflect"): ["MicroJournal", "WinLogger", "GratitudeProxy"],
            ("energized", "celebrate"): ["WinLogger", "GratitudeProxy", "ActivityTracker"],
            
            ("tired", "process"): ["GratitudeProxy", "WorryBox", "MicroJournal"],
            ("tired", "plan"): ["EnergyDial", "GratitudeProxy", "MicroJournal"],
            ("tired", "reflect"): ["GratitudeProxy", "MicroJournal", "WorryBox"],
            ("tired", "celebrate"): ["GratitudeProxy", "WinLogger", "MicroJournal"]
        }
        
        # Get app class names for this state/intent combo
        app_names = suggestions.get((user_state, user_intent), ["MicroJournal", "GratitudeProxy", "EnergyDial"])
        
        # Find actual app instances
        suggested_apps = []
        for app_name in app_names:
            for app in self.apps:
                if app.__class__.__name__ == app_name:
                    suggested_apps.append(app)
                    break
        
        return suggested_apps[:3]  # Return top 3 suggestions
    
    def draw_app_recommendations(self):
        """Draw final app recommendations with direct launch capability"""
        self.display.fill(Color.BLACK)
        
        # Get user's responses (stored during flow)
        user_responses = getattr(self, 'check_in_responses', {})
        user_state = user_responses.get('feeling', 'focused')
        user_intent = user_responses.get('intention', 'reflect')
        
        # Header
        header_y = max(8, (self.display.height - 400) // 4)
        title = "Recommended for you"
        title_x = (self.display.width - len(title) * 8) // 2
        self.display.text(title, title_x, header_y, Color.WHITE)
        
        # Contextual message based on state
        context_messages = {
            "stressed": "Let's process and find calm",
            "focused": "Perfect time to be productive", 
            "energized": "Channel that energy positively",
            "tired": "Gentle tools for reflection"
        }
        
        context_msg = context_messages.get(user_state, "Mindful tools for you")
        context_x = (self.display.width - len(context_msg) * 8) // 2
        self.display.text(context_msg, context_x, header_y + 20, Color.CYAN)
        
        # Get suggested apps
        suggested_apps = self.get_suggested_apps_for_state(user_state, user_intent)
        
        # Display apps as selectable cards
        cards_start_y = header_y + 60
        for i, app in enumerate(suggested_apps):
            y_pos = cards_start_y + i * 45
            
            # Get app display name
            app_names, _ = LauncherUtils.get_app_display_info()
            app_name = app_names.get(app.__class__.__name__, app.__class__.__name__)
            
            # Selection highlighting
            if i == self.selected_app:
                # Selected app - highlighted
                card_width = self.display.width - 30
                self.display.fill_rect(15, y_pos, card_width, 40, Color.rgb565(60, 70, 80))
                self.display.rect(15, y_pos, card_width, 40, Color.WHITE)
                text_color = Color.WHITE
                desc_color = Color.LIGHT_GRAY
            else:
                # Normal app
                text_color = Color.LIGHT_GRAY
                desc_color = Color.GRAY
            
            # App name
            self.display.text(app_name, 25, y_pos + 8, text_color)
            
            # Brief description of why it's suggested
            descriptions = {
                "WorryBox": "Process concerns mindfully",
                "MicroJournal": "Reflect through writing", 
                "GratitudeProxy": "Cultivate appreciation",
                "EnergyDial": "Check in with yourself",
                "ActivityTracker": "Plan and track progress",
                "WinLogger": "Celebrate your wins",
                "CountdownHub": "Focus with time structure"
            }
            
            desc = descriptions.get(app.__class__.__name__, "Mindful digital tool")
            self.display.text(desc, 25, y_pos + 22, desc_color)
        
        # Instructions
        footer_y = self.display.height - 25
        instructions = "U/D:Select  A:Launch  B:Back  Y:Browse All"
        inst_x = (self.display.width - len(instructions) * 8) // 2
        self.display.text(instructions, inst_x, footer_y, Color.GRAY)
        
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
        elif self.launcher_mode == "recommendations":
            result = self.handle_recommendations_input()
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
        """Handle input during mindful check-in flow"""
        check_in_data = self.get_check_in_flow()
        current_step = check_in_data["steps"][self.selected_flow_step]
        
        # Navigate response options
        if not self.joystick.up_pin.value():
            self.selected_check_in_option = max(0, self.selected_check_in_option - 1)
            self.draw_screen()
            time.sleep_ms(150)
        elif not self.joystick.down_pin.value():
            self.selected_check_in_option = min(len(current_step["options"]) - 1, self.selected_check_in_option + 1)
            self.draw_screen()
            time.sleep_ms(150)
                
        # Select response and continue
        if self.buttons.is_pressed('A'):
            # Store the user's response
            selected_option = current_step["options"][self.selected_check_in_option]
            
            if self.selected_flow_step == 0:  # First question (feeling)
                self.check_in_responses['feeling'] = selected_option.get('state')
            elif self.selected_flow_step == 1:  # Second question (intention)
                self.check_in_responses['intention'] = selected_option.get('intent')
            
            # Move to next step or finish
            if self.selected_flow_step < len(check_in_data["steps"]) - 1:
                # Next question
                self.selected_flow_step += 1
                self.selected_check_in_option = 0  # Reset selection
                self.draw_screen()
            else:
                # Flow complete, show recommendations
                self.launcher_mode = "recommendations"
                self.selected_app = 0  # Reset app selection
                self.draw_screen()
            
            time.sleep_ms(200)
            
        # Go back to intent selection or previous step
        if self.buttons.is_pressed('B'):
            if self.selected_flow_step > 0:
                # Go back to previous question
                self.selected_flow_step -= 1
                self.selected_check_in_option = 0
                self.draw_screen()
            else:
                # Go back to intent selection
                self.launcher_mode = "intent"
                self.draw_screen()
            time.sleep_ms(200)
            
        return "continue"
    
    def handle_recommendations_input(self):
        """Handle input in recommendations screen"""
        # Get suggested apps based on user responses
        user_responses = getattr(self, 'check_in_responses', {})
        user_state = user_responses.get('feeling', 'focused')
        user_intent = user_responses.get('intention', 'reflect')
        suggested_apps = self.get_suggested_apps_for_state(user_state, user_intent)
        
        # Navigate app recommendations
        if not self.joystick.up_pin.value():
            self.selected_app = max(0, self.selected_app - 1)
            self.draw_screen()
            time.sleep_ms(150)
        elif not self.joystick.down_pin.value():
            self.selected_app = min(len(suggested_apps) - 1, self.selected_app + 1)
            self.draw_screen()
            time.sleep_ms(150)
        
        # Launch selected app directly
        if self.buttons.is_pressed('A') and suggested_apps:
            selected_app = suggested_apps[self.selected_app]
            return ("launch_app", selected_app)
        
        # Browse all apps (fallback to traditional app grid)
        if self.buttons.is_pressed('Y'):
            self.launcher_mode = "browse"
            self.current_app_index = 0
            self.draw_screen()
            time.sleep_ms(200)
        
        # Go back to flow
        if self.buttons.is_pressed('B'):
            self.launcher_mode = "flow"
            self.selected_flow_step = len(self.get_check_in_flow()["steps"]) - 1  # Go to last step
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