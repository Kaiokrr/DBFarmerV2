"""
DBFarmer v2.0 - Dragon Ball Legends Story Farmer
Modernisé pour BlueStacks 5 par rapport au DBFarmer original de LUXTACO
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
#  CONFIGURATION PAR DEFAUT
# ─────────────────────────────────────────────────────────────

DEFAULT_CONFIG = {
    "window_name": "BlueStacks App Player",   # Titre de la fenetre BlueStacks 5
    "image_folder": "images",                  # Dossier des images de reference
    "confidence": 0.75,                        # Seuil de detection (0.0 a 1.0)
    "loop_delay": 1.0,                         # Delai entre chaque verification (sec)
    "click_delay": 0.5,                        # Delai apres un clic (sec)
    "anti_stuck_delay": 60.0,                  # Intervalle anti-stuck (sec)
    "max_tries": 15,                           # Nb max de tentatives par bouton
    "combat_timeout": 600,                     # Timeout combat max (sec) = 10 min
    "overlay_enabled": True,                   # Afficher l'overlay
    "log_level": "INFO",
    "skip_position": {
        "x_pct": 0.82,   # Position X en % de la largeur de la fenetre (0.82 = 82% = droite)
        "y_pct": 0.05    # Position Y en % de la hauteur de la fenetre (0.05 = 5% = haut)
    }
}

CONFIG_PATH = "config.json"
LOG_DIR = "logs"

# Noms des fichiers images attendus dans le dossier images/
# Tu dois capturer ces boutons depuis ton jeu et les sauvegarder avec ces noms exactement
IMAGE_FILES = {
    # ── SETUP INITIAL ──────────────────────────────────────────
    "StoryButton":      "story.png",          # Bouton "Histoire" directement sur l'accueil
    "ContinueButton":   "continue.png",       # Bouton "Continuer" (reprendre la quete)

    # ── SELECTION DU COMBAT ────────────────────────────────────
    "MissionObject":    "mission.png",        # Le niveau/stage a cliquer
    "DemoCheckmark":    "demo.png",           # Case "Play Demo" VIDE (bon état → lancer le combat sans y toucher)
    "DemoChecked":      "demo_checked.png",   # Case "Play Demo" COCHÉE jaune (mauvais état → cliquer pour décocher)
    "StartBattleButton":"startbattle.png",    # Bouton "Combattre" / "Start Battle"
    "YesButton":        "yes.png",            # Bouton "Oui" / confirmation
    "NoButton":         "no.png",             # Bouton "Non" (a ignorer / eviter)

    # ── SELECTION DE L'EQUIPE ──────────────────────────────────
    "LegendsPointer":   "legendspointer.png", # Point de repere pour placer l'equipe
    "ReadyButton":      "ready.png",          # Bouton "Pret" / "Ready"

    # ── PENDANT / FIN DU COMBAT ───────────────────────────────
    "FinishedPointer":  "finishedpointer.png",# Indicateur de fin de combat
    "TapArrow":         "tap.png",            # Fleche "Tap to continue" apres combat
    "OkBattleButton":   "okbattle.png",       # Bouton "OK" sur l'ecran de resultats
    "SkipButton":       "skip.png",           # Bouton "Skip" (passer une cinematique)

    # ── NIVEAUX CINEMATIQUE (slides d'histoire sans combat) ───
    "StorySlide":       "storyslide.png",     # Indicateur qu'on est sur un slide d'histoire (ex: boite de dialogue, fond noir avec texte)

    # ── NAVIGATION / ANTI-STUCK ───────────────────────────────
    "ArrowObject":      "arrow.png",          # Fleche de navigation generale
    "CloseButton":      "close.png",          # Bouton fermer (X) sur popups
    "BackButton":       "back.png",           # Bouton retour du jeu
    "HomeButton":       "home.png",           # Bouton home du jeu (amène à l'accueil)
}

# Priorite pour l'anti-stuck (plus le chiffre est haut, plus c'est prioritaire)
PRIORITY_LIST = {
    "SkipButton":        15,
    "ArrowObject":       13,
    "CloseButton":       12,
    "TapArrow":          11,
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

# Offsets pour cliquer sur les 3 personnages de l'equipe
# (relatifs au LegendsPointer detecte)
TEAM_OFFSETS = {
    "y":       90,   # Decalage vertical vers les persos
    "char1_x": 300,  # Decalage horizontal perso 1
    "char2_x": 200,  # Decalage horizontal perso 2
    "char3_x": 100,  # Decalage horizontal perso 3
}

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
#  GESTION DE LA CONFIG
# ─────────────────────────────────────────────────────────────

def load_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r") as f:
                config = json.load(f)
            # Fusion avec les valeurs par defaut (pour les nouvelles cles)
            for key, val in DEFAULT_CONFIG.items():
                config.setdefault(key, val)
            logger.info(f"Config chargee depuis {CONFIG_PATH}")
            return config
        except Exception as e:
            logger.warning(f"Erreur lecture config: {e} -> utilisation config par defaut")
    # Creer la config par defaut
    with open(CONFIG_PATH, "w") as f:
        json.dump(DEFAULT_CONFIG, f, indent=4)
    logger.info(f"Config par defaut creee dans {CONFIG_PATH}")
    return DEFAULT_CONFIG.copy()

# ─────────────────────────────────────────────────────────────
#  OVERLAY TKINTER (affichage en temps reel)
# ─────────────────────────────────────────────────────────────

class Overlay:
    def __init__(self, get_data_callback):
        self.get_data = get_data_callback
        self.root = tk.Tk()
        self.root.title("DBFarmer v2")
        self.root.overrideredirect(True)         # Pas de barre de titre Windows
        self.root.geometry("+5+5")
        self.root.wm_attributes("-topmost", True)
        self.root.configure(bg="#0d0d0d")
        self.root.wm_attributes("-alpha", 0.92)

        # Barre de titre custom
        bar = tk.Frame(self.root, bg="#1a0a2e", pady=3)
        bar.pack(fill="x")
        tk.Label(bar, text="⚡ DBFarmer v2 | BlueStacks 5 ⚡",
                 fg="#b060ff", bg="#1a0a2e",
                 font=("Consolas", 10, "bold")).pack(side="left", padx=8)
        tk.Label(bar, text="✕", fg="#ff5555", bg="#1a0a2e",
                 font=("Consolas", 11, "bold"), cursor="hand2").pack(side="right", padx=6)

        # Stats
        self.status_var = tk.StringVar(value="⏳ Démarrage...")
        self.loop_var   = tk.StringVar(value="Boucles: 0")
        self.stuck_var  = tk.StringVar(value="Anti-stuck: OK")
        self.action_var = tk.StringVar(value="Action: En attente")

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
            self.loop_var.set(f"🔁 Boucles: {data.get('loops', 0)} | Complétées: {data.get('completed', 0)}")
            self.stuck_var.set(f"🛡 Anti-stuck: {data.get('stuck_fixed', 0)} fix(s)")
            self.action_var.set(f"⚡ Action: {data.get('action', '...')}")

            # Afficher derniere ligne du log
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
#  CLASSE PRINCIPALE DU FARMER
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
            "status":      "Initialisation",
            "loops":       0,
            "completed":   0,
            "stuck_fixed": 0,
            "action":      "Démarrage",
        }

        # Flag pour désactiver l'anti-stuck pendant les combats
        self.in_combat = False

        os.makedirs(self.image_folder, exist_ok=True)

        # Charger les images
        self.images = {}
        self._load_images()

        # Trouver la fenetre BlueStacks
        self.window = self._find_window()

        # Demarrer l'anti-stuck en thread
        self._stuck_thread = threading.Thread(target=self._anti_stuck_loop, daemon=True)
        self._stuck_thread.start()

        # Overlay
        if self.config["overlay_enabled"]:
            overlay_thread = threading.Thread(
                target=lambda: Overlay(lambda: self.stats).run(),
                daemon=True
            )
            overlay_thread.start()

        logger.info("DBFarmer initialisé avec succès")

    # ── Chargement des images ───────────────────────────────────

    def _load_images(self):
        missing = []
        for key, filename in IMAGE_FILES.items():
            path = os.path.join(self.image_folder, filename)
            if os.path.exists(path):
                img = cv2.imread(path)
                if img is not None:
                    self.images[key] = img
                    logger.debug(f"Image chargée: {key} ({filename})")
                else:
                    logger.warning(f"Impossible de lire l'image: {filename}")
                    missing.append(key)
            else:
                missing.append(key)

        if missing:
            logger.warning(f"Images manquantes ({len(missing)}): {missing}")
            logger.warning(f"Mets ces images dans le dossier '{self.image_folder}/'")
            logger.warning("Utilise l'outil de capture: python capture.py")
        else:
            logger.info(f"Toutes les images chargées ({len(self.images)})")

    # ── Gestion de la fenetre BlueStacks ───────────────────────

    def _find_window(self):
        name = self.config["window_name"]
        logger.info(f"Recherche de la fenetre: '{name}'")
        for _ in range(30):
            wins = pyautogui.getWindowsWithTitle(name)
            if wins:
                win = wins[0]
                logger.info(f"Fenetre trouvée: {win.title} | Pos: ({win.left},{win.top}) Taille: {win.width}x{win.height}")
                return win
            time.sleep(0.5)
        logger.error(f"Fenetre '{name}' introuvable ! Vérifie que BlueStacks est ouvert.")
        print(f"\n[ERREUR] Fenetre BlueStacks introuvable.")
        print(f"  -> Assure-toi que BlueStacks 5 est ouvert.")
        print(f"  -> Verifie 'window_name' dans config.json")
        print(f"  -> Titre actuel de tes fenetres ouvertes:")
        for w in pyautogui.getAllWindows():
            if w.title:
                print(f"     '{w.title}'")
        sys.exit(1)

    def _get_window_region(self):
        """Retourne (left, top, width, height) de la fenetre BlueStacks."""
        try:
            wins = pyautogui.getWindowsWithTitle(self.config["window_name"])
            if wins:
                w = wins[0]
                return (w.left, w.top, w.width, w.height)
        except:
            pass
        return None

    # ── Capture d'ecran ────────────────────────────────────────

    def _screenshot(self):
        """Capture uniquement la fenetre BlueStacks."""
        region = self._get_window_region()
        if region is None:
            return None
        try:
            l, t, w, h = region
            img = ImageGrab.grab(bbox=(l, t, l+w, t+h))
            return np.array(img)
        except Exception as e:
            logger.error(f"Erreur capture: {e}")
            return None

    # ── Detection d'image ──────────────────────────────────────

    def _find(self, key: str) -> tuple | None:
        """
        Cherche une image dans la fenetre BlueStacks.
        Retourne (x, y) ABSOLU sur l'ecran, ou None si pas trouve.
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
            logger.warning(f"Template {key} plus grand que l'ecran, resize...")
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
                logger.debug(f"Trouvé [{key}] confiance={max_val:.2f} pos=({abs_x},{abs_y})")
                return (abs_x, abs_y)

        return None

    def _find_with_score(self, key: str, screenshot_bgr) -> tuple[float, tuple | None]:
        """
        Cherche une image dans un screenshot déjà capturé.
        Retourne (score, coords) — coords peut être None si sous le seuil.
        Utilisé pour comparer plusieurs images sur le même screenshot.
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
        Compare plusieurs images sur le MÊME screenshot et retourne
        celle qui a le score le plus élevé.
        Évite les faux positifs entre images similaires (ex: demo vs demo_checked).
        Retourne (key_gagnante, coords) ou (None, None) si aucune trouvée.
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
            logger.debug(f"→ Gagnant: [{best_key}] score={best_score:.3f}")
            return best_key, best_coords

        return None, None

    # ── Clic ───────────────────────────────────────────────────

    def _click(self, x: int, y: int):
        """Clique a une position absolue sur l'ecran."""
        pyautogui.click(x, y)
        time.sleep(self.click_delay)
        logger.debug(f"Clic en ({x}, {y})")

    def _click_skip(self) -> bool:
        """
        Clique sur le bouton Skip par coordonnées fixes.
        Deux modes dans config.json → skip_position :

        Mode "absolute" (recommandé) :
            {"mode": "absolute", "x": 851, "y": 49}
            Coordonnées absolues sur ton écran — à mesurer une fois.

        Mode "relative" (si tu changes de résolution) :
            {"mode": "relative", "x_pct": 0.82, "y_pct": 0.06}
            Pourcentage de la ZONE DE JEU (pas la fenêtre Windows entière).
        """
        pos = self.config.get("skip_position", {"mode": "absolute", "x": 851, "y": 49})
        mode = pos.get("mode", "absolute")

        if mode == "absolute":
            x = pos["x"]
            y = pos["y"]
        else:
            # Mode relatif : calculé sur la zone de jeu réelle
            # On utilise la capture d'écran pour obtenir les vraies dimensions
            region = self._get_window_region()
            if region is None:
                logger.warning("_click_skip: fenêtre introuvable")
                return False
            l, t, w, h = region
            x = int(l + w * pos.get("x_pct", 0.82))
            y = int(t + h * pos.get("y_pct", 0.06))

        logger.info(f"Clic Skip en ({x}, {y}) [mode={mode}]")
        pyautogui.click(x, y)
        time.sleep(self.click_delay)
        return True

    # ── Attendre et cliquer ────────────────────────────────────

    def _wait_and_click(self, key: str, timeout: float = 120, delay: float = None) -> bool:
        """
        Attend indefiniment qu'un element apparaisse puis clique dessus.
        Retourne True si clique, False si timeout.
        """
        delay = delay or self.loop_delay
        self._set_action(f"Attente: {key}")
        start = time.time()
        while True:
            coords = self._find(key)
            if coords:
                self._set_action(f"Clic: {key}")
                self._click(*coords)
                return True
            if time.time() - start > timeout:
                logger.warning(f"Timeout ({timeout}s) en attendant [{key}]")
                return False
            time.sleep(delay)

    def _try_click(self, key: str, tries: int = None, delay: float = None) -> bool:
        """
        Tente de cliquer sur un element, avec un nombre limite d'essais.
        Retourne True si clique, False si echec apres tous les essais.
        """
        tries = tries or self.max_tries
        delay = delay or self.loop_delay
        for i in range(tries):
            coords = self._find(key)
            if coords:
                self._click(*coords)
                return True
            time.sleep(delay)
        logger.warning(f"[{key}] non trouvé après {tries} essais")
        return False

    # ── Selectionner l'equipe ──────────────────────────────────

    def _select_team(self):
        """
        Clique sur les 3 emplacements de personnages.
        Utilise LegendsPointer comme point de reference.
        """
        self._set_action("Sélection équipe")
        start = time.time()
        while True:
            coords = self._find("LegendsPointer")
            if coords:
                px, py = coords
                offsets = TEAM_OFFSETS
                team_y  = py + offsets["y"]
                char1_x = px - offsets["char1_x"]
                char2_x = px - offsets["char2_x"]
                char3_x = px - offsets["char3_x"]

                time.sleep(0.2)
                self._click(char1_x, team_y)
                logger.info(f"Perso 1 cliqué: ({char1_x}, {team_y})")
                self._click(char2_x, team_y)
                logger.info(f"Perso 2 cliqué: ({char2_x}, {team_y})")
                self._click(char3_x, team_y)
                logger.info(f"Perso 3 cliqué: ({char3_x}, {team_y})")
                return True

            if time.time() - start > 60:
                logger.warning("LegendsPointer introuvable, selection equipe ignoree")
                return False
            time.sleep(self.loop_delay)

    # ── Stats / status ─────────────────────────────────────────

    def _set_action(self, action: str):
        self.stats["action"] = action
        logger.info(action)

    def _set_status(self, status: str):
        self.stats["status"] = status

    # ── SETUP INITIAL (une seule fois au lancement) ────────────

    def setup(self):
        """
        Séquence de démarrage : Histoire → Continuer → Oui
        Chaque étape attend indéfiniment — si bloquée, l'anti-stuck
        (thread background) prend le relais et débloque la situation.
        """
        logger.info("="*55)
        logger.info("  SETUP INITIAL")
        logger.info("="*55)
        self._set_status("Setup")

        print("\n[DBFarmer] Attente du bouton Histoire...")

        # 1. Bouton Histoire — attend indéfiniment, anti-stuck gère les blocages
        self._set_action("Attente: StoryButton")
        while not self._find("StoryButton"):
            time.sleep(0.5)
        self._click(*self._find("StoryButton"))
        logger.info("✓ Histoire sélectionnée")

        # 2. Bouton Continuer — attend indéfiniment
        self._set_action("Attente: ContinueButton")
        while not self._find("ContinueButton"):
            time.sleep(0.5)
        self._click(*self._find("ContinueButton"))
        logger.info("✓ Continuer cliqué")

        # 3. Confirmation Oui (si nécessaire)
        time.sleep(0.5)
        self._try_click("YesButton", tries=5, delay=0.4)

        logger.info("✓ Setup terminé - la boucle prend le relais")

    # ── DETECTION DU TYPE DE NIVEAU ────────────────────────────

    def _detect_level_type(self, timeout: float = 45.0) -> str:
        """
        Détecte le type du niveau en cherchant en parallèle :
          - StartBattleButton → COMBAT
          - StorySlide        → CINEMATIQUE
          - SkipButton        → CINEMATIQUE (bouton Skip toujours présent sur les slides)

        Le premier signal trouvé gagne immédiatement.
        """
        self._set_action("Détection type de niveau...")
        logger.info("Détection du type de niveau en cours...")

        start = time.time()
        while time.time() - start < timeout:
            if self._find("StartBattleButton"):
                logger.info("→ COMBAT (StartBattleButton présent)")
                return "combat"
            if self._find("StorySlide"):
                logger.info("→ CINEMATIQUE (StorySlide présent)")
                return "story"
            if self._find("SkipButton"):
                logger.info("→ CINEMATIQUE (SkipButton présent)")
                return "story"
            time.sleep(0.3)

        logger.warning(f"Type non détecté après {timeout}s → COMBAT par défaut")
        return "unknown"

    # ── GESTION D'UN NIVEAU CINEMATIQUE (slides) ───────────────

    def _handle_story_level(self):
        """
        Niveau cinématique : Skip → Oui (confirmer skip) → Oui (niveau suivant).
        """
        logger.info("─── Gestion niveau CINEMATIQUE ───")
        self._set_status("Cinématique")

        # ── Étape 1 : Skip la cinématique ─────────────────────
        self._set_action("Skip cinématique")
        self._click_skip()
        logger.info("✓ Skip cliqué (coordonnées fixes)")

        # ── Étape 2 : Un seul Oui pour confirmer le skip ──────
        time.sleep(0.5)
        if self._wait_and_click("YesButton", timeout=15):
            logger.info("✓ Skip confirmé")
        else:
            logger.warning("YesButton non trouvé après Skip")

        self.stats["story_levels"] = self.stats.get("story_levels", 0) + 1
        return True

    # ── VERIFICATION DEMO DECOCHEE ─────────────────────────────

    def _ensure_demo_unchecked(self, timeout: float = 20.0) -> bool:
        """
        Compare demo.png (vide) et demo_checked.png (cochée) sur le MÊME screenshot.
        Celui qui a le score le plus haut = l'état réel.
        Évite les faux positifs entre les deux images similaires.

        - Gagnant = DemoCheckmark (vide)   → bon état, on lance
        - Gagnant = DemoChecked  (cochée)  → on clique pour décocher
        """
        self._set_action("Vérif Play Demo décochée...")
        start = time.time()

        while time.time() - start < timeout:
            winner, coords = self._find_best("DemoCheckmark", "DemoChecked")

            if winner == "DemoCheckmark":
                logger.info("✓ Play Demo vide (décochée) — score gagnant")
                return True

            elif winner == "DemoChecked":
                logger.info(f"Play Demo cochée — clic pour décocher en {coords}")
                self._click(*coords)
                time.sleep(0.8)
                # Revérifier avec _find_best
                winner2, _ = self._find_best("DemoCheckmark", "DemoChecked")
                if winner2 == "DemoCheckmark":
                    logger.info("✓ Play Demo décochée après clic")
                    return True
                logger.debug(f"Encore état [{winner2}], nouvel essai...")

            else:
                # Aucune trouvée → écran pas encore chargé
                time.sleep(0.4)

        logger.warning(f"Play Demo non confirmée décochée après {timeout}s")
        return False

    # ── VIDER LES TAPS EN ATTENTE ──────────────────────────────

    def _flush_taps(self, max_taps: int = 10, timeout_per_tap: float = 3.0):
        """
        Clique sur TapArrow en boucle jusqu'à ce qu'il disparaisse.
        Gère les cas où plusieurs TAP s'enchaînent :
          - Level up de personnage
          - Objectifs du niveau complétés
          - Animations diverses

        S'arrête dès que TapArrow n'est plus visible ou après max_taps clics.
        """
        taps = 0
        while taps < max_taps:
            time.sleep(0.5)
            coords = self._find("TapArrow")
            if coords:
                self._click(*coords)
                taps += 1
                logger.info(f"✓ TAP #{taps} cliqué en {coords}")
            else:
                # Plus de TAP visible → on sort
                break

        if taps > 0:
            logger.info(f"✓ {taps} TAP(s) vidé(s)")
        else:
            logger.debug("Pas de TAP en attente")

    # ── GESTION D'UN NIVEAU COMBAT ─────────────────────────────

    def _handle_combat_level(self):
        """
        Gère un niveau de combat.

        Séquence complète :
          [DemoCheckmark déjà visible à l'entrée]
          Demo → Combattre → Oui → Équipe → Prêt → Oui
          → [combat auto] →
          FinishedPointer → (TapArrow si présent) → OkBattle → (TapArrow si présent) → OkBattle
          → Oui (rejouer) → Skip cinématique éventuel → Oui
          → [retour détection prochain niveau]
        """
        logger.info("─── Gestion niveau COMBAT ───")
        self._set_status("Préparation combat")

        # ── Demo : vérifier qu'elle est DÉCOCHÉE avant de lancer ──
        self._set_action("Demo checkmark")
        if not self._ensure_demo_unchecked(timeout=20):
            logger.warning("Demo non confirmée décochée, on continue quand même")
        logger.info("✓ Demo décochée, lancement du combat")

        # Attendre que StartBattleButton soit bien chargé avant de cliquer
        self._set_action("Attente StartBattle...")
        self._wait_and_click("StartBattleButton", timeout=30)
        logger.info("✓ Combattre cliqué")

        # Oui pour confirmer la dépense d'énergie
        time.sleep(0.8)
        if not self._try_click("YesButton", tries=8, delay=0.5):
            logger.warning("YesButton non trouvé après StartBattle")

        # Sélection équipe + Prêt
        self._select_team()

        self._wait_and_click("ReadyButton", timeout=30)
        logger.info("✓ Prêt")

        time.sleep(0.5)
        if not self._try_click("YesButton", tries=8, delay=0.5):
            logger.warning("YesButton non trouvé après ReadyButton")

        # ── Attente fin de combat ──────────────────────────────
        self.in_combat = True
        self._set_status("Combat en cours")
        self._set_action("Attente fin de combat...")
        logger.info("Attente FinishedPointer...")

        combat_start = time.time()
        combat_max   = self.config["combat_timeout"]  # 600s = 10 min

        found = False
        while time.time() - combat_start < combat_max:
            if self._find("FinishedPointer"):
                self._click(*self._find("FinishedPointer"))
                found = True
                break
            # Après 10 min sans FinishedPointer → réactiver l'anti-stuck
            if time.time() - combat_start >= combat_max:
                break
            time.sleep(self.loop_delay)

        self.in_combat = False

        if not found:
            logger.warning(f"FinishedPointer non trouvé après {combat_max}s → anti-stuck réactivé, récupération")
            return False
        logger.info("✓ Combat terminé")

        # ── Écran de résultats ─────────────────────────────────
        # Séquence complète :
        # [TAP x N si level up / objectifs] → OkBattle → [TAP x N] → OkBattle
        self._set_action("Écran de résultats")
        for step in range(2):
            # Vider tous les TAP en attente avant chaque OkBattle
            self._flush_taps()
            # Ensuite cliquer OkBattle
            self._wait_and_click("OkBattleButton", timeout=20)
            logger.info(f"✓ OkBattle étape {step+1}")

        # ── Confirmation rejouer ───────────────────────────────
        self._set_action("Confirmation rejouer")
        time.sleep(0.8)   # Laisser l'écran de confirmation apparaître
        self._wait_and_click("YesButton", timeout=30)
        logger.info("✓ Rejouer confirmé")

        # ── Fin : retour à la détection du prochain niveau ────
        logger.info("✓ Combat géré, retour détection prochain niveau")
        return True

    # ── BOUCLE PRINCIPALE ──────────────────────────────────────

    def loop(self):
        """
        Boucle infinie : détecte le type de niveau → gère → recommence.
        """
        logger.info("="*55)
        logger.info("  BOUCLE DE FARMING DÉMARRÉE")
        logger.info("="*55)
        self._set_status("Farming")

        while True:
            try:
                level_type = self._detect_level_type(timeout=45)

                if level_type == "story":
                    logger.info("★ Niveau CINÉMATIQUE")
                    success = self._handle_story_level()
                    if success:
                        self.stats["completed"] += 1
                        logger.info(f"✓✓ Cinématique terminée | Total: {self.stats['completed']}")
                    else:
                        logger.warning("Cinématique échouée → récupération")
                        self._recover_to_menu()

                elif level_type == "combat":
                    logger.info("★ Niveau COMBAT")
                    success = self._handle_combat_level()
                    if success:
                        self.stats["loops"]     += 1
                        self.stats["completed"] += 1
                        logger.info(f"✓✓ Combat terminé | Combats: {self.stats['loops']} | Total: {self.stats['completed']}")
                    else:
                        logger.warning("Combat échoué → récupération")
                        self._recover_to_menu()

                elif level_type == "unknown":
                    logger.warning("Type inconnu après timeout → récupération vers menu")
                    self._recover_to_menu()

                time.sleep(0.5)

            except KeyboardInterrupt:
                logger.info("Arrêt demandé (CTRL+C)")
                print("\n[DBFarmer] Arrêt. Stats finales:")
                print(f"  Total complétés  : {self.stats['completed']}")
                print(f"    Combats        : {self.stats['loops']}")
                print(f"    Cinématiques   : {self.stats.get('story_levels', 0)}")
                print(f"  Anti-stuck fixes : {self.stats['stuck_fixed']}")
                print(f"  Récupérations   : {self.stats.get('recoveries', 0)}")
                sys.exit(0)

            except Exception as e:
                logger.error(f"Erreur dans la boucle: {e}", exc_info=True)
                time.sleep(3)

    # ── RECUPERATION VERS LE MENU ──────────────────────────────

    def _recover_to_menu(self, max_backs: int = 15) -> bool:
        """
        Tente de revenir au menu principal en utilisant :
          1. BackButton  → bouton retour du jeu (priorité max)
          2. HomeButton  → visible = on clique = amène directement à l'accueil
          3. Echap       → si aucun bouton du jeu trouvé

        S'arrête dès que StoryButton ou HomeButton sont visibles.
        Une fois sur l'accueil, relance setup().
        """
        logger.warning("═══ RÉCUPÉRATION VERS LE MENU ═══")
        self._set_status("Récupération...")
        self.stats["recoveries"] = self.stats.get("recoveries", 0) + 1

        for attempt in range(max_backs):

            # ── On est sur l'accueil → relancer setup ─────────
            if self._find("StoryButton"):
                logger.info("✓ StoryButton visible → accueil atteint")
                time.sleep(1.0)
                self.setup()
                return True

            # ── HomeButton visible → un clic ramène à l'accueil
            home = self._find("HomeButton")
            if home:
                logger.info(f"✓ HomeButton visible → clic en {home}")
                self._click(*home)
                time.sleep(1.5)
                logger.info("✓ Accueil atteint via Home → relance setup")
                self.setup()
                return True

            # ── BackButton visible → reculer d'un écran ───────
            back = self._find("BackButton")
            if back:
                logger.info(f"Retour #{attempt+1} via BackButton en {back}")
                self._click(*back)
                time.sleep(1.2)

                # Fermer popup éventuel
                close = self._find("CloseButton")
                if close:
                    self._click(*close)
                    time.sleep(0.8)

                # TAP popup éventuel
                tap = self._find("TapArrow")
                if tap:
                    self._click(*tap)
                    time.sleep(0.8)

                # Refuser confirmation éventuelle
                no = self._find("NoButton")
                if no:
                    self._click(*no)
                    time.sleep(0.8)

                continue

            # ── Aucun bouton du jeu trouvé → Echap ────────────
            logger.info(f"Retour #{attempt+1} via Echap (aucun bouton trouvé)")

            # TAP popup avant Echap
            tap = self._find("TapArrow")
            if tap:
                self._click(*tap)
                time.sleep(0.8)

            pyautogui.press("escape")
            time.sleep(1.2)

        logger.error("Impossible de revenir au menu après plusieurs tentatives")
        return False

    # ── ANTI-STUCK (thread background) ────────────────────────

    def _anti_stuck_loop(self):
        """
        Toutes les X secondes, compare 2 screenshots.
        Si identiques -> le jeu est bloque -> clic intelligent sur le bouton prioritaire.
        """
        time.sleep(5)  # Attendre que le jeu soit lance
        logger.info("Anti-stuck démarré (thread background)")

        while True:
            try:
                old_ss = self._screenshot()
                time.sleep(self.config["anti_stuck_delay"])
                new_ss = self._screenshot()

                if old_ss is None or new_ss is None:
                    continue

                # Ne pas interférer pendant un combat
                if self.in_combat:
                    logger.debug("Anti-stuck en pause (combat en cours)")
                    continue

                # Comparer les deux screenshots
                diff = cv2.absdiff(
                    cv2.cvtColor(old_ss, cv2.COLOR_RGB2GRAY),
                    cv2.cvtColor(new_ss, cv2.COLOR_RGB2GRAY)
                )
                diff_score = np.sum(diff)

                # ── Vérification écran hors contexte ──────────
                # Même si l'écran bouge (animations shop etc.), on vérifie
                # qu'on est bien sur un écran attendu par le bot.
                # Si ni StartBattleButton ni StorySlide ni SkipButton ni StoryButton
                # ne sont visibles → on est perdu → récupération immédiate.
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
                ])

                if not on_known_screen:
                    logger.warning("Anti-stuck: écran non reconnu (shop, popup, etc.) → récupération")
                    self._set_status("Anti-stuck: récupération")
                    self.stats["stuck_fixed"] += 1
                    self._recover_to_menu()
                    continue

                if diff_score < 50000:  # Ecran quasiment identique = stuck
                    logger.warning(f"Stuck détecté! diff={diff_score}")
                    self._set_status("Anti-stuck actif")

                    # Chercher le bouton le plus prioritaire
                    best_key  = None
                    best_prio = -1
                    for key, prio in sorted(PRIORITY_LIST.items(), key=lambda x: -x[1]):
                        coords = self._find(key)
                        if coords:
                            if prio > best_prio:
                                best_prio = prio
                                best_key  = key
                                best_coords = coords

                    if best_key:
                        logger.info(f"Anti-stuck: clic sur [{best_key}] prio={best_prio}")
                        self._click(*best_coords)
                        self.stats["stuck_fixed"] += 1
                    else:
                        logger.warning("Anti-stuck: aucun bouton trouvé, appui sur Echap")
                        pyautogui.press("escape")

                    self._set_status("Farming")
                else:
                    logger.debug(f"Anti-stuck OK, diff={diff_score}")

            except Exception as e:
                logger.error(f"Erreur anti-stuck: {e}")
                time.sleep(5)

    # ── POINT D'ENTREE ─────────────────────────────────────────

    def run(self):
        print("="*55)
        print("  DBFarmer v2.0 - Dragon Ball Legends")
        print("  Adapté pour BlueStacks 5")
        print("="*55)
        print()
        print(f"  Config       : {CONFIG_PATH}")
        print(f"  Images       : {self.image_folder}/")
        print(f"  Log          : {log_file}")
        print(f"  Fenetre      : {self.config['window_name']}")
        print(f"  Confiance    : {self.confidence}")
        print()
        print("  Lance le jeu, va sur le menu principal")
        print("  et assure-toi que l'equipe est deja configuree.")
        print()
        print("  CTRL+C pour arreter a tout moment.")
        print("="*55)
        print()

        # Activer la fenetre BlueStacks
        try:
            self.window.activate()
            self.window.maximize()
        except:
            logger.warning("Impossible d'activer/maximiser la fenetre (mode fenetre?)")

        self.setup()
        self.loop()

# ─────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────

if __name__ == "__main__":
    pyautogui.FAILSAFE = True   # Souris en coin haut-gauche = arret d'urgence
    pyautogui.PAUSE    = 0.05
    pyautogui.useImageNotFoundException(False)

    farmer = DBFarmer()
    farmer.run()
