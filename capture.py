"""
DBFarmer v2 - Outil de capture des images de reference
Lance ce script AVANT main.py pour capturer tous les boutons du jeu.

Usage: python capture.py
"""

import os
import sys
import time
import json
import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageGrab

IMAGE_FOLDER = "images"

# Liste de tous les boutons a capturer avec description
BUTTONS_TO_CAPTURE = [
    # ── SETUP INITIAL ──────────────────────────────────────────
    ("story",           "StoryButton",       "Le bouton 'Histoire' directement sur l'accueil du jeu"),
    ("continue",        "ContinueButton",    "Le bouton 'Continuer' pour reprendre la quete"),
    ("yes",             "YesButton",         "Le bouton 'Oui' ou 'OK' de confirmation"),
    ("no",              "NoButton",          "Le bouton 'Non' (a eviter/ignorer)"),
    ("demo",            "DemoCheckmark",     "Case 'Play Demo' VIDE/décochée (carré vide + texte Play Demo) — capture toute la zone"),
    ("demo_checked",    "DemoChecked",       "Case 'Play Demo' COCHÉE jaune (carré avec coche + texte Play Demo) — capture toute la zone"),
    ("startbattle",     "StartBattleButton", "Le bouton 'Combattre' / 'Start Battle'"),
    ("legendspointer",  "LegendsPointer",    "Point de repere pour la selection d'equipe (ex: la zone titre)"),
    ("ready",           "ReadyButton",       "Le bouton 'Pret' / 'Ready' avant le combat"),
    ("finishedpointer", "FinishedPointer",   "L'indicateur de fin de combat (texte victoire ou icone)"),
    ("tap",             "TapArrow",          "La fleche ou texte 'Appuyer pour continuer' apres combat"),
    ("okbattle",        "OkBattleButton",    "Le bouton 'OK' sur l'ecran de resultats"),
    ("skip",            "SkipButton",        "Le bouton 'Skip' pour passer une cinematique"),
    ("storyslide",      "StorySlide",        "Indicateur de slide d'histoire (boite de dialogue, fond avec texte narratif...)"),
    ("arrow",           "ArrowObject",       "Fleche de navigation generale"),
    ("close",           "CloseButton",       "Bouton X pour fermer un popup"),
    ("back",            "BackButton",        "Bouton retour du jeu (fleche retour en bas ou coin)"),
    ("home",            "HomeButton",        "Bouton home du jeu (icone maison, amene a l'accueil)"),
    ("mission",         "MissionObject",     "Le stage/niveau a selectionner dans la liste"),
]

os.makedirs(IMAGE_FOLDER, exist_ok=True)

class CaptureApp:

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DBFarmer v2 - Outil de Capture")
        self.root.geometry("700x600")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(True, True)

        self.current_idx = 0
        self.captured = {}

        # Verifier lesquelles sont deja capturees
        for fname, key, _ in BUTTONS_TO_CAPTURE:
            path = os.path.join(IMAGE_FOLDER, fname + ".png")
            if os.path.exists(path):
                self.captured[fname] = True

        self._build_ui()

    def _build_ui(self):
        # Titre
        tk.Label(self.root, text="⚡ DBFarmer v2 - Capture des Images", 
                 fg="#b060ff", bg="#1a1a2e",
                 font=("Consolas", 14, "bold")).pack(pady=10)

        tk.Label(self.root,
                 text="Clique sur 'Capturer' puis selectionne la zone sur ton ecran\n"
                      "Les images deja capturees sont indiquees en vert ✓",
                 fg="#aaaaaa", bg="#1a1a2e",
                 font=("Consolas", 9)).pack()

        # Frame liste
        list_frame = tk.Frame(self.root, bg="#1a1a2e")
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Scrollbar
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

        # Info
        self.info_var = tk.StringVar(value="Sélectionne un bouton dans la liste")
        tk.Label(self.root, textvariable=self.info_var,
                 fg="#ffcc00", bg="#1a1a2e",
                 font=("Consolas", 9), wraplength=650).pack(pady=5)

        # Boutons
        btn_frame = tk.Frame(self.root, bg="#1a1a2e")
        btn_frame.pack(pady=10)

        tk.Button(btn_frame, text="📸 Capturer (Selection zone)",
                  command=self.capture_selection,
                  bg="#4020aa", fg="white",
                  font=("Consolas", 10, "bold"),
                  padx=15, pady=8,
                  relief="flat", cursor="hand2").pack(side="left", padx=5)

        tk.Button(btn_frame, text="🖥 Screenshot complet",
                  command=self.capture_fullscreen,
                  bg="#206040", fg="white",
                  font=("Consolas", 10),
                  padx=15, pady=8,
                  relief="flat", cursor="hand2").pack(side="left", padx=5)

        tk.Button(btn_frame, text="🗑 Effacer",
                  command=self.delete_image,
                  bg="#602020", fg="white",
                  font=("Consolas", 10),
                  padx=15, pady=8,
                  relief="flat", cursor="hand2").pack(side="left", padx=5)

        tk.Button(btn_frame, text="✅ Terminer & Lancer le bot",
                  command=self.finish,
                  bg="#205060", fg="white",
                  font=("Consolas", 10, "bold"),
                  padx=15, pady=8,
                  relief="flat", cursor="hand2").pack(side="left", padx=5)

        # Progress
        done = sum(1 for _, key, _ in BUTTONS_TO_CAPTURE if os.path.exists(os.path.join(IMAGE_FOLDER, key.replace("Button","").replace("Object","").lower()+".png")))
        total = len(BUTTONS_TO_CAPTURE)
        self.progress_var = tk.StringVar(value=f"Complété: {len(self.captured)}/{total}")
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
            self.progress_var.set(f"Complété: {captured}/{total}")

    def _get_selected(self):
        sel = self.listbox.curselection()
        if not sel:
            messagebox.showwarning("Attention", "Sélectionne d'abord un bouton dans la liste !")
            return None, None, None
        idx = sel[0]
        return BUTTONS_TO_CAPTURE[idx]

    def capture_selection(self):
        """Capture par selection de zone avec un overlay transparent."""
        fname, key, desc = self._get_selected()
        if not fname:
            return

        self.info_var.set(f"Prepare: {key} - {desc}")
        self.root.update()

        self.root.withdraw()  # Cacher la fenetre
        time.sleep(0.4)

        # Lancer l'outil de selection
        SelectionCapture(self.root, fname, key, desc, self._on_capture_done)

    def capture_fullscreen(self):
        """Prend un screenshot complet et laisse l'utilisateur recadrer."""
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
            self.info_var.set(f"✓ Sauvegardé: images/{fname}.png")
        else:
            self.info_var.set("Capture annulée")
        self._refresh_list()

    def delete_image(self):
        fname, key, _ = self._get_selected()
        if not fname:
            return
        path = os.path.join(IMAGE_FOLDER, fname + ".png")
        if os.path.exists(path):
            os.remove(path)
            self.captured.pop(fname, None)
            self.info_var.set(f"🗑 Supprimé: {fname}.png")
        else:
            self.info_var.set("Pas d'image a supprimer pour cet element")
        self._refresh_list()

    def finish(self):
        captured = [f for f, _, _ in BUTTONS_TO_CAPTURE if os.path.exists(os.path.join(IMAGE_FOLDER, f+".png"))]
        total    = len(BUTTONS_TO_CAPTURE)
        missing  = [k for f, k, _ in BUTTONS_TO_CAPTURE if not os.path.exists(os.path.join(IMAGE_FOLDER, f+".png"))]

        if missing:
            ans = messagebox.askyesno("Images manquantes",
                f"{len(missing)}/{total} images manquantes:\n{', '.join(missing[:6])}...\n\n"
                "Le bot peut quand meme fonctionner mais risque d'etre incomplet.\n"
                "Continuer quand meme ?")
            if not ans:
                return

        self.root.destroy()
        print("\n[INFO] Fermeture de l'outil de capture.")
        print("[INFO] Lance maintenant: python main.py")
        sys.exit(0)

    def run(self):
        self.root.mainloop()


