"""
DBFarmer v2 - Reference Image Capture Tool
Run this script BEFORE main.py to capture all game buttons.

Usage: python capture.py
"""

import os
import sys
import time
import tkinter as tk
from tkinter import messagebox
import pyautogui
import cv2
import numpy as np
from PIL import Image, ImageTk

IMAGE_FOLDER = "images"

# List of all buttons to capture with descriptions
BUTTONS_TO_CAPTURE = [
    # ── INITIAL SETUP ──────────────────────────────────────────
    ("story",           "StoryButton",       "The 'Story' button on the game home screen"),
    ("continue",        "ContinueButton",    "The 'Continue' button to resume your progress"),
    ("yes",             "YesButton",         "The 'Yes' / 'OK' confirmation button"),
    ("no",              "NoButton",          "The 'No' button (to avoid / ignore)"),
    ("demo",            "DemoCheckmark",     "'Play Demo' UNCHECKED (empty checkbox + Play Demo text) — capture full zone"),
    ("demo_checked",    "DemoChecked",       "'Play Demo' CHECKED yellow (checkmark + Play Demo text) — capture full zone"),
    ("startbattle",     "StartBattleButton", "The 'Start Battle' button"),
    ("legendspointer",  "LegendsPointer",    "Reference point for team selection (e.g. title zone)"),
    ("ready",           "ReadyButton",       "The 'Ready' button before combat"),
    ("finishedpointer", "FinishedPointer",   "End of combat indicator (victory text or icon)"),
    ("tap",             "TapArrow",          "'Tap to continue' arrow after combat (centered at bottom)"),
    ("tap2",            "TapArrow2",         "TAP icon variant (bottom right corner of screen)"),
    ("okbattle",        "OkBattleButton",    "The 'OK' button on the results screen"),
    ("skip",            "SkipButton",        "The 'Skip' button to skip a cinematic"),
    ("storyslide",      "StorySlide",        "Story slide indicator (dialogue box, narrative background...)"),
    ("rematch",         "RematchButton",     "'Rematch' button — only visible on defeat screen (next to OK)"),
    ("back",            "BackButton",        "In-game back button (used for recovery when stuck)"),
    ("home",            "HomeButton",        "In-game home button (used for recovery when stuck)"),
    ("mission",         "MissionObject",     "The stage/level to select in the list"),
]

os.makedirs(IMAGE_FOLDER, exist_ok=True)


