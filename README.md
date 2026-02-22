# DBFarmer v2 🐉
**Dragon Ball Legends - Story Mode Farmer for BlueStacks 5**

Modernized fork of the original [LUXTACO](https://github.com/LUXTACO/DBFarmer) project, fully rewritten for BlueStacks 5 and the current version of the game.

---

## ✨ Changes vs the original

- ✅ Compatible with **BlueStacks 5** (original was for MEmu — window must be named "BlueStacks App Player")
- ✅ **OpenCV** template matching detection (more reliable than pyautogui alone)
- ✅ Automatic handling of **cinematic levels** (story slides without combat)
- ✅ Intelligent level type detection (combat or cinematic)
- ✅ **Play Demo** checkbox state verification before each battle
- ✅ **Multiple TAP** handling after combat (level up, objectives)
- ✅ **Defeat detection** with automatic Rematch
- ✅ Real-time **overlay** with stats and logs (draggable)
- ✅ **Anti-stuck** with automatic recovery to main menu
- ✅ Built-in **image capture tool** (`capture.py`)
- ✅ Removed Discord dependency
- ✅ Per-session logs in `logs/` folder

---

## ⚡ Quick Install

Double-click `start.bat` → choice **1** (install dependencies)

Or manually:
```
pip install pyautogui opencv-python pillow numpy pygetwindow
```

---

## 📸 Step 1: Capture button images

Run `start.bat` → choice **2**, or:
```
python capture.py
```

A GUI will open. For each button:
1. Select it in the list
2. Click **"Capture (Select zone)"**
3. The window hides → draw a rectangle around the button in the game
4. The zone is saved automatically ✓

### Buttons to capture:

| Image | Description |
|-------|-------------|
| `story.png` | "Story" button on the home screen |
| `continue.png` | "Continue" button (resume progress) |
| `yes.png` | "Yes" / confirmation button |
| `no.png` | "No" button |
| `demo.png` | **"Play Demo" unchecked** (empty checkbox — required state to launch auto battle) |
| `demo_checked.png` | **"Play Demo" checked** (yellow checkmark — bot will uncheck it) |
| `startbattle.png` | "Start Battle" button |
| `legendspointer.png` | Reference zone for team selection |
| `ready.png` | "Ready" button |
| `finishedpointer.png` | End of battle indicator |
| `tap.png` | "TAP" button / arrow after battle (centered at bottom) |
| `tap2.png` | "TAP" icon variant (bottom right corner) |
| `okbattle.png` | "OK" button on results screen |
| `rematch.png` | "Rematch" button — only visible on defeat screen |
| `storyslide.png` | Story slide indicator (dialogue box, narrative background) |
| `arrow.png` | General navigation arrow |
| `back.png` | In-game back button (used for recovery when stuck) |
| `home.png` | In-game home button (used for recovery when stuck) |
| `mission.png` | The stage/level to select |

> **Note**: `demo.png` and `demo_checked.png` are already included in the `images/` folder — no need to recapture them.

> **Tip**: Capture images with BlueStacks in **fullscreen** mode.

---

## ⚙️ Configure Skip position (important)

The **Skip** button on cinematic levels is clicked using fixed coordinates (more reliable than image detection). You only need to measure its position **once**:

1. Open the game on a cinematic level (slide visible with the Skip button)
2. In a Python terminal:
```python
import pyautogui, time
time.sleep(3)
print(pyautogui.position())
```
3. Within 3 seconds, hover your mouse **over the Skip button**
4. Note the coordinates and put them in `config.json`:

```json
"skip_position": {
    "mode": "absolute",
    "x": 1120,
    "y": 70
}
```

---

## 🤖 Step 2: Run the bot

```
python main.py
```
or `start.bat` → choice **3**.

Before launching:
- ✅ BlueStacks 5 is open in **fullscreen**
- ✅ The game is on the **home screen** (not in combat)
- ✅ You have energy to play

**CTRL+C** to stop cleanly.  
**Mouse to top-left corner** = emergency stop (pyautogui failsafe).

---

## 🔄 How it works

### Startup sequence (once)
```
Home → Story → Continue
```

### Main loop
The bot automatically detects the type of each level:

**COMBAT level**:
```
Verify Play Demo unchecked → Start Battle → Team selection → Ready
→ [auto battle] →
FinishedPointer → Victory or Defeat (Rematch) →
TAP(s) if level up → OK → TAP(s) → OK → Yes (replay)
→ [next level]
```

**CINEMATIC level** (story slides without combat):
```
Skip → Yes
```

### Stuck handling
Every timeout automatically triggers a recovery:
1. Anti-stuck sets a `recovery_requested` flag
2. Main loop detects it between each action
3. `_recover_to_menu()` returns to menu via `BackButton` → `HomeButton` → Escape
4. `setup()` restarts farming from the home screen

The anti-stuck is **paused** during combat and the results screen to avoid false positives.

---

## ⚙️ Configuration (config.json)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `window_name` | `BlueStacks App Player` | BlueStacks window title |
| `confidence` | `0.75` | OpenCV detection threshold (0.5–0.95) |
| `click_delay` | `0.5` | Delay after each click (sec) |
| `anti_stuck_delay` | `60.0` | Anti-stuck check frequency (sec) |
| `combat_timeout` | `600` | Max combat duration before recovery (sec) |
| `overlay_enabled` | `true` | Show overlay |
| `skip_position` | `x:1120, y:70` | Absolute coordinates of the Skip button |

---

## ❓ Common issues

**"BlueStacks window not found"**  
→ Make sure BlueStacks 5 is open. Run `python main.py` to see the list of detected windows and adjust `window_name` in `config.json`.

**Bot launches combat with Play Demo checked**  
→ Recapture `demo.png` (empty checkbox) and `demo_checked.png` (yellow checkmark) making sure to include the "Play Demo" text in your selection area.

**Skip doesn't click in the right place**  
→ Measure the exact coordinates of the Skip button and update `config.json` → `skip_position`.

**Detection too sensitive / not sensitive enough**  
→ Adjust `confidence` in `config.json` (higher = stricter, lower = more lenient).

**Bot gets stuck**  
→ The anti-stuck triggers automatically every 60s. It detects unrecognized screens (shop, popups, etc.) and sets a recovery flag. The main loop returns to menu via `back.png` → `home.png` → Escape, then restarts setup. During combat and results screen, anti-stuck is paused. If combat exceeds 10 min, anti-stuck reactivates and forces recovery.

---

## 📦 Dependencies

- Python 3.8+
- pyautogui
- opencv-python
- pillow
- numpy
- pygetwindow

---

## 🙏 Credits

Based on [DBFarmer](https://github.com/LUXTACO/DBFarmer) by **LUXTACO**.
