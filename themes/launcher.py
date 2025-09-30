"""
Launcher Orchestrator - Manages different launcher types
Dynamically loads and switches between launcher implementations
"""

from launcher_mindful import MindfulLauncher
from launcher_standard import StandardLauncher
from launcher_fidget import FidgetLauncher

class LauncherManager:
    """Manager class that handles different launcher types"""

    LAUNCHER_TYPES = {
        "mindful": MindfulLauncher,
        "standard": StandardLauncher,
        "fidget": FidgetLauncher
    }
    
    def __init__(self, apps, display, joystick, buttons, launcher_type="standard"):
        self.apps = apps
        self.display = display
        self.joystick = joystick
        self.buttons = buttons
        
        self.launcher_type = launcher_type
        self.current_launcher = None
        
        # Initialize the selected launcher
        self.switch_launcher(launcher_type)
        
    def switch_launcher(self, launcher_type):
        """Switch to a different launcher type"""
        if launcher_type not in self.LAUNCHER_TYPES:
            launcher_type = "standard"  # Default fallback
            
        launcher_class = self.LAUNCHER_TYPES[launcher_type]
        self.current_launcher = launcher_class(
            self.apps, self.display, self.joystick, self.buttons
        )
        self.launcher_type = launcher_type
        
    def init(self):
        """Initialize the current launcher"""
        if self.current_launcher:
            self.current_launcher.init()
            
    def handle_input(self):
        """Handle input through the current launcher"""
        if self.current_launcher:
            return self.current_launcher.handle_input()
        return "continue"
        
    def draw_screen(self):
        """Draw screen through the current launcher"""
        if self.current_launcher:
            self.current_launcher.draw_screen()
            
    def get_launcher_type(self):
        """Get current launcher type"""
        return self.launcher_type
        
    @staticmethod
    def get_available_launchers():
        """Get list of available launcher types"""
        return list(LauncherManager.LAUNCHER_TYPES.keys())
        
    @staticmethod
    def load_launcher_preference():
        """Load launcher preference from configuration"""
        try:
            import json
            with open("/stores/theme.json", "r") as f:
                theme_config = json.load(f)
                return theme_config.get("launcher", "standard")
        except:
            return "standard"  # Default
            
    @staticmethod
    def save_launcher_preference(launcher_type):
        """Save launcher preference to configuration"""
        try:
            import json
            # Load existing theme config
            try:
                with open("/stores/theme.json", "r") as f:
                    theme_config = json.load(f)
            except:
                theme_config = {}
                
            # Update launcher preference
            theme_config["launcher"] = launcher_type
            
            # Save back to file
            with open("/stores/theme.json", "w") as f:
                json.dump(theme_config, f)
                
            return True
        except:
            return False