class CaptureApp:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DBFarmer v2 - Capture Tool")
        self.root.geometry("700x600")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(True, True)

        self.captured = {}
        for fname, key, _ in BUTTONS_TO_CAPTURE:
            path = os.path.join(IMAGE_FOLDER, fname + ".png")
            if os.path.exists(path):
                self.captured[fname] = True

        self._build_ui()

    def _build_ui(self):
        tk.Label(self.root, text="⚡ DBFarmer v2 - Image Capture",
                 fg="#b060ff", bg="#1a1a2e",
                 font=("Consolas", 14, "bold")).pack(pady=10)

        tk.Label(self.root,
                 text="Click 'Capture' then select the zone on your screen\n"
                      "Already captured images are shown in green ✓",
                 fg="#aaaaaa", bg="#1a1a2e",
                 font=("Consolas", 9)).pack()

        list_frame = tk.Frame(self.root, bg="#1a1a2e")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")

        self.listbox = tk.Listbox(list_frame,
                                   yscrollcommand=scrollbar.set,
                                   bg="#0d0d1a", fg="#dddddd",
                                   font=("Consolas", 10),
                                   selectbackground="#4020aa",
                                   height=15)
        self.listbox.pack(fill="both", expand=True)
        scrollbar.config(command=self.listbox.yview)

        self._refresh_list()

        self.info_var = tk.StringVar(value="Select a button from the list")
        tk.Label(self.root, textvariable=self.info_var,
                 fg="#ffcc00", bg="#1a1a2e",
                 font=("Consolas", 9), wraplength=650).pack(pady=5)

        btn_frame = tk.Frame(self.root, bg="#1a1a2e")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="📸 Capture (Select zone)",
                  command=self.capture_selection,
                  bg="#4020aa", fg="white",
                  font=("Consolas", 10, "bold"),
                  padx=15, pady=8,
                  relief="flat", cursor="hand2").pack(side="left", padx=5)

        tk.Button(btn_frame, text="🖥 Full screenshot",
                  command=self.capture_fullscreen,
                  bg="#206040", fg="white",
                  font=("Consolas", 10),
                  padx=15, pady=8,
                  relief="flat", cursor="hand2").pack(side="left", padx=5)

        tk.Button(btn_frame, text="🗑 Delete",
                  command=self.delete_image,
                  bg="#602020", fg="white",
                  font=("Consolas", 10),
                  padx=15, pady=8,
                  relief="flat", cursor="hand2").pack(side="left", padx=5)

        tk.Button(btn_frame, text="✅ Done & Launch bot",
                  command=self.finish,
                  bg="#205060", fg="white",
                  font=("Consolas", 10, "bold"),
                  padx=15, pady=8,
                  relief="flat", cursor="hand2").pack(side="left", padx=5)

        total = len(BUTTONS_TO_CAPTURE)
        self.progress_var = tk.StringVar(value=f"Completed: {len(self.captured)}/{total}")
        tk.Label(self.root, textvariable=self.progress_var,
                 fg="#60ff90", bg="#1a1a2e",
                 font=("Consolas", 10)).pack(pady=3)

    def _refresh_list(self):
        self.listbox.delete(0, "end")
        for fname, key, desc in BUTTONS_TO_CAPTURE:
            path = os.path.join(IMAGE_FOLDER, fname + ".png")
            exists = os.path.exists(path)
            status = "✓" if exists else "○"
            color  = "#60ff90" if exists else "#ff6060"
            self.listbox.insert("end", f"  {status}  {key:<22}  {desc[:38]}")
            idx = self.listbox.size() - 1
            self.listbox.itemconfig(idx, fg=color)

        total = len(BUTTONS_TO_CAPTURE)
        captured = sum(1 for f, _, _ in BUTTONS_TO_CAPTURE if os.path.exists(os.path.join(IMAGE_FOLDER, f+".png")))
        if hasattr(self, 'progress_var'):
            self.progress_var.set(f"Completed: {captured}/{total}")

    def _get_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Warning", "Please select a button from the list first!")
            return None, None, None
        return BUTTONS_TO_CAPTURE[sel[0]]

    def capture_selection(self):
        fname, key, desc = self._get_selected()
        if not fname:
            return
        self.info_var.set(f"Preparing: {key} - {desc}")
        self.root.update()
        self.root.withdraw()
        time.sleep(0.4)
        SelectionCapture(self.root, fname, key, desc, self._on_capture_done)

    def capture_fullscreen(self):
        fname, key, desc = self._get_selected()
        if not fname:
            return
        self.root.withdraw()
        time.sleep(0.4)
        ss = pyautogui.screenshot()
        ss_np = np.array(ss)
        self.root.deiconify()
        CropWindow(self.root, ss_np, fname, key, desc, self._on_capture_done)

    def _on_capture_done(self, fname, success):
        self.root.deiconify()
        if success:
            self.captured[fname] = True
            self.info_var.set(f"✓ Saved: images/{fname}.png")
        else:
            self.info_var.set("Capture cancelled")
        self._refresh_list()

    def delete_image(self):
        fname, key, _ = self._get_selected()
        if not fname:
            return
        path = os.path.join(IMAGE_FOLDER, fname + ".png")
        if os.path.exists(path):
            os.remove(path)
            self.captured.pop(fname, None)
            self.info_var.set(f"🗑 Deleted: {fname}.png")
        else:
            self.info_var.set("No image to delete for this item")
        self._refresh_list()

    def finish(self):
        total   = len(BUTTONS_TO_CAPTURE)
        missing = [k for f, k, _ in BUTTONS_TO_CAPTURE if not os.path.exists(os.path.join(IMAGE_FOLDER, f+".png"))]

        if missing:
            ans = messagebox.askyesno("Missing images",
                f"{len(missing)}/{total} images missing:\n{', '.join(missing[:6])}...\n\n"
                "The bot can still run but may be incomplete.\n"
                "Continue anyway?")
            if not ans:
                return

        self.root.destroy()
        print("\n[INFO] Capture tool closed.")
        print("[INFO] Now run: python main.py")
        sys.exit(0)

    def run(self):
        self.root.mainloop()


