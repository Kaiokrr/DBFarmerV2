"""
DBFarmer v2.0 - Dragon Ball Legends Story Farmer
Modernized for BlueStacks 5 based on the original DBFarmer by LUXTACO
Compatible: BlueStacks 5, Windows 10/11, Python 3.8+
"""

import os
import sys
import json
import time
import logging
import datetime
import threading
import tkinter as tk
from tkinter import ttk
import pyautogui
import cv2
import numpy as np
from PIL import ImageGrab

# ─────────────────────────────────────────────────────────────
#  DEFAULT CONFIGURATION
# ─────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "window_name": "BlueStacks App Player",   # BlueStacks 5 window title
    "image_folder": "images",                  # Reference images folder
    "confidence": 0.75,                        # Detection threshold (0.0 to 1.0)
    "loop_delay": 1.0,                         # Delay between each check (sec)
    "click_delay": 0.5,                        # Delay after a click (sec)
    "anti_stuck_delay": 60.0,                  # Anti-stuck interval (sec)
    "max_tries": 15,                           # Max attempts per button
    "combat_timeout": 600,                     # Max combat duration (sec) = 10 min
    "overlay_enabled": True,                   # Show overlay
    "log_level": "INFO",
    "skip_position": {
        "x_pct": 0.82,   # X position as % of window width (0.82 = 82% = right side)
        "y_pct": 0.05    # Y position as % of window height (0.05 = 5% = top)
    },
    "team_slots": [
        {"x": 845, "y": 631},
        {"x": 945, "y": 631},
        {"x": 1045, "y": 631},
        {"x": 845, "y": 731},
        {"x": 945, "y": 731},
        {"x": 1045, "y": 731}
    ]
}

CONFIG_PATH = "config.json"
LOG_DIR = "logs"

# Image filenames expected in the images/ folder
# Capture these buttons from your game and save them with these exact names
IMAGE_FILES = {
    # ── INITIAL SETUP ──────────────────────────────────────────
    "StoryButton":      "story.png",          # "Story" button on the home screen
    "ContinueButton":   "continue.png",       # "Continue" button (resume progress)

    # ── COMBAT SELECTION ───────────────────────────────────────
    "MissionObject":    "mission.png",        # The level/stage to click
    "DemoCheckmark":    "demo.png",           # "Play Demo" UNCHECKED (correct state → launch combat)
    "DemoChecked":      "demo_checked.png",   # "Play Demo" CHECKED yellow (wrong state → click to uncheck)
    "StartBattleButton":"startbattle.png",    # "Start Battle" button
    "YesButton":        "yes.png",            # "Yes" / confirmation button
    "NoButton":         "no.png",             # "No" button (to avoid)

    # ── TEAM SELECTION ─────────────────────────────────────────
    "LegendsPointer":   "legendspointer.png", # Reference point — signals team selection screen is ready
    "ReadyButton":      "ready.png",          # "Ready" button

    # ── DURING / END OF COMBAT ─────────────────────────────────
    "FinishedPointer":  "finishedpointer.png",# End of combat indicator
    "TapArrow":         "tap.png",            # "Tap to continue" arrow after combat (centered bottom)
    "TapArrow2":        "tap2.png",           # TAP icon variant (bottom right corner)
    "OkBattleButton":   "okbattle.png",       # "OK" button on results screen
    "SkipButton":       "skip.png",           # "Skip" button (skip a cinematic)
    "RematchButton":    "rematch.png",        # Rematch button (visible only on defeat screen)
    "QuitBattleButton": "quitbattle.png",     # Quit Battle button (to exit a stuck combat)
    "InCombatIndicator":"incombat.png",       # AUTO ON button — visible only during combat

    # ── CINEMATIC LEVELS (story slides without combat) ─────────
    "StorySlide":       "storyslide.png",     # Indicator that we're on a story slide

    # ── NAVIGATION / ANTI-STUCK ────────────────────────────────
    "BackButton":       "back.png",           # In-game back button
    "HomeButton":       "home.png",           # In-game home button (returns to home screen)
}

# Priority for anti-stuck (higher number = higher priority)
PRIORITY_LIST = {
    "SkipButton":        15,
    "ArrowObject":       13,
    "TapArrow":          11,
    "TapArrow2":         11,
    "QuitBattleButton":  10,
    "NoButton":          10,
    "YesButton":          9,
    "StartBattleButton":  8,
    "DemoCheckmark":      7,
    "OkBattleButton":     6,
    "ReadyButton":        5,
    "StoryButton":        3,
    "ContinueButton":     1,
    "MissionObject":      0,
}

# Team slots are now configured directly in config.json under "team_slots"

# ─────────────────────────────────────────────────────────────
#  LOGGING
# ─────────────────────────────────────────────────────────────

os.makedirs(LOG_DIR, exist_ok=True)
log_file = os.path.join(LOG_DIR, f"{datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.log")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ]
)
logger = logging.getLogger("DBFarmer")

# ─────────────────────────────────────────────────────────────
#  CONFIG MANAGEMENT
# ─────────────────────────────────────────────────────────────

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
            # Merge with defaults (for new keys)
            for key, val in DEFAULT_CONFIG.items():
                config.setdefault(key, val)
            logger.info(f"Config loaded from {CONFIG_PATH}")
            return config
        except Exception as e:
            logger.warning(f"Config read error: {e} -> using default config")
    # Create default config
    with open(CONFIG_PATH, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)
    logger.info(f"Default config created at {CONFIG_PATH}")
    return DEFAULT_CONFIG.copy()

