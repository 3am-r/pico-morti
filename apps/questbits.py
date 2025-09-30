"""
QuestBits - Micro-Motivation Engine
Tiny quests and routines for 30-90 second wins
Features progress tracking, streaks, and Morti celebrations
"""

import time
import json
import random
from lib.st7789 import Color

class QuestBits:
    def __init__(self, display, joystick, buttons):
        """Initialize QuestBits app"""
        self.display = display
        self.joystick = joystick
        self.buttons = buttons

        # UI state
        self.current_screen = "home"  # home, quest_active, completed, stats
        self.selected_pack = 0
        self.current_quest = None
        self.quest_start_time = 0
        self.morti_animation_frame = 0
        self.celebration_timer = 0

        # Quest content packs
        self.quest_packs = {
            "Focus": {
                "color": Color.BLUE,
                "icon": "◆",
                "quests": [
                    "Take 3 deep breaths with eyes closed",
                    "Write down your top priority for today",
                    "Clear your desk of distractions",
                    "Set a 25-minute focused work timer",
                    "List 3 things you're grateful for",
                    "Stretch your neck and shoulders",
                    "Drink a full glass of water mindfully",
                    "Close unnecessary browser tabs",
                    "Write tomorrow's most important task"
                ]
            },
            "Movement": {
                "color": Color.GREEN,
                "icon": "▲",
                "quests": [
                    "Do 10 jumping jacks",
                    "Walk around the block",
                    "Stretch your arms above your head 5 times",
                    "Do wall push-ups for 30 seconds",
                    "March in place for 1 minute",
                    "Touch your toes 10 times",
                    "Take the stairs instead of elevator",
                    "Do 5 squats",
                    "Walk to the furthest water fountain"
                ]
            },
            "Mindfulness": {
                "color": Color.PURPLE,
                "icon": "◉",
                "quests": [
                    "Notice 5 things you can see right now",
                    "Listen for 30 seconds without judgment",
                    "Feel the temperature of the air on your skin",
                    "Count backwards from 20 to 1",
                    "Name 3 sounds you hear",
                    "Focus on your breathing for 1 minute",
                    "Feel your feet touching the ground",
                    "Notice one thing you haven't seen before",
                    "Appreciate something beautiful nearby"
                ]
            },
            "Social": {
                "color": Color.YELLOW,
                "icon": "♦",
                "quests": [
                    "Send a quick 'thinking of you' message",
                    "Compliment someone genuinely",
                    "Ask someone about their day",
                    "Say thank you to someone who helped you",
                    "Smile at the next person you see",
                    "Hold the door for someone",
                    "Share something positive on social media",
                    "Call a friend or family member",
                    "Write a positive review for a local business"
                ]
            }
        }

        # Load progress data
        self.load_progress()

    def load_progress(self):
        """Load progress data from storage"""
        try:
            with open('/stores/questbits.json', 'r') as f:
                data = json.load(f)
                self.total_completed = data.get('total_completed', 0)
                self.daily_streak = data.get('daily_streak', 0)
                self.last_quest_date = data.get('last_quest_date', '')
                self.pack_stats = data.get('pack_stats', {pack: 0 for pack in self.quest_packs.keys()})
                self.daily_completed = data.get('daily_completed', 0)
                self.last_daily_reset = data.get('last_daily_reset', '')
        except:
            # Initialize default values
            self.total_completed = 0
            self.daily_streak = 0
            self.last_quest_date = ''
            self.pack_stats = {pack: 0 for pack in self.quest_packs.keys()}
            self.daily_completed = 0
            self.last_daily_reset = ''

    def save_progress(self):
        """Save progress data to storage"""
        try:
            data = {
                'total_completed': self.total_completed,
                'daily_streak': self.daily_streak,
                'last_quest_date': self.last_quest_date,
                'pack_stats': self.pack_stats,
                'daily_completed': self.daily_completed,
                'last_daily_reset': self.last_daily_reset
            }
            with open('/stores/questbits.json', 'w') as f:
                json.dump(data, f)
        except:
            pass  # Fail silently

    def check_daily_reset(self):
        """Check if we need to reset daily counters"""
        current_date = time.localtime()[:3]  # (year, month, day)
        current_date_str = f"{current_date[0]}-{current_date[1]:02d}-{current_date[2]:02d}"

        if self.last_daily_reset != current_date_str:
            self.daily_completed = 0
            self.last_daily_reset = current_date_str
            self.save_progress()

    def get_random_quest(self, pack_name):
        """Get a random quest from the specified pack"""
        quests = self.quest_packs[pack_name]["quests"]
        return random.choice(quests)

    def start_quest(self, pack_name):
        """Start a new quest from the specified pack"""
        self.current_quest = {
            "pack": pack_name,
            "text": self.get_random_quest(pack_name),
            "start_time": time.ticks_ms()
        }
        self.current_screen = "quest_active"

    def complete_quest(self):
        """Mark current quest as completed and update stats"""
        if not self.current_quest:
            return

        # Update statistics
        self.total_completed += 1
        self.daily_completed += 1
        pack_name = self.current_quest["pack"]
        self.pack_stats[pack_name] = self.pack_stats.get(pack_name, 0) + 1

        # Update streak
        current_date = time.localtime()[:3]
        current_date_str = f"{current_date[0]}-{current_date[1]:02d}-{current_date[2]:02d}"

        if self.last_quest_date == current_date_str:
            # Same day, don't update streak
            pass
        elif self.last_quest_date == "":
            # First quest ever
            self.daily_streak = 1
        else:
            # Check if it's consecutive day
            # For simplicity, just increment (would need proper date math for real consecutive checking)
            self.daily_streak += 1

        self.last_quest_date = current_date_str

        # Save progress
        self.save_progress()

        # Switch to celebration screen
        self.current_screen = "completed"
        self.celebration_timer = time.ticks_ms()
        self.morti_animation_frame = 0

    def init(self):
        """Initialize app"""
        self.check_daily_reset()
        self.draw_screen()

    def draw_home_screen(self):
        """Draw the home screen with quest pack selection"""
        self.display.fill(Color.BLACK)

        # Title
        self.display.text("QUESTBITS", 80, 5, Color.CYAN)

        # Stats line
        stats_text = f"Total:{self.total_completed} Today:{self.daily_completed} Streak:{self.daily_streak}"
        self.display.text(stats_text, 5, 20, Color.GRAY)

        # Quest packs
        pack_names = list(self.quest_packs.keys())
        y_start = 45

        for i, pack_name in enumerate(pack_names):
            pack_info = self.quest_packs[pack_name]
            y = y_start + i * 35

            # Highlight selected pack
            if i == self.selected_pack:
                self.display.fill_rect(5, y - 5, 230, 30, Color.WHITE)
                text_color = Color.BLACK
                bg_color = Color.WHITE
            else:
                text_color = pack_info["color"]
                bg_color = Color.BLACK

            # Pack icon and name
            icon_text = f"{pack_info['icon']} {pack_name}"
            self.display.text(icon_text, 10, y, text_color)

            # Pack completion count
            completed = self.pack_stats.get(pack_name, 0)
            count_text = f"({completed})"
            count_x = 180
            self.display.text(count_text, count_x, y, text_color)

            # Quick preview of quest type
            preview = pack_name.lower()[:6]
            self.display.text(preview, 10, y + 12, Color.GRAY if i != self.selected_pack else Color.DARK_GRAY)

        # Instructions
        self.display.text("↑↓:Select A:Start B:Stats", 20, 220, Color.GRAY)

    def draw_quest_active_screen(self):
        """Draw the active quest screen"""
        self.display.fill(Color.BLACK)

        if not self.current_quest:
            return

        pack_name = self.current_quest["pack"]
        pack_info = self.quest_packs[pack_name]

        # Title with pack indicator
        title = f"{pack_info['icon']} {pack_name} Quest"
        title_x = (240 - len(title) * 8) // 2
        self.display.text(title, title_x, 5, pack_info["color"])

        # Quest text (word wrap)
        quest_text = self.current_quest["text"]
        self.draw_wrapped_text(quest_text, 10, 30, 220, Color.WHITE)

        # Timer
        elapsed = (time.ticks_ms() - self.current_quest["start_time"]) // 1000
        timer_text = f"Time: {elapsed}s"
        self.display.text(timer_text, 10, 140, Color.YELLOW)

        # Morti encouragement
        encouragements = [
            "You've got this! ◕‿◕",
            "Tiny steps, big wins! ◕ᴗ◕",
            "Focus energy building... ◕◡◕",
            "Small quest, huge impact! ◕‿◕"
        ]
        encouragement = encouragements[elapsed % len(encouragements)]
        self.display.text(encouragement, 10, 160, Color.GREEN)

        # Instructions
        self.display.text("A:Complete B:Cancel", 50, 220, Color.GRAY)

    def draw_completed_screen(self):
        """Draw quest completion celebration screen"""
        self.display.fill(Color.BLACK)

        # Animated celebration header
        if time.ticks_ms() - self.celebration_timer < 3000:  # 3 second celebration
            frame = (time.ticks_ms() // 200) % 4
            celebrations = ["★ QUEST COMPLETE! ★", "✧ QUEST COMPLETE! ✧", "◆ QUEST COMPLETE! ◆", "♦ QUEST COMPLETE! ♦"]
            celebration_text = celebrations[frame]
            text_x = (240 - len(celebration_text) * 8) // 2
            self.display.text(celebration_text, text_x, 20, Color.YELLOW)

            # Morti celebration animation
            morti_frames = ["◕‿◕", "◕ᴗ◕", "◕◡◕", "◕‿◕", "ᕕ( ◕‿◕ )ᕗ"]
            morti_frame = morti_frames[frame % len(morti_frames)]
            morti_text = f"Morti says: {morti_frame}"
            morti_x = (240 - len(morti_text) * 8) // 2
            self.display.text(morti_text, morti_x, 50, Color.GREEN)
        else:
            # Static completion message
            self.display.text("★ QUEST COMPLETE! ★", 40, 20, Color.YELLOW)
            self.display.text("Morti says: ◕‿◕", 60, 50, Color.GREEN)

        # Rewards earned
        self.display.text("Rewards Earned:", 10, 80, Color.CYAN)
        self.display.text("• +1 Total Quests", 15, 95, Color.WHITE)
        self.display.text("• +1 Daily Progress", 15, 110, Color.WHITE)

        if self.current_quest:
            pack_name = self.current_quest["pack"]
            reward_text = f"• +1 {pack_name} XP"
            self.display.text(reward_text, 15, 125, Color.WHITE)

        # Updated stats
        self.display.text("Updated Stats:", 10, 150, Color.CYAN)
        stats_text = f"Total: {self.total_completed}"
        self.display.text(stats_text, 15, 165, Color.WHITE)
        daily_text = f"Today: {self.daily_completed}"
        self.display.text(daily_text, 15, 180, Color.WHITE)
        streak_text = f"Streak: {self.daily_streak}"
        self.display.text(streak_text, 15, 195, Color.WHITE)

        # Instructions
        self.display.text("A:Another Quest B:Home", 40, 220, Color.GRAY)

    def draw_stats_screen(self):
        """Draw detailed statistics screen"""
        self.display.fill(Color.BLACK)

        # Title
        self.display.text("QUEST STATISTICS", 50, 5, Color.CYAN)

        # Overall stats
        self.display.text("Overall Progress:", 10, 25, Color.YELLOW)
        self.display.text(f"Total Completed: {self.total_completed}", 15, 40, Color.WHITE)
        self.display.text(f"Daily Streak: {self.daily_streak}", 15, 55, Color.WHITE)
        self.display.text(f"Today: {self.daily_completed}", 15, 70, Color.WHITE)

        # Pack breakdown
        self.display.text("Pack Breakdown:", 10, 95, Color.YELLOW)
        y = 110
        for pack_name, count in self.pack_stats.items():
            pack_color = self.quest_packs[pack_name]["color"]
            icon = self.quest_packs[pack_name]["icon"]
            text = f"{icon} {pack_name}: {count}"
            self.display.text(text, 15, y, pack_color)
            y += 15

        # Instructions
        self.display.text("B:Back to Home", 60, 220, Color.GRAY)

    def draw_wrapped_text(self, text, x, y, max_width, color):
        """Draw text with word wrapping"""
        words = text.split(' ')
        line = ''
        line_y = y
        char_width = 8  # Approximate character width

        for word in words:
            test_line = line + word + ' '
            if len(test_line) * char_width <= max_width:
                line = test_line
            else:
                if line:
                    self.display.text(line.strip(), x, line_y, color)
                    line_y += 15
                line = word + ' '

        if line:
            self.display.text(line.strip(), x, line_y, color)

    def draw_screen(self):
        """Draw the current screen"""
        if self.current_screen == "home":
            self.draw_home_screen()
        elif self.current_screen == "quest_active":
            self.draw_quest_active_screen()
        elif self.current_screen == "completed":
            self.draw_completed_screen()
        elif self.current_screen == "stats":
            self.draw_stats_screen()

        self.display.display()

    def update(self):
        """Update QuestBits app"""
        self.buttons.update()

        if self.current_screen == "home":
            # Navigation
            if self.buttons.is_pressed('UP'):
                self.selected_pack = (self.selected_pack - 1) % len(self.quest_packs)
                self.draw_screen()
                time.sleep_ms(150)

            elif self.buttons.is_pressed('DOWN'):
                self.selected_pack = (self.selected_pack + 1) % len(self.quest_packs)
                self.draw_screen()
                time.sleep_ms(150)

            elif self.buttons.is_pressed('A'):
                # Start quest from selected pack
                pack_names = list(self.quest_packs.keys())
                selected_pack_name = pack_names[self.selected_pack]
                self.start_quest(selected_pack_name)
                self.draw_screen()
                time.sleep_ms(200)

            elif self.buttons.is_pressed('B'):
                # Show stats
                self.current_screen = "stats"
                self.draw_screen()
                time.sleep_ms(200)

        elif self.current_screen == "quest_active":
            if self.buttons.is_pressed('A'):
                # Complete quest
                self.complete_quest()
                self.draw_screen()
                time.sleep_ms(200)

            elif self.buttons.is_pressed('B'):
                # Cancel quest
                self.current_quest = None
                self.current_screen = "home"
                self.draw_screen()
                time.sleep_ms(200)

        elif self.current_screen == "completed":
            if self.buttons.is_pressed('A'):
                # Start another quest (same pack)
                if self.current_quest:
                    pack_name = self.current_quest["pack"]
                    self.start_quest(pack_name)
                    self.draw_screen()
                    time.sleep_ms(200)

            elif self.buttons.is_pressed('B'):
                # Return to home
                self.current_quest = None
                self.current_screen = "home"
                self.draw_screen()
                time.sleep_ms(200)

        elif self.current_screen == "stats":
            if self.buttons.is_pressed('B'):
                # Return to home
                self.current_screen = "home"
                self.draw_screen()
                time.sleep_ms(200)

        # Auto-refresh active quest screen every second
        if self.current_screen == "quest_active":
            if time.ticks_ms() % 1000 < 50:  # Refresh roughly every second
                self.draw_screen()

        return True

    def cleanup(self):
        """Cleanup when exiting app"""
        self.save_progress()