class SelectionCapture:
    """Transparent overlay to select a zone on screen."""

    def __init__(self, parent, fname, key, desc, callback):
        self.fname    = fname
        self.key      = key
        self.callback = callback
        self.start_x  = None
        self.start_y  = None
        self.rect     = None

        self.win = tk.Toplevel(parent)
        self.win.attributes("-fullscreen", True)
        self.win.attributes("-alpha", 0.35)
        self.win.configure(bg="black")
        self.win.attributes("-topmost", True)

        self.canvas = tk.Canvas(self.win, cursor="crosshair", bg="black",
                                 highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        sw = self.win.winfo_screenwidth()
        self.canvas.create_text(sw//2, 40,
                                 text=f"Select zone: {key}\n{desc}\n(Click and drag)",
                                 fill="yellow", font=("Arial", 14, "bold"),
                                 justify="center")

        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.win.bind("<Escape>", lambda e: self._cancel())

    def _on_press(self, e):
        self.start_x = e.x
        self.start_y = e.y
        self.rect = self.canvas.create_rectangle(
            e.x, e.y, e.x, e.y, outline="#b060ff", width=2, fill="")

    def _on_drag(self, e):
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, e.x, e.y)

    def _on_release(self, e):
        x1 = min(self.start_x, e.x)
        y1 = min(self.start_y, e.y)
        x2 = max(self.start_x, e.x)
        y2 = max(self.start_y, e.y)

        if x2 - x1 < 5 or y2 - y1 < 5:
            self._cancel()
            return

        self.win.destroy()
        time.sleep(0.1)
        clean_ss = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
        clean_np = np.array(clean_ss)

        path = os.path.join(IMAGE_FOLDER, self.fname + ".png")
        cv2.imwrite(path, cv2.cvtColor(clean_np, cv2.COLOR_RGB2BGR))
        print(f"[OK] Saved: {path} ({x2-x1}x{y2-y1}px)")
        self.callback(self.fname, True)

    def _cancel(self):
        self.win.destroy()
        self.callback(self.fname, False)


class CropWindow:
    """Window to crop a full screenshot."""

    def __init__(self, parent, ss_np, fname, key, desc, callback):
        self.fname    = fname
        self.ss_np    = ss_np
        self.callback = callback

        self.win = tk.Toplevel(parent)
        self.win.title(f"Crop: {key}")
        self.win.configure(bg="#1a1a2e")
        self.win.attributes("-topmost", True)

        tk.Label(self.win, text=f"Select zone for: {key}\n{desc}",
                 fg="#ffcc00", bg="#1a1a2e",
                 font=("Consolas", 9)).pack(pady=5)

        h, w = ss_np.shape[:2]
        max_w, max_h = 900, 550
        scale = min(max_w/w, max_h/h)
        self.scale = scale
        disp_w = int(w * scale)
        disp_h = int(h * scale)

        img_rgb  = cv2.cvtColor(ss_np, cv2.COLOR_RGB2BGR)
        img_disp = cv2.resize(img_rgb, (disp_w, disp_h))
        img_pil  = Image.fromarray(cv2.cvtColor(img_disp, cv2.COLOR_BGR2RGB))
        self.tk_img = ImageTk.PhotoImage(img_pil)

        self.canvas = tk.Canvas(self.win, width=disp_w, height=disp_h,
                                 cursor="crosshair", bg="black")
        self.canvas.pack(padx=5, pady=5)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

        self.start_x = self.start_y = None
        self.rect = None

        self.canvas.bind("<ButtonPress-1>",   self._on_press)
        self.canvas.bind("<B1-Motion>",       self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.win.bind("<Escape>", lambda e: self._cancel())

        btn_f = tk.Frame(self.win, bg="#1a1a2e")
        btn_f.pack(pady=5)
        tk.Button(btn_f, text="Cancel", command=self._cancel,
                  bg="#602020", fg="white", padx=10).pack(side="left", padx=5)

    def _on_press(self, e):
        self.start_x = e.x
        self.start_y = e.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(e.x, e.y, e.x, e.y,
                                                  outline="#b060ff", width=2)

    def _on_drag(self, e):
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, e.x, e.y)

    def _on_release(self, e):
        x1 = int(min(self.start_x, e.x) / self.scale)
        y1 = int(min(self.start_y, e.y) / self.scale)
        x2 = int(max(self.start_x, e.x) / self.scale)
        y2 = int(max(self.start_y, e.y) / self.scale)

        if x2 - x1 < 5 or y2 - y1 < 5:
            return

        self.win.destroy()
        crop = self.ss_np[y1:y2, x1:x2]
        path = os.path.join(IMAGE_FOLDER, self.fname + ".png")
        cv2.imwrite(path, cv2.cvtColor(crop, cv2.COLOR_RGB2BGR))
        print(f"[OK] Saved: {path} ({x2-x1}x{y2-y1}px)")
        self.callback(self.fname, True)

    def _cancel(self):
        self.win.destroy()
        self.callback(self.fname, False)


if __name__ == "__main__":
    print("DBFarmer v2 - Image Capture Tool")
    print("="*40)
    app = CaptureApp()
    app.run()
