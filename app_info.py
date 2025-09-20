"""
App Information Registry - Centralized app metadata
Single source of truth for all app information across launchers
"""

from lib.st7789 import Color

class AppInfo:
    """Centralized app information and metadata"""
    
    # Master app registry with all metadata
    APPS = {
        "MicroJournal": {
            "display_name": "Journal",
            "short_name": "Journal",
            "color": Color.GREEN,
            "category": "productivity",
            "intents": ["get_stuff_done", "check_in"],
            "description": "Write your thoughts",
            "icon": "📝"
        },
        "CountdownHub": {
            "display_name": "Countdown Timer",
            "short_name": "Counter",
            "color": Color.RED,
            "category": "productivity",
            "intents": ["get_stuff_done"],
            "description": "Focus timer",
            "icon": "⏱️"
        },
        "ActivityTracker": {
            "display_name": "Activity Tracker",
            "short_name": "Track",
            "color": Color.YELLOW,
            "category": "productivity",
            "intents": ["get_stuff_done", "check_in"],
            "description": "Track activities",
            "icon": "📊"
        },
        "EnergyDial": {
            "display_name": "Energy Dial",
            "short_name": "Energy",
            "color": Color.BLUE,
            "category": "wellness",
            "intents": ["get_stuff_done", "check_in"],
            "description": "Energy levels",
            "icon": "🔋"
        },
        "GratitudeProxy": {
            "display_name": "Gratitude",
            "short_name": "Thanks",
            "color": Color.ORANGE,
            "category": "wellness",
            "intents": ["check_in", "take_break", "spiritual"],
            "description": "Practice gratitude",
            "icon": "🙏"
        },
        "WinLogger": {
            "display_name": "Win Logger",
            "short_name": "Wins",
            "color": Color.YELLOW,
            "category": "wellness",
            "intents": ["check_in"],
            "description": "Log your wins",
            "icon": "🏆"
        },
        "WorryBox": {
            "display_name": "Worry Box",
            "short_name": "Worry",
            "color": Color.DARK_GRAY,
            "category": "wellness",
            "intents": ["check_in"],
            "description": "Release worries",
            "icon": "📦"
        },
        "XPet": {
            "display_name": "Virtual Pet",
            "short_name": "Pet",
            "color": Color.MAGENTA,
            "category": "games",
            "intents": ["take_break"],
            "description": "Care for pet",
            "icon": "🐾"
        },
        "AirMonkey": {
            "display_name": "Air Monkey",
            "short_name": "Monkey",
            "color": Color.ORANGE,
            "category": "games",
            "intents": ["take_break"],
            "description": "Jump & collect",
            "icon": "🐵"
        },
        "ElementalSandbox": {
            "display_name": "Elemental",
            "short_name": "Element",
            "color": Color.RED,
            "category": "games",
            "intents": ["take_break"],
            "description": "Physics sandbox",
            "icon": "🔥"
        },
        "FidgetSpinner": {
            "display_name": "Fidget Spinner",
            "short_name": "Fidget",
            "color": Color.CYAN,
            "category": "games",
            "intents": ["take_break"],
            "description": "Spin to relax",
            "icon": "🌀"
        },
        "Prayers": {
            "display_name": "Prayer Times",
            "short_name": "Prayer",
            "color": Color.GREEN,
            "category": "spiritual",
            "intents": ["spiritual"],
            "description": "Prayer schedule",
            "icon": "🕌"
        },
        "HijriCalendar": {
            "display_name": "Hijri Calendar",
            "short_name": "Hijri",
            "color": Color.YELLOW,
            "category": "spiritual",
            "intents": ["spiritual"],
            "description": "Islamic calendar",
            "icon": "📅"
        },
        "QiblaCompass": {
            "display_name": "Qibla Compass",
            "short_name": "Qibla",
            "color": Color.GREEN,
            "category": "spiritual",
            "intents": ["spiritual"],
            "description": "Find Qibla",
            "icon": "🧭"
        },
        "WorldClock": {
            "display_name": "World Clock",
            "short_name": "World",
            "color": Color.PURPLE,
            "category": "utilities",
            "intents": ["take_break"],
            "description": "Time zones",
            "icon": "🌍"
        },
        "Settings": {
            "display_name": "Settings",
            "short_name": "Setup",
            "color": Color.CYAN,
            "category": "system",
            "intents": ["get_stuff_done"],
            "description": "Customize device",
            "icon": "⚙️"
        },
        "TimeSyncApp": {
            "display_name": "Time Sync",
            "short_name": "Time",
            "color": Color.CYAN,
            "category": "system",
            "intents": [],
            "description": "Sync time",
            "icon": "🔄"
        },
        "MedTracker": {
            "display_name": "Med Tracker",
            "short_name": "Meds",
            "color": Color.ORANGE,
            "category": "wellness",
            "intents": ["check_in"],
            "description": "Track medications",
            "icon": "💊"
        }
    }
    
    # Intent definitions with apps
    INTENTS = [
        {
            "id": "get_stuff_done",
            "name": "Get Stuff Done",
            "emoji": "⚡",
            "description": "Focus & productivity",
            "color": Color.GREEN,
            "apps": ["journal", "countdown", "tracker", "energy_dial", "settings"],
            "flow": ["What's your main goal today?", "Set a timer?", "Track progress?"],
            "keywords": ["productive", "focus", "work", "goal"]
        },
        {
            "id": "check_in",
            "name": "Check In",
            "emoji": "💭",
            "description": "Self-care & reflection",
            "color": Color.BLUE,
            "apps": ["energy_dial", "journal", "gratitude", "worry_box", "win_logger", "med_tracker"],
            "flow": ["How's your energy?", "Journal thoughts?", "Practice gratitude?"],
            "keywords": ["self", "care", "reflection", "mood"]
        },
        {
            "id": "take_break",
            "name": "Take a Break",
            "emoji": "🎮",
            "description": "Fun & relaxation",
            "color": Color.ORANGE,
            "apps": ["pet", "air_monkey", "elemental", "fidget_spinner", "gratitude", "world_clock"],
            "flow": ["Play with pet?", "Physics sandbox?", "Quick game?", "Fidget spinner?", "Relax & breathe?"],
            "keywords": ["fun", "play", "relax", "break"]
        },
        {
            "id": "spiritual",
            "name": "Spiritual",
            "emoji": "🕌",
            "description": "Prayer & guidance",
            "color": Color.PURPLE,
            "apps": ["prayers", "hijri_calendar", "qibla", "gratitude"],
            "flow": ["Prayer time?", "Check calendar?", "Find qibla?"],
            "keywords": ["prayer", "spiritual", "guidance", "faith"]
        }
    ]
    
    # App categories for grouping
    CATEGORIES = {
        "productivity": {
            "name": "Productivity",
            "color": Color.GREEN,
            "apps": ["MicroJournal", "CountdownHub", "ActivityTracker"]
        },
        "wellness": {
            "name": "Wellness", 
            "color": Color.BLUE,
            "apps": ["EnergyDial", "GratitudeProxy", "WinLogger", "WorryBox", "MedTracker"]
        },
        "games": {
            "name": "Games",
            "color": Color.ORANGE,
            "apps": ["XPet", "AirMonkey", "ElementalSandbox", "FidgetSpinner"]
        },
        "spiritual": {
            "name": "Spiritual",
            "color": Color.PURPLE,
            "apps": ["Prayers", "HijriCalendar", "QiblaCompass"]
        },
        "utilities": {
            "name": "Utilities",
            "color": Color.GRAY,
            "apps": ["WorldClock"]
        },
        "system": {
            "name": "System",
            "color": Color.CYAN,
            "apps": ["Settings", "TimeSyncApp"]
        }
    }
    
    @classmethod
    def get_app_info(cls, class_name):
        """Get app info by class name"""
        return cls.APPS.get(class_name, {})
    
    @classmethod
    def get_display_name(cls, class_name):
        """Get display name for app"""
        app = cls.APPS.get(class_name, {})
        return app.get("display_name", class_name)
    
    @classmethod
    def get_short_name(cls, class_name):
        """Get short name for app (for grids)"""
        app = cls.APPS.get(class_name, {})
        return app.get("short_name", class_name[:8])
    
    @classmethod
    def get_color(cls, class_name):
        """Get color for app"""
        app = cls.APPS.get(class_name, {})
        return app.get("color", Color.WHITE)
    
    @classmethod
    def get_app_list_for_standard_launcher(cls):
        """Get ordered list of (name, color) tuples for standard launcher"""
        # Define the order we want apps to appear
        app_order = [
            "MicroJournal",
            "ActivityTracker", 
            "EnergyDial",
            "GratitudeProxy",
            "WinLogger",
            "WorryBox",
            "XPet",
            "AirMonkey",
            "ElementalSandbox",
            "FidgetSpinner",
            "Prayers",
            "HijriCalendar",
            "QiblaCompass",
            "CountdownHub",
            "WorldClock",
            "MedTracker",
            "TimeSyncApp",
            "Settings"
        ]
        
        result = []
        for class_name in app_order:
            if class_name in cls.APPS:
                app = cls.APPS[class_name]
                result.append((app["short_name"], app["color"]))
        return result
    
    @classmethod
    def get_apps_for_intent(cls, intent_id):
        """Get apps for a specific intent"""
        for intent in cls.INTENTS:
            if intent["id"] == intent_id:
                return intent.get("apps", [])
        return []
    
    @classmethod
    def get_intent_by_index(cls, index):
        """Get intent by index"""
        if 0 <= index < len(cls.INTENTS):
            return cls.INTENTS[index]
        return None
    
    @classmethod
    def get_apps_in_category(cls, category):
        """Get all apps in a category"""
        cat = cls.CATEGORIES.get(category, {})
        return cat.get("apps", [])