# ─────────────────────────────────────────────────────────────
#  TKINTER OVERLAY (real-time display)
# ─────────────────────────────────────────────────────────────

class Overlay:
    def __init__(self, get_data_callback):
        self.get_data = get_data_callback
        self.root = tk.Tk()
        self.root.title("DBFarmer v2")
        self.root.overrideredirect(True)         # No Windows title bar
        self.root.geometry("+5+5")
        self.root.wm_attributes("-topmost", True)
        self.root.configure(bg="#0d0d0d")
        self.root.wm_attributes("-alpha", 0.92)

        # Custom title bar
        bar = tk.Frame(self.root, bg="#1a0a2e", pady=3)
        bar.pack(fill="x")
        tk.Label(bar, text="⚡ DBFarmer v2 | BlueStacks 5 ⚡",
                 fg="#b060ff", bg="#1a0a2e",
                 font=("Consolas", 10, "bold")).pack(side="left", padx=8)
        tk.Label(bar, text="✕", fg="#ff5555", bg="#1a0a2e",
                 font=("Consolas", 11, "bold"), cursor="hand2").pack(side="right", padx=6)

        # Stats
        self.status_var = tk.StringVar(value="⏳ Starting...")
        self.loop_var   = tk.StringVar(value="Loops: 0")
        self.stuck_var  = tk.StringVar(value="Anti-stuck: OK")
        self.action_var = tk.StringVar(value="Action: Waiting")

        for var, color in [
            (self.status_var, "#ffffff"),
            (self.loop_var,   "#b060ff"),
            (self.stuck_var,  "#60ff90"),
            (self.action_var, "#ffcc00"),
        ]:
            tk.Label(self.root, textvariable=var,
                     fg=color, bg="#0d0d0d",
                     font=("Consolas", 9), anchor="w").pack(fill="x", padx=8, pady=1)

        # Console log
        self.console = tk.Text(self.root, height=10, width=60,
                               bg="#111111", fg="#b060ff",
                               font=("Consolas", 8), borderwidth=0)
        self.console.pack(fill="both", padx=4, pady=4)

        # Drag
        bar.bind("<ButtonPress-1>", self._start_drag)
        bar.bind("<B1-Motion>", self._drag)

        self.root.after(500, self._update)

    def _start_drag(self, e):
        self._drag_x = e.x
        self._drag_y = e.y

    def _drag(self, e):
        x = self.root.winfo_x() + e.x - self._drag_x
        y = self.root.winfo_y() + e.y - self._drag_y
        self.root.geometry(f"+{x}+{y}")

    def _update(self):
        try:
            data = self.get_data()
            self.status_var.set(f"🟢 Status: {data.get('status', '...')}")
            self.loop_var.set(f"🔁 Loops: {data.get('loops', 0)} | Completed: {data.get('completed', 0)}")
            self.stuck_var.set(f"🛡 Anti-stuck: {data.get('stuck_fixed', 0)} fix(s)")
            self.action_var.set(f"⚡ Action: {data.get('action', '...')}")

            # Show last log lines
            try:
                with open(log_file, "r", encoding="utf-8") as lf:
                    lines = lf.readlines()[-12:]
                self.console.delete("1.0", "end")
                self.console.insert("end", "".join(lines))
                self.console.see("end")
            except:
                pass
        except:
            pass
        self.root.after(500, self._update)

    def run(self):
        self.root.mainloop()

# ─────────────────────────────────────────────────────────────
#  MAIN FARMER CLASS
# ─────────────────────────────────────────────────────────────

