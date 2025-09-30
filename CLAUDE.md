# Pico Morti Project Documentation

## Project Overview
**Name:** Pico Morti
**Type:** MicroPython-based portable digital companion device
**License:** MIT License (Copyright 2025 3am-r)
**Platform:** Raspberry Pi Pico with LCD displays
**Primary Language:** MicroPython

This is a modular, multi-app ecosystem running on Raspberry Pi Pico hardware, featuring virtual pets, productivity tools, wellness apps, and games. The system provides a Tamagotchi-like experience with modern features including WiFi connectivity, battery monitoring, and multiple hardware configurations support.

## Hardware Support

### Currently Supported Devices
1. **Waveshare Pico-LCD-1.3** (TARGET_HARDWARE=WAVESHARE_1_3)
   - Display: 240x240 ST7789 LCD
   - Input: 5-way digital joystick + 4 buttons (A/B/X/Y)
   - Features: Battery monitoring, WiFi support
   - CPU: 125MHz Raspberry Pi Pico

2. **GeeekPi GPIO Module 3.5"** (TARGET_HARDWARE=GEEKPI_3_5)
   - Display: 320x480 ST7796 LCD
   - Input: Touch screen (GT911) + buttons
   - Features: Larger display, touch input
   - CPU: 125MHz Raspberry Pi Pico

### Hardware Configuration
- Configuration selected via `config.txt` file
- Hardware abstraction layer in `/devices/` directory
- Runtime hardware detection and configuration loading
- Pin mappings and display drivers are hardware-specific

## Project Structure

```
pico-morti/
├── main.py              # Main application entry point
├── boot.py              # Boot configuration and path setup
├── loader.py            # Personalized greeting/loading screen
├── app_info.py          # Centralized app registry and metadata
├── config.txt           # User configuration (WiFi, name, hardware)
├── LICENSE              # MIT License
│
├── apps/                # Productivity and wellness applications
│   ├── journal.py       # MicroJournal - digital diary
│   ├── tracker.py       # Activity tracker
│   ├── energy_dial.py   # Energy level monitoring
│   ├── gratitude.py     # Gratitude practice
│   ├── win_logger.py    # Achievement tracking
│   ├── worry_box.py     # Anxiety management tool
│   ├── med_tracker.py   # Medication tracking
│   ├── countdown.py     # Focus timer/countdown
│   ├── world_clock.py   # World clock display
│   ├── prayers.py       # Prayer times (Islamic)
│   ├── hijri_calendar.py # Hijri calendar
│   └── qibla.py         # Qibla compass
│
├── games/               # Entertainment applications
│   ├── pet.py           # XPet virtual pet game
│   ├── air_monkey.py    # Platform jumping game
│   ├── elemental.py     # Physics sandbox game
│   └── fidget_spinner.py # Fidget spinner simulation
│
├── themes/              # Launcher themes and implementations
│   ├── launcher.py      # LauncherManager orchestrator
│   ├── launcher_mindful.py  # Mindful launcher (intent-based)
│   ├── launcher_standard.py # Standard grid launcher
│   └── launcher_utils.py    # Shared launcher utilities
│
├── lib/                 # Core libraries and drivers
│   ├── st7789.py        # ST7789 display driver
│   ├── st7796.py        # ST7796 display driver
│   ├── gt911.py         # GT911 touch controller
│   ├── joystick.py      # Joystick input handler
│   ├── buttons.py       # Button input handler
│   ├── battery_monitor.py # Battery monitoring
│   ├── wifi_time.py     # WiFi time synchronization
│   └── dst_utils.py     # Daylight saving time utilities
│
├── devices/             # Hardware configurations
│   ├── hardware_runtime.py  # Runtime hardware detection
│   ├── waveshare_1_3.py    # Waveshare 1.3" config
│   └── geekpi_3_5.py       # GeeekPi 3.5" config
│
├── system/              # System utilities
│   ├── settings.py      # Settings app (WiFi, time, etc.)
│   └── time_sync.py     # Time synchronization
│
└── stores/              # Data storage (empty, for app data)
```

## Architecture & Design Patterns

### Core Architecture
- **Modular App System**: Each app is a self-contained class with standard interface
- **Hardware Abstraction Layer**: Device-agnostic design with hardware configs
- **Dynamic Module Loading**: Apps loaded on-demand to conserve memory
- **Event-Driven Input**: Centralized input handling through joystick/buttons/touch
- **State Management**: Apps maintain their own state with persistence

### App Interface Pattern
Every app implements:
```python
class AppName:
    def __init__(self, display, joystick, buttons):
        # Initialize app

    def init(self):
        # Called when app is opened

    def handle_input(self):
        # Process user input, return "exit" to close

    def draw_screen(self):
        # Render the display
```

### Display System
- Color class provides predefined colors (Color.RED, Color.BLUE, etc.)
- Display drivers support: fill(), fill_rect(), text(), pixel(), line()
- Hardware-specific resolution and rotation handling
- Backlight control where available

### Input System
- **Joystick**: 5-way digital (up/down/left/right/center)
- **Buttons**: A, B, X, Y with configurable actions
- **Touch**: Available on supported hardware (GeeekPi)
- **Sleep Button**: B button for sleep/wake functionality

## Key Features & Applications

### Wellness & Productivity Apps
- **Journal**: Digital diary with date-based entries
- **Activity Tracker**: Log and track daily activities
- **Energy Dial**: Monitor and log energy levels
- **Gratitude**: Practice gratitude with prompts
- **Win Logger**: Track daily achievements
- **Worry Box**: Anxiety management tool
- **Med Tracker**: Medication schedule tracking

### Games
- **XPet**: Full virtual pet with hunger, happiness, health stats
- **Air Monkey**: Platform jumping game
- **Elemental**: Physics-based sandbox
- **Fidget Spinner**: Interactive fidget simulation

### System Features
- **Mindful Launcher**: Intent-based app suggestions
- **Standard Launcher**: Traditional grid layout
- **Settings App**: WiFi config, time setup, system preferences
- **Battery Monitoring**: Real-time battery status
- **WiFi Time Sync**: Automatic time synchronization
- **Personalized Greeting**: Custom welcome message from config

## Configuration Files

### config.txt
```
# Device Configuration
TARGET_HARDWARE=WAVESHARE_1_3  # or GEEKPI_3_5

# Personal Configuration
FIRST_NAME=Amr
LAST_NAME=Salem

# WiFi Configuration
SSID=YourWiFiName
PASSWORD=YourWiFiPassword
TIMEZONE=-5  # UTC offset
```

### Data Storage
- Apps store data in text files (e.g., `xpet.dat`, `journal.txt`)
- JSON files for structured data (`theme.json`)
- Simple key-value format for most app data
- `/stores/` directory reserved for future use

## Development Guidelines

### Memory Management
- MicroPython has limited RAM (~264KB usable)
- Use `gc.collect()` frequently
- Lazy import modules when possible
- Clear unused variables explicitly
- Avoid loading all apps at startup

### Code Style
- Clean, self-documenting code
- Minimal comments (code should be readable)
- Standard Python naming conventions
- Error handling with try/except blocks
- Default values for all configurations

### Adding New Apps
1. Create new Python file in `/apps/` or `/games/`
2. Implement standard app interface (init, handle_input, draw_screen)
3. Add entry to `app_info.py` with metadata
4. Add to app_modules list in `main.py:123`

### Adding New Hardware
1. Create hardware config in `/devices/`
2. Define all pins, display config, capabilities
3. Add to SUPPORTED_HARDWARE in `hardware_runtime.py`
4. Update hardware detection logic

### Color Constants
Available via global Color class:
- Basic: BLACK, WHITE, RED, GREEN, BLUE, YELLOW, CYAN, MAGENTA
- Extended: ORANGE, PURPLE, PINK, LIME, TEAL, BROWN
- Shades: GRAY, LIGHT_GRAY, DARK_GRAY

## Testing & Deployment

### Deployment Process
1. Edit `config.txt` with target hardware and WiFi settings
2. Copy all files to Raspberry Pi Pico via Thonny or mpremote
3. Device auto-starts with boot.py → main.py

### Common Commands
- **Reset Device**: Press hardware reset button
- **Sleep/Wake**: Press B button
- **Exit App**: Press X button (typical)
- **Navigate**: Use joystick or touch

### Debugging
- Serial output available via USB
- Print statements visible in Thonny console
- Hardware validation on startup
- Error messages for missing configs

## Known Issues & Limitations

### Current Limitations
- No automated tests (manual testing only)
- Memory constraints limit concurrent apps
- No over-the-air updates
- Limited to 2MB flash storage
- No audio support currently

### Performance Notes
- CPU runs at 125MHz
- SPI display at 62.5MHz baudrate
- Smooth animations at ~30 FPS
- Garbage collection may cause brief pauses

## Future Development Areas

### Potential Enhancements
- [ ] Add more games (puzzle, racing, RPG)
- [ ] Implement app marketplace/store
- [ ] Add Bluetooth support for notifications
- [ ] Create desktop companion app
- [ ] Add data sync/backup functionality
- [ ] Implement themes customization
- [ ] Add multiplayer features via WiFi
- [ ] Create app development SDK
- [ ] Add voice/sound support (buzzer)
- [ ] Implement automatic OTA updates

### Code Quality Improvements
- [ ] Add unit testing framework
- [ ] Implement CI/CD pipeline
- [ ] Create documentation generator
- [ ] Add code linting rules
- [ ] Implement error reporting system
- [ ] Add performance profiling
- [ ] Create memory usage analyzer

## Important Notes for Development

1. **Memory is Critical**: Always monitor memory usage with `gc.mem_free()`
2. **Test on Hardware**: Simulator behavior may differ from actual device
3. **Pin Conflicts**: Verify pin assignments don't conflict with SPI/I2C
4. **Power Management**: Consider battery life in all features
5. **Display Updates**: Minimize full screen redraws for performance
6. **File I/O**: Keep file operations minimal and handle errors
7. **User Experience**: Maintain responsive UI (< 100ms input response)

## Git Workflow

### Current State
- Main branch active
- Recent commits show active development
- Features being added incrementally
- Config.txt has uncommitted changes

### Commit Convention
- Feature additions: "add [feature name]"
- Bug fixes: "fix [issue description]"
- Updates: "update [component name]"
- Text/UI: "[component] text issues and pixelation fix"

## Contact & Support

- **License Holder**: 3am-r
- **Year**: 2025
- **License Type**: MIT (open source)

---

*This document serves as the primary reference for understanding and developing the Pico Morti project. Keep it updated as the project evolves.*