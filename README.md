# DBFarmer v2 🐉
**Dragon Ball Legends - Story Mode Farmer for BlueStacks 5**

Modernized fork of the original [LUXTACO](https://github.com/LUXTACO/DBFarmer) project, fully rewritten for BlueStacks 5 and the current version of the game.

---

## ✨ What's new vs the original

- ✅ Compatible with **BlueStacks 5**
- ✅ **OpenCV** template matching (more reliable detection)
- ✅ Automatic handling of **cinematic levels** (story slides without combat)
- ✅ Intelligent level type detection (combat or cinematic)
- ✅ **Play Demo** checkbox verification before each battle
- ✅ **Multiple TAP** handling after combat (level up, objectives)
- ✅ **Defeat detection** with automatic Rematch
- ✅ **Smart Recovery** — detects current screen and resumes from the right point
- ✅ **In-combat detection** via AUTO ON button
- ✅ **QuitBattle** support during recovery
- ✅ Real-time **overlay** with stats and logs (draggable)
- ✅ **Anti-stuck** background thread with automatic recovery
- ✅ Team slots configured via **absolute coordinates** in `config.json`
- ✅ Built-in **image capture tool** (`capture.py`) with "Done & Launch bot" button
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

Click **"Done & Launch bot"** when finished — it will start the bot automatically.

### Buttons to capture:

| Image | Description |
|-------|-------------|
| `story.png` | "Story" button on the home screen |
| `continue.png` | "Continue" button (resume progress) |
| `yes.png` | "Yes" / confirmation button |
| `no.png` | "No" button |
| `demo.png` | **"Play Demo" unchecked** (empty checkbox) ✅ already included |
| `demo_checked.png` | **"Play Demo" checked** (yellow checkmark) ✅ already included |
| `startbattle.png` | "Start Battle" button |
| `legendspointer.png` | Any element visible on team selection screen (e.g. "Details" button) — used as signal that the screen is ready |
| `ready.png` | "Ready" button |
| `finishedpointer.png` | End of battle indicator |
| `tap.png` | "Tap to continue" arrow after battle (centered bottom) |
| `tap2.png` | TAP icon variant (bottom right corner) |
| `okbattle.png` | "OK" button on results screen |
| `skip.png` | "Skip" button on cinematic levels |
| `storyslide.png` | Story slide indicator (dialogue box, narrative background) |
| `rematch.png` | "Rematch" button — only visible on defeat screen |
| `quitbattle.png` | "Quit Battle" button — appears after pressing back during combat |
| `incombat.png` | **AUTO ON** button — visible only during active combat (top left) |
| `back.png` | In-game back button (used for recovery) |
| `home.png` | In-game home button (used for recovery) |
| `mission.png` | The stage/level to select |

> **Note**: `demo.png` and `demo_checked.png` are already included — no need to recapture them.

> **Tip**: Capture images with BlueStacks in **fullscreen** mode for best results.

---

## ⚙️ Step 2: Configure positions

### Skip button
The Skip button is clicked using fixed coordinates. Measure its position once:

```python
import pyautogui, time
time.sleep(3)
print(pyautogui.position())
```
Hover over the Skip button within 3 seconds, then update `config.json`:
```json
"skip_position": {
    "mode": "absolute",
    "x": 1120,
    "y": 70
}
```

### Team slots
Character slots are clicked using absolute coordinates defined in `config.json`:
```json
"team_slots": [
    {"x": 845, "y": 631},
    {"x": 945, "y": 631},
    {"x": 1045, "y": 631},
    {"x": 845, "y": 731},
    {"x": 945, "y": 731},
    {"x": 1045, "y": 731}
]
```
If the bot clicks the wrong slots, adjust these values to match your screen. Row 1 = slots 1–3, Row 2 = slots 4–6.

---

## 🤖 Step 3: Run the bot

```
python main.py
```
or `start.bat` → choice **3**.

Before launching:
- ✅ BlueStacks 5 is open in **fullscreen**
- ✅ The game is on the **home screen**
- ✅ Your team is already configured in the game

**CTRL+C** to stop cleanly.  
**Mouse to top-left corner** = emergency stop (pyautogui failsafe).

---

## 🔄 How it works

### Startup sequence (once)
```
Home → Story → Continue
```

### Main loop
The bot detects the type of each level automatically:

**COMBAT level**:
```
Verify Play Demo unchecked → Start Battle
→ Team selection (6 slots) → Ready
→ [auto battle]
→ FinishedPointer detected
→ TAP(s) if any → OK → TAP(s) if any → OK
→ Yes (replay) → [next level]
```

**CINEMATIC level**:
```
Skip → Yes (confirm)
```

### Smart Recovery
When something goes wrong, the bot detects the current screen and resumes from the right point:

| Screen detected | Action |
|----------------|--------|
| AUTO ON visible | Still in combat → wait for FinishedPointer |
| OkBattleButton | Resume from results screen |
| ReadyButton | Go back → re-select team → full combat |
| StartBattleButton | Resume full combat sequence |
| SkipButton / StorySlide | Resume cinematic |
| TapArrow | Flush TAPs and continue |
| YesButton | Click and continue |
| StoryButton | Re-run setup |
| Nothing recognized | Full recovery: Back → Home → Escape |

### Anti-stuck
Running as a background thread every 60 seconds:
- TAP detected → clicks immediately
- Screen frozen (no pixel diff) → clicks highest priority button
- Unrecognized screen → requests recovery
- Paused during combat and results screen to avoid false positives

---

## ⚙️ Configuration (config.json)

| Parameter | Default | Description |
|-----------|---------|-------------|
| `window_name` | `BlueStacks App Player` | BlueStacks window title |
| `confidence` | `0.75` | OpenCV detection threshold (0.5–0.95) |
| `click_delay` | `0.5` | Delay after each click (sec) |
| `loop_delay` | `1.0` | Delay between each check (sec) |
| `anti_stuck_delay` | `60.0` | Anti-stuck check interval (sec) |
| `combat_timeout` | `600` | Max combat duration before recovery (sec) |
| `overlay_enabled` | `true` | Show overlay window |
| `skip_position` | `x:1120, y:70` | Absolute coordinates of the Skip button |
| `team_slots` | 6 positions | Absolute coordinates for each character slot |

---

## ❓ Common issues

**"BlueStacks window not found"**  
→ Make sure BlueStacks 5 is open. Check `window_name` in `config.json` matches your window title exactly.

**Bot clicks wrong character slots**  
→ Adjust the `team_slots` coordinates in `config.json` to match your screen layout.

**Skip doesn't click in the right place**  
→ Measure the exact coordinates of the Skip button and update `skip_position` in `config.json`.

**Detection too sensitive / not sensitive enough**  
→ Adjust `confidence` in `config.json` (higher = stricter, lower = more lenient).

**Bot detects Play Demo as checked when it's not**  
→ Recapture `demo.png` and `demo_checked.png` making sure to include the full checkbox + "Play Demo" text.

**Bot keeps recovering for no reason**  
→ Lower `confidence` slightly or recapture the image that is causing false negatives.

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