class SelectionCapture:
    """Overlay transparent pour selectionner une zone sur l'ecran."""

    def __init__(self, parent, fname, key, desc, callback):
        self.fname    = fname
        self.key      = key
        self.desc     = desc
        self.callback = callback
        self.start_x  = None
        self.start_y  = None
        self.rect     = None

        # Screenshot de fond
        self.bg_img = pyautogui.screenshot()
        self.bg_np  = np.array(self.bg_img)

        # Fenetre overlay
        self.win = tk.Toplevel(parent)
        self.win.attributes("-fullscreen", True)
        self.win.attributes("-alpha", 0.35)
        self.win.configure(bg="black")
        self.win.attributes("-topmost", True)

        # Canvas
        self.canvas = tk.Canvas(self.win, cursor="crosshair", bg="black",
                                 highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

        # Instructions
        sw = self.win.winfo_screenwidth()
        self.canvas.create_text(sw//2, 40,
                                 text=f"Sélectionne la zone: {key}\n{desc}\n(Clique et glisse)",
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
            e.x, e.y, e.x, e.y,
            outline="#b060ff", width=2, fill="")

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

        # Recapture propre (sans l'overlay)
        time.sleep(0.1)
        clean_ss = pyautogui.screenshot(region=(x1, y1, x2-x1, y2-y1))
        clean_np = np.array(clean_ss)

        path = os.path.join(IMAGE_FOLDER, self.fname + ".png")
        cv2.imwrite(path, cv2.cvtColor(clean_np, cv2.COLOR_RGB2BGR))
        print(f"[OK] Sauvegardé: {path} ({x2-x1}x{y2-y1}px)")

        self.callback(self.fname, True)

    def _cancel(self):
        self.win.destroy()
        self.callback(self.fname, False)


class CropWindow:
    """Fenetre pour recadrer un screenshot complet."""

    def __init__(self, parent, ss_np, fname, key, desc, callback):
        self.fname    = fname
        self.key      = key
        self.ss_np    = ss_np
        self.callback = callback

        self.win = tk.Toplevel(parent)
        self.win.title(f"Recadrer: {key}")
        self.win.configure(bg="#1a1a2e")
        self.win.attributes("-topmost", True)

        tk.Label(self.win, text=f"Sélectionne la zone pour: {key}\n{desc}",
                 fg="#ffcc00", bg="#1a1a2e",
                 font=("Consolas", 9)).pack(pady=5)

        # Redimensionner l'image pour l'affichage
        h, w = ss_np.shape[:2]
        max_w, max_h = 900, 550
        scale = min(max_w/w, max_h/h)
        self.scale  = scale
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
        tk.Button(btn_f, text="Annuler", command=self._cancel,
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
        print(f"[OK] Sauvegardé: {path} ({x2-x1}x{y2-y1}px)")
        self.callback(self.fname, True)

    def _cancel(self):
        self.win.destroy()
        self.callback(self.fname, False)


if __name__ == "__main__":
    print("DBFarmer v2 - Outil de Capture")
    print("="*40)
    app = CaptureApp()
    app.run()