class DBFarmer:

    def __init__(self):
        self.config = load_config()
        self.image_folder = self.config["image_folder"]
        self.confidence   = self.config["confidence"]
        self.loop_delay   = self.config["loop_delay"]
        self.click_delay  = self.config["click_delay"]
        self.max_tries    = self.config["max_tries"]

        # Stats
        self.stats = {
            "status":      "Initializing",
            "loops":       0,
            "completed":   0,
            "stuck_fixed": 0,
            "action":      "Starting",
        }

        # Flag to pause anti-stuck during combat and results screen
        self.in_combat = False

        # Flag set by anti-stuck to request a recovery
        # Main loop detects it and handles recovery properly
        self.recovery_requested = False

        os.makedirs(self.image_folder, exist_ok=True)

        # Load images
        self.images = {}
        self._load_images()

        # Find BlueStacks window
        self.window = self._find_window()

        # Start anti-stuck thread
        self._stuck_thread = threading.Thread(target=self._anti_stuck_loop, daemon=True)
        self._stuck_thread.start()

        # Overlay
        if self.config["overlay_enabled"]:
            overlay_thread = threading.Thread(
                target=lambda: Overlay(lambda: self.stats).run(),
                daemon=True
            )
            overlay_thread.start()

        logger.info("DBFarmer initialized successfully")

    # ── Image loading ───────────────────────────────────────────

    def _load_images(self):
        missing = []
        for key, filename in IMAGE_FILES.items():
            path = os.path.join(self.image_folder, filename)
            if os.path.exists(path):
                img = cv2.imread(path)
                if img is not None:
                    self.images[key] = img
                    logger.debug(f"Image loaded: {key} ({filename})")
                else:
                    logger.warning(f"Could not read image: {filename}")
                    missing.append(key)
            else:
                missing.append(key)

        if missing:
            logger.warning(f"Missing images ({len(missing)}): {missing}")
            logger.warning(f"Put these images in the '{self.image_folder}/' folder")
            logger.warning("Use the capture tool: python capture.py")
        else:
            logger.info(f"All images loaded ({len(self.images)})")

    # ── BlueStacks window management ───────────────────────────

    def _find_window(self):
        name = self.config["window_name"]
        logger.info(f"Looking for window: '{name}'")
        for _ in range(30):
            wins = pyautogui.getWindowsWithTitle(name)
            if wins:
                win = wins[0]
                logger.info(f"Window found: {win.title} | Pos: ({win.left},{win.top}) Size: {win.width}x{win.height}")
                return win
            time.sleep(0.5)
        logger.error(f"Window '{name}' not found! Make sure BlueStacks is open.")
        print(f"\n[ERROR] BlueStacks window not found.")
        print(f"  -> Make sure BlueStacks 5 is open.")
        print(f"  -> Check 'window_name' in config.json")
        print(f"  -> Currently open windows:")
        for w in pyautogui.getAllWindows():
            if w.title:
                print(f"     '{w.title}'")
        sys.exit(1)

    def _get_window_region(self):
        """Returns (left, top, width, height) of the BlueStacks window."""
        try:
            wins = pyautogui.getWindowsWithTitle(self.config["window_name"])
            if wins:
                w = wins[0]
                return (w.left, w.top, w.width, w.height)
        except:
            pass
        return None

    # ── Screenshot ─────────────────────────────────────────────

    def _screenshot(self):
        """Captures only the BlueStacks window."""
        region = self._get_window_region()
        if region is None:
            return None
        try:
            l, t, w, h = region
            img = ImageGrab.grab(bbox=(l, t, l+w, t+h))
            return np.array(img)
        except Exception as e:
            logger.error(f"Screenshot error: {e}")
            return None

    # ── Image detection ────────────────────────────────────────

    def _find(self, key: str) -> tuple | None:
        """
        Searches for an image in the BlueStacks window.
        Returns ABSOLUTE (x, y) on screen, or None if not found.
        """
        if key not in self.images:
            return None

        screenshot = self._screenshot()
        if screenshot is None:
            return None

        template = self.images[key]
        screen_bgr = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)

        sh, sw = screen_bgr.shape[:2]
        th, tw = template.shape[:2]
        if th > sh or tw > sw:
            logger.warning(f"Template {key} larger than screen, resizing...")
            template = cv2.resize(template, (min(tw, sw-1), min(th, sh-1)))

        result = cv2.matchTemplate(screen_bgr, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= self.confidence:
            rel_x = max_loc[0] + tw // 2
            rel_y = max_loc[1] + th // 2
            region = self._get_window_region()
            if region:
                abs_x = region[0] + rel_x
                abs_y = region[1] + rel_y
                logger.debug(f"Found [{key}] confidence={max_val:.2f} pos=({abs_x},{abs_y})")
                return (abs_x, abs_y)

        return None

    def _find_with_confidence(self, key: str, confidence: float) -> tuple | None:
        """Same as _find but with a custom confidence threshold."""
        if key not in self.images:
            return None
        screenshot = self._screenshot()
        if screenshot is None:
            return None
        template = self.images[key]
        screen_bgr = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        sh, sw = screen_bgr.shape[:2]
        th, tw = template.shape[:2]
        if th > sh or tw > sw:
            template = cv2.resize(template, (min(tw, sw-1), min(th, sh-1)))
        result = cv2.matchTemplate(screen_bgr, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)
        if max_val >= confidence:
            rel_x = max_loc[0] + tw // 2
            rel_y = max_loc[1] + th // 2
            region = self._get_window_region()
            if region:
                abs_x = region[0] + rel_x
                abs_y = region[1] + rel_y
                logger.debug(f"Found [{key}] confidence={max_val:.2f} (threshold={confidence}) pos=({abs_x},{abs_y})")
                return (abs_x, abs_y)
        return None

    def _find_with_score(self, key: str, screenshot_bgr) -> tuple[float, tuple | None]:
        """
        Searches for an image in an already captured screenshot.
        Returns (score, coords) — coords can be None if below threshold.
        Used to compare multiple images on the same screenshot.
        """
        if key not in self.images:
            return 0.0, None

        template = self.images[key]
        sh, sw = screenshot_bgr.shape[:2]
        th, tw = template.shape[:2]
        if th > sh or tw > sw:
            template = cv2.resize(template, (min(tw, sw-1), min(th, sh-1)))
            th, tw = template.shape[:2]

        result = cv2.matchTemplate(screenshot_bgr, template, cv2.TM_CCOEFF_NORMED)
        _, max_val, _, max_loc = cv2.minMaxLoc(result)

        if max_val >= self.confidence:
            region = self._get_window_region()
            if region:
                abs_x = region[0] + max_loc[0] + tw // 2
                abs_y = region[1] + max_loc[1] + th // 2
                return max_val, (abs_x, abs_y)

        return max_val, None

    def _find_best(self, *keys: str) -> tuple[str | None, tuple | None]:
        """
        Compares multiple images on the SAME screenshot and returns
        the one with the highest score.
        Avoids false positives between similar images (e.g. demo vs demo_checked).
        Returns (winning_key, coords) or (None, None) if none found.
        """
        screenshot = self._screenshot()
        if screenshot is None:
            return None, None

        screen_bgr = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)

        best_key    = None
        best_score  = -1.0
        best_coords = None

        for key in keys:
            score, coords = self._find_with_score(key, screen_bgr)
            logger.debug(f"  _find_best [{key}] score={score:.3f}")
            if score > best_score:
                best_score  = score
                best_key    = key
                best_coords = coords

        if best_score >= self.confidence:
            logger.debug(f"→ Winner: [{best_key}] score={best_score:.3f}")
            return best_key, best_coords

        return None, None

    # ── Click ──────────────────────────────────────────────────

    def _click(self, x: int, y: int):
        """Clicks at an absolute position on screen."""
        pyautogui.click(x, y)
        time.sleep(self.click_delay)
        logger.debug(f"Click at ({x}, {y})")

    def _click_skip(self) -> bool:
        """
        Clicks the Skip button using fixed coordinates.
        Two modes in config.json → skip_position:

        Mode "absolute" (recommended):
            {"mode": "absolute", "x": 851, "y": 49}
            Absolute coordinates on your screen — measure once.

        Mode "relative" (if you change resolution):
            {"mode": "relative", "x_pct": 0.82, "y_pct": 0.06}
            Percentage of the GAME ZONE (not the entire Windows window).
        """
        pos = self.config.get("skip_position", {"mode": "absolute", "x": 851, "y": 49})
        mode = pos.get("mode", "absolute")

        if mode == "absolute":
            x = pos["x"]
            y = pos["y"]
        else:
            region = self._get_window_region()
            if region is None:
                logger.warning("_click_skip: window not found")
                return False
            l, t, w, h = region
            x = int(l + w * pos.get("x_pct", 0.82))
            y = int(t + h * pos.get("y_pct", 0.06))

        logger.info(f"Skip click at ({x}, {y}) [mode={mode}]")
        pyautogui.click(x, y)
        time.sleep(self.click_delay)
        return True

    # ── Wait and click ─────────────────────────────────────────

    def _wait_and_click(self, key: str, timeout: float = 30, delay: float = None) -> bool:
        """
        Waits for an element to appear then clicks it.
        If timeout exceeded → recovery_requested = True (anti-stuck takes over).
        Returns True if clicked, False if timeout.
        """
        delay = delay or self.loop_delay
        self._set_action(f"Waiting: {key}")
        start = time.time()
        while True:
            coords = self._find(key)
            if coords:
                self._set_action(f"Click: {key}")
                self._click(*coords)
                return True
            if time.time() - start > timeout:
                logger.warning(f"Timeout ({timeout}s) waiting for [{key}] → recovery requested")
                self.recovery_requested = True
                return False
            time.sleep(delay)

    def _try_click(self, key: str, tries: int = None, delay: float = None) -> bool:
        """
        Tries to click an element with a limited number of attempts.
        Returns True if clicked, False if failed after all attempts.
        """
        tries = tries or self.max_tries
        delay = delay or self.loop_delay
        for i in range(tries):
            coords = self._find(key)
            if coords:
                self._click(*coords)
                return True
            time.sleep(delay)
        logger.warning(f"[{key}] not found after {tries} attempts")
        return False

    # ── Team selection ─────────────────────────────────────────

    def _select_team(self):
        """
        Waits for LegendsPointer to confirm team selection screen is ready,
        then clicks all 6 slots using absolute coordinates from config.json.
        Edit 'team_slots' in config.json to calibrate positions for your screen.
        """
        self._set_action("Waiting for team selection screen...")
        start = time.time()
        while True:
            if self._find("LegendsPointer"):
                break
            if time.time() - start > 30:
                logger.warning("LegendsPointer not found after 30s → skipping wait")
                break
            time.sleep(0.5)

        self._set_action("Team selection")
        slots = self.config.get("team_slots", [])
        if not slots:
            logger.warning("No team_slots in config.json — skipping team selection")
            return True

        time.sleep(0.3)
        for i, slot in enumerate(slots):
            self._click(slot["x"], slot["y"])
            logger.info(f"Char {i+1} clicked: ({slot['x']}, {slot['y']})")
            if i == 2:
                time.sleep(0.5)

        # Wait for UI to settle before ReadyButton
        time.sleep(1.0)
        return True

    # ── Stats / status ─────────────────────────────────────────

    def _set_action(self, action: str):
        self.stats["action"] = action
        logger.info(action)

    def _set_status(self, status: str):
        self.stats["status"] = status

    # ── INITIAL SETUP ──────────────────────────────────────────

    def setup(self):
        """
        Startup sequence: Story → Continue
        Each step checks recovery_requested — if blocked, anti-stuck handles it.
        """
        logger.info("="*55)
        logger.info("  INITIAL SETUP")
        logger.info("="*55)
        self._set_status("Setup")

        print("\n[DBFarmer] Waiting for Story button...")

        # 1. Story button — timeout 60s then recovery
        self._set_action("Waiting: StoryButton")
        start = time.time()
        while not self._find("StoryButton"):
            if self.recovery_requested:
                logger.warning("Setup stuck on StoryButton → recovery")
                return
            if time.time() - start > 60:
                logger.warning("Timeout StoryButton (60s) → recovery requested")
                self.recovery_requested = True
                return
            time.sleep(0.5)
        self._click(*self._find("StoryButton"))
        logger.info("✓ Story selected")

        # 2. Continue button — timeout 60s then recovery
        self._set_action("Waiting: ContinueButton")
        start = time.time()
        while not self._find("ContinueButton"):
            if self.recovery_requested:
                logger.warning("Setup stuck on ContinueButton → recovery")
                return
            if time.time() - start > 60:
                logger.warning("Timeout ContinueButton (60s) → recovery requested")
                self.recovery_requested = True
                return
            time.sleep(0.5)
        self._click(*self._find("ContinueButton"))
        logger.info("✓ Continue clicked")

        # 3. Check if recovery was requested after ContinueButton
        if self.recovery_requested:
            logger.warning("Setup stuck after ContinueButton → recovery")
            return

        # 4. Yes confirmation (if needed)
        time.sleep(0.5)
        self._try_click("YesButton", tries=5, delay=0.4)
        if self.recovery_requested:
            logger.warning("Setup stuck on YesButton → recovery")
            return

        logger.info("✓ Setup done - main loop taking over")

    # ── LEVEL TYPE DETECTION ───────────────────────────────────

    def _detect_level_type(self, timeout: float = 45.0) -> str:
        """
        Detects the level type by searching in parallel:
          - StartBattleButton → COMBAT
          - StorySlide        → CINEMATIC
          - SkipButton        → CINEMATIC (always present on slides)

        First signal found wins immediately.
        """
        self._set_action("Detecting level type...")
        logger.info("Detecting level type...")

        start = time.time()
        while time.time() - start < timeout:
            if self._find("StartBattleButton"):
                logger.info("→ COMBAT (StartBattleButton found)")
                return "combat"
            if self._find("StorySlide"):
                logger.info("→ CINEMATIC (StorySlide found)")
                return "story"
            if self._find("SkipButton"):
                logger.info("→ CINEMATIC (SkipButton found)")
                return "story"
            time.sleep(0.3)

        logger.warning(f"Level type not detected after {timeout}s → recovery requested")
        self.recovery_requested = True
        return "unknown"

    # ── CINEMATIC LEVEL HANDLING ───────────────────────────────

    def _handle_story_level(self):
        """
        Cinematic level: Skip → Yes (confirm skip).
        """
        logger.info("─── Handling CINEMATIC level ───")
        self._set_status("Cinematic")

        # Step 1: Skip the cinematic
        self._set_action("Skip cinematic")
        self._click_skip()
        logger.info("✓ Skip clicked (fixed coordinates)")

        # Step 2: One Yes to confirm skip
        time.sleep(0.5)
        if not self._wait_and_click("YesButton", timeout=15):
            return False
        logger.info("✓ Skip confirmed")

        self.stats["story_levels"] = self.stats.get("story_levels", 0) + 1
        return True

    # ── PLAY DEMO CHECKBOX VERIFICATION ───────────────────────

    def _ensure_demo_unchecked(self, timeout: float = 20.0) -> bool:
        """
        Compares demo.png (unchecked) and demo_checked.png (checked) on the SAME screenshot.
        The one with the highest score = actual state.
        Avoids false positives between similar images.
        Returns True if demo is unchecked (correct state), False if timeout.
        """
        start = time.time()
        while time.time() - start < timeout:
            winner, coords = self._find_best("DemoCheckmark", "DemoChecked")

            if winner == "DemoCheckmark":
                logger.info("✓ Play Demo unchecked (correct state)")
                return True

            elif winner == "DemoChecked":
                logger.info(f"Play Demo checked — clicking to uncheck at {coords}")
                self._click(*coords)
                time.sleep(0.8)
                # Re-verify with _find_best
                winner2, _ = self._find_best("DemoCheckmark", "DemoChecked")
                if winner2 == "DemoCheckmark":
                    logger.info("✓ Play Demo unchecked after click")
                    return True
                logger.debug(f"Still state [{winner2}], retrying...")

            else:
                # None found → screen not loaded yet
                time.sleep(0.4)

        logger.warning(f"Play Demo not confirmed unchecked after {timeout}s → recovery requested")
        self.recovery_requested = True
        return False

    # ── FLUSH PENDING TAPS ─────────────────────────────────────

    def _flush_taps(self, max_taps: int = 10):
        """
        Clicks TapArrow in a loop until it disappears.
        Double check after absence to catch late-appearing TAPs.
        """
        taps = 0
        while taps < max_taps:
            time.sleep(0.5)
            coords = self._find("TapArrow") or self._find("TapArrow2")
            if coords:
                self._click(*coords)
                taps += 1
                logger.info(f"✓ TAP #{taps} clicked at {coords}")
            else:
                # Wait a bit and re-check in case a new TAP appears
                time.sleep(1.5)
                coords = self._find("TapArrow") or self._find("TapArrow2")
                if coords:
                    self._click(*coords)
                    taps += 1
                    logger.info(f"✓ Late TAP #{taps} clicked at {coords}")
                else:
                    break  # Truly no more TAPs

        if taps > 0:
            logger.info(f"✓ {taps} TAP(s) cleared")
        else:
            logger.debug("No TAP pending")

    # ── COMBAT LEVEL HANDLING ──────────────────────────────────

    def _handle_combat_level(self):
        """
        Combat level sequence:
          [DemoCheckmark already visible on entry]
          Demo → Start Battle → Team → Ready
          → [auto combat] →
          FinishedPointer → (TapArrow if present) → OkBattle → (TapArrow if present) → OkBattle
          → Yes (replay) → [back to level detection]
        """
        logger.info("─── Handling COMBAT level ───")
        self._set_status("Preparing combat")

        # ── Demo: verify it's UNCHECKED before launching ───────
        self._set_action("Demo checkmark")
        if not self._ensure_demo_unchecked(timeout=20):
            return False  # recovery_requested already set by _ensure_demo_unchecked
        logger.info("✓ Demo unchecked, launching combat")

        # ── Wait for StartBattleButton to be loaded ────────────
        self._set_action("Waiting for StartBattle...")
        if not self._wait_and_click("StartBattleButton", timeout=30):
            return False  # recovery_requested already set by _wait_and_click
        logger.info("✓ Start Battle clicked")

        # ── Team selection + Ready ─────────────────────────────
        self._select_team()
        if self.recovery_requested:
            return False

        if not self._wait_and_click("ReadyButton", timeout=30):
            return False
        logger.info("✓ Ready")

        # ── Wait for end of combat ─────────────────────────────
        self.in_combat = True
        self._set_status("Combat in progress")
        self._set_action("Waiting for end of combat...")
        logger.info("Waiting for FinishedPointer...")

        combat_start = time.time()
        combat_max   = self.config["combat_timeout"]  # 600s = 10 min

        found = False
        while time.time() - combat_start < combat_max:
            if self._find("FinishedPointer"):
                self._click(*self._find("FinishedPointer"))
                found = True
                break
            time.sleep(self.loop_delay)

        self.in_combat = False

        if not found:
            logger.warning(f"FinishedPointer not found after {combat_max}s → anti-stuck reactivated, recovery")
            return False
        logger.info("✓ Combat finished")

        # Wait for post-combat animations and TAPs to load
        time.sleep(2.0)

        # ── Check victory or defeat ────────────────────────────
        if self._find_with_confidence("RematchButton", min(0.90, self.confidence + 0.15)):
            logger.info("✗ DEFEAT detected (RematchButton visible) → Rematch")
            rematch = self._find_with_confidence("RematchButton", min(0.90, self.confidence + 0.15))
            self._click(*rematch)
            self.in_combat = True
            self._set_status("Combat in progress (rematch)")
            self._set_action("Waiting for end of combat (rematch)...")
            logger.info("Waiting for FinishedPointer (rematch)...")

            combat_start = time.time()
            found = False
            while time.time() - combat_start < combat_max:
                if self._find("FinishedPointer"):
                    self._click(*self._find("FinishedPointer"))
                    found = True
                    break
                time.sleep(self.loop_delay)

            self.in_combat = False
            if not found:
                logger.warning("FinishedPointer not found after rematch → recovery")
                return False
            logger.info("✓ Rematch combat finished")
            time.sleep(2.0)

        # ── Results screen (victory confirmed) ─────────────────
        self.in_combat = True
        self._set_action("Results screen")
        for step in range(2):
            self._flush_taps()
            if not self._wait_and_click("OkBattleButton", timeout=20):
                self.in_combat = False
                return False
            logger.info(f"✓ OkBattle step {step+1}")

        # ── Replay confirmation ────────────────────────────────
        self._set_action("Replay confirmation")
        time.sleep(0.8)
        if not self._wait_and_click("YesButton", timeout=30):
            self.in_combat = False
            return False
        logger.info("✓ Replay confirmed")

        # ── Done: anti-stuck reactivated ───────────────────────
        self.in_combat = False
        logger.info("✓ Combat handled, back to level detection")
        return True

    # ── MAIN LOOP ──────────────────────────────────────────────

    def loop(self):
        """
        Infinite loop: detect level type → handle → repeat.
        """
        logger.info("="*55)
        logger.info("  FARMING LOOP STARTED")
        logger.info("="*55)
        self._set_status("Farming")

        while True:
            try:
                # ── Check if anti-stuck requested a recovery ───
                if self.recovery_requested:
                    logger.warning("Recovery requested by anti-stuck → handling")
                    self.recovery_requested = False
                    self.in_combat = False  # Safety
                    self._smart_recover()
                    continue

                level_type = self._detect_level_type(timeout=45)

                if level_type == "story":
                    logger.info("★ CINEMATIC level")
                    success = self._handle_story_level()
                    if success:
                        self.stats["completed"] += 1
                        logger.info(f"✓✓ Cinematic done | Total: {self.stats['completed']}")
                    else:
                        logger.warning("Cinematic failed → smart recovery")
                        self._smart_recover()

                elif level_type == "combat":
                    logger.info("★ COMBAT level")
                    success = self._handle_combat_level()
                    if success:
                        self.stats["loops"]     += 1
                        self.stats["completed"] += 1
                        logger.info(f"✓✓ Combat done | Combats: {self.stats['loops']} | Total: {self.stats['completed']}")
                    else:
                        logger.warning("Combat failed → smart recovery")
                        self._smart_recover()

                elif level_type == "unknown":
                    logger.warning("Unknown level type after timeout → smart recovery")
                    self._smart_recover()

                time.sleep(0.5)

            except KeyboardInterrupt:
                logger.info("Stop requested (CTRL+C)")
                print("\n[DBFarmer] Stopped. Final stats:")
                print(f"  Total completed  : {self.stats['completed']}")
                print(f"    Combats        : {self.stats['loops']}")
                print(f"    Cinematics     : {self.stats.get('story_levels', 0)}")
                print(f"  Anti-stuck fixes : {self.stats['stuck_fixed']}")
                print(f"  Recoveries       : {self.stats.get('recoveries', 0)}")
                sys.exit(0)

            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(3)

    # ── COMBAT DETECTION ───────────────────────────────────────

    def _is_in_combat(self) -> bool:
        """
        Detects if we are currently in an active combat
        by looking for the AUTO ON button (only visible during combat).
        """
        return self._find("InCombatIndicator") is not None

    # ── SMART RECOVERY ─────────────────────────────────────────

    def _smart_recover(self):
        """
        Detects the current screen and resumes from the right point
        instead of always going back to the menu.

        Priority order:
          1. In combat (AUTO ON visible)  → quit combat then recover
          2. OkBattleButton               → resume from results screen
          3. ReadyButton                  → resume from Ready
          4. StartBattleButton            → resume full combat sequence
          5. SkipButton / StorySlide      → resume cinematic
          6. TapArrow                     → flush taps and continue
          7. YesButton                    → click and continue
          8. StoryButton                  → setup()
          9. Nothing recognized           → _recover_to_menu()
        """
        logger.warning("═══ SMART RECOVERY ═══")
        self._set_status("Smart recovery...")
        self.stats["recoveries"] = self.stats.get("recoveries", 0) + 1
        self.in_combat = False
        time.sleep(1.0)

        # ── 1. In combat (AUTO ON visible) → wait for FinishedPointer ──
        if self._is_in_combat():
            logger.info("Smart recovery: AUTO ON detected → still in combat, waiting for FinishedPointer")
            self.in_combat = True
            self._set_action("Waiting for end of combat (smart recovery)...")
            combat_start = time.time()
            combat_max   = self.config["combat_timeout"]
            found = False
            while time.time() - combat_start < combat_max:
                if self._find("FinishedPointer"):
                    self._click(*self._find("FinishedPointer"))
                    found = True
                    break
                time.sleep(self.loop_delay)
            self.in_combat = False
            if not found:
                logger.warning("FinishedPointer not found after combat timeout → full recovery")
                self._recover_to_menu()
                return
            time.sleep(2.0)
            # Results screen
            self.in_combat = True
            for step in range(2):
                self._flush_taps()
                if not self._wait_and_click("OkBattleButton", timeout=20):
                    self.in_combat = False
                    self._recover_to_menu()
                    return
                logger.info(f"✓ OkBattle step {step+1}")
            time.sleep(0.8)
            self._wait_and_click("YesButton", timeout=30)
            self.in_combat = False
            logger.info("✓ Smart recovery: combat finished normally")
            return

        # ── 2. Results screen ──────────────────────────────────
        if self._find("OkBattleButton"):
            logger.info("Smart recovery: results screen → resuming from OkBattle")
            self.in_combat = True
            for step in range(2):
                self._flush_taps()
                if not self._wait_and_click("OkBattleButton", timeout=20):
                    self.in_combat = False
                    self._recover_to_menu()
                    return
                logger.info(f"✓ OkBattle step {step+1}")
            time.sleep(0.8)
            if not self._wait_and_click("YesButton", timeout=30):
                self.in_combat = False
                self._recover_to_menu()
                return
            self.in_combat = False
            logger.info("✓ Smart recovery: results handled")
            return

        # ── 3. Ready screen → go back and restart from StartBattle ──
        if self._find("ReadyButton"):
            logger.info("Smart recovery: ReadyButton visible → going back to re-select team")
            back = self._find_with_confidence("BackButton", max(0.50, self.confidence - 0.25))
            if back:
                self._click(*back)
                time.sleep(1.2)
                self._flush_taps()
            else:
                pyautogui.press("escape")
                time.sleep(1.2)
            # Now should be on StartBattle screen → full combat sequence
            if self._find("StartBattleButton"):
                logger.info("Smart recovery: StartBattle found after back → resuming full combat")
                success = self._handle_combat_level()
                if success:
                    self.stats["loops"]     += 1
                    self.stats["completed"] += 1
                else:
                    self._recover_to_menu()
            else:
                self._recover_to_menu()
            return

        # ── 4. Start Battle screen ─────────────────────────────
        if self._find("StartBattleButton"):
            logger.info("Smart recovery: StartBattle screen → resuming full combat")
            success = self._handle_combat_level()
            if success:
                self.stats["loops"]     += 1
                self.stats["completed"] += 1
            else:
                self._recover_to_menu()
            return

        # ── 5. Cinematic ───────────────────────────────────────
        if self._find("SkipButton") or self._find("StorySlide"):
            logger.info("Smart recovery: cinematic screen → resuming")
            success = self._handle_story_level()
            if success:
                self.stats["completed"] += 1
            else:
                self._recover_to_menu()
            return

        # ── 6. TAP pending ─────────────────────────────────────
        if self._find("TapArrow") or self._find("TapArrow2"):
            logger.info("Smart recovery: TAP detected → flushing")
            self._flush_taps()
            return

        # ── 7. Yes button ──────────────────────────────────────
        if self._find("YesButton"):
            logger.info("Smart recovery: YesButton detected → clicking")
            self._click(*self._find("YesButton"))
            return

        # ── 8. Already on home screen ──────────────────────────
        if self._find("StoryButton"):
            logger.info("Smart recovery: already on home screen → setup")
            self.recovery_requested = False
            self.setup()
            return

        # ── 9. Nothing recognized → full recovery ──────────────
        logger.warning("Smart recovery: screen not recognized → full recovery to menu")
        self._recover_to_menu()

    # ── RECOVERY TO MENU ───────────────────────────────────────

    def _recover_to_menu(self, max_backs: int = 15) -> bool:
        """
        Tries to return to the main menu using:
          1. BackButton  → in-game back button (highest priority)
          2. HomeButton  → visible = click = goes directly to home
          3. Escape      → if no in-game button found

        Stops as soon as StoryButton is visible.
        Once on home screen, relaunches setup().
        """
        logger.warning("═══ RECOVERY TO MENU ═══")
        self._set_status("Recovering...")
        self.stats["recoveries"] = self.stats.get("recoveries", 0) + 1

        for attempt in range(max_backs):

            # ── Already on home screen → relaunch setup ────────
            if self._find("StoryButton"):
                logger.info("✓ StoryButton visible → home screen reached")
                time.sleep(1.0)
                self.recovery_requested = False
                self.setup()
                if self.recovery_requested:
                    logger.warning("Setup interrupted → new recovery attempt")
                    continue
                return True

            # ── HomeButton visible → one click goes to home ────
            home = self._find("HomeButton")
            if home:
                logger.info(f"✓ HomeButton visible → click at {home}")
                self._click(*home)
                time.sleep(1.5)
                logger.info("✓ Home reached via HomeButton → relaunching setup")
                self.recovery_requested = False
                self.setup()
                if self.recovery_requested:
                    logger.warning("Setup interrupted → new recovery attempt")
                    continue
                return True

            # ── BackButton visible → go back one screen ────────
            back = self._find_with_confidence("BackButton", max(0.50, self.confidence - 0.25))
            if back:
                logger.info(f"Back #{attempt+1} via BackButton at {back}")
                self._click(*back)
                time.sleep(1.2)

                # QuitBattle may appear after pressing back during combat
                quit_btn = self._find("QuitBattleButton")
                if quit_btn:
                    logger.info("QuitBattle button found → clicking")
                    self._click(*quit_btn)
                    time.sleep(1.2)

                # Flush all pending TAPs after back
                self._flush_taps()

                # Refuse possible confirmation
                no = self._find("NoButton")
                if no:
                    self._click(*no)
                    time.sleep(0.8)

                continue

            # ── No in-game button found → Escape ───────────────
            logger.info(f"Back #{attempt+1} via Escape (no button found)")

            # Flush TAPs before Escape
            self._flush_taps()

            pyautogui.press("escape")
            time.sleep(1.2)

        logger.error("Could not return to menu after multiple attempts")
        return False

    # ── ANTI-STUCK (background thread) ────────────────────────

    def _anti_stuck_loop(self):
        """
        Every X seconds, compares 2 screenshots.
        If identical → game is stuck → smart click on highest priority button.
        Also detects unrecognized screens (shop, popups) and requests recovery.
        TAP buttons are clicked immediately without waiting for diff check.
        """
        time.sleep(5)  # Wait for game to launch
        logger.info("Anti-stuck started (background thread)")

        while True:
            try:
                old_ss = self._screenshot()
                time.sleep(self.config["anti_stuck_delay"])
                new_ss = self._screenshot()

                if old_ss is None or new_ss is None:
                    continue

                # Do not interfere during combat or results screen
                if self.in_combat:
                    logger.debug("Anti-stuck paused (combat in progress)")
                    continue

                # Compare the two screenshots
                diff = cv2.absdiff(
                    cv2.cvtColor(old_ss, cv2.COLOR_RGB2GRAY),
                    cv2.cvtColor(new_ss, cv2.COLOR_RGB2GRAY)
                )
                diff_score = np.sum(diff)

                # ── Check for unrecognized screen ──────────────
                on_known_screen = any([
                    self._find("StartBattleButton"),
                    self._find("StoryButton"),
                    self._find("StorySlide"),
                    self._find("SkipButton"),
                    self._find("FinishedPointer"),
                    self._find("OkBattleButton"),
                    self._find("YesButton"),
                    self._find("ReadyButton"),
                    self._find("ContinueButton"),
                    self._find("TapArrow"),
                    self._find("TapArrow2"),
                ])

                # ── TAP detected → click immediately without waiting for diff ──
                tap = self._find("TapArrow") or self._find("TapArrow2")
                if tap:
                    logger.info("Anti-stuck: TAP detected → immediate click")
                    self._click(*tap)
                    self.stats["stuck_fixed"] += 1
                    continue

                if not on_known_screen:
                    logger.warning("Anti-stuck: unrecognized screen → recovery requested")
                    self.recovery_requested = True
                    self.stats["stuck_fixed"] += 1
                    continue

                if diff_score < 50000:
                    logger.warning(f"Stuck detected! diff={diff_score}")
                    self._set_status("Anti-stuck active")

                    best_key    = None
                    best_prio   = -1
                    best_coords = None
                    for key, prio in sorted(PRIORITY_LIST.items(), key=lambda x: -x[1]):
                        coords = self._find(key)
                        if coords:
                            if prio > best_prio:
                                best_prio   = prio
                                best_key    = key
                                best_coords = coords

                    if best_key:
                        logger.info(f"Anti-stuck: clicking [{best_key}] prio={best_prio}")
                        self._click(*best_coords)
                        self.stats["stuck_fixed"] += 1
                    else:
                        logger.warning("Anti-stuck: no button found → recovery requested")
                        self.recovery_requested = True
                        self.stats["stuck_fixed"] += 1

                    self._set_status("Farming")
                else:
                    logger.debug(f"Anti-stuck OK, diff={diff_score}")

            except Exception as e:
                logger.error(f"Anti-stuck error: {e}")
                time.sleep(5)

    # ── ENTRY POINT ────────────────────────────────────────────

    def run(self):
        print("="*55)
        print("  DBFarmer v2.0 - Dragon Ball Legends")
        print("  Adapted for BlueStacks 5")
        print("="*55)
        print()
        print(f"  Config       : {CONFIG_PATH}")
        print(f"  Images       : {self.image_folder}/")
        print(f"  Log          : {log_file}")
        print(f"  Window       : {self.config['window_name']}")
        print(f"  Confidence   : {self.confidence}")
        print()
        print("  Launch the game, go to the main menu")
        print("  and make sure your team is already configured.")
        print()
        print("  CTRL+C to stop at any time.")
        print("="*55)
        print()

        # Activate BlueStacks window
        try:
            self.window.activate()
            self.window.maximize()
        except:
            logger.warning("Could not activate/maximize window")

        self.setup()
        self.loop()

# ─────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pyautogui.FAILSAFE = True   # Mouse to top-left corner = emergency stop
    pyautogui.PAUSE    = 0.05
    pyautogui.useImageNotFoundException(False)

    farmer = DBFarmer()
    farmer.run()
