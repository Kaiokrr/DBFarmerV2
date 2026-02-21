"""
DBFarmer v2 - Installation automatique des dependances
Lance: python install.py
"""
import os
import sys
import subprocess

LIBRARIES = [
    "pyautogui",
    "opencv-python",
    "pillow",
    "numpy",
    "pygetwindow",
]

print("="*50)
print("  DBFarmer v2 - Installation des dependances")
print("="*50)
print()

all_ok = True
for lib in LIBRARIES:
    try:
        import_name = lib.replace("-", "_").replace("opencv_python", "cv2").replace("pillow", "PIL")
        __import__(import_name)
        print(f"  ✓ {lib} (deja installe)")
    except ImportError:
        print(f"  → Installation de {lib}...", end=" ", flush=True)
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", lib, "-q"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("OK")
        else:
            print(f"ECHEC!\n    {result.stderr.strip()}")
            all_ok = False

print()
if all_ok:
    print("  ✓ Toutes les dependances sont installees!")
    print()
    print("  Etapes suivantes:")
    print("  1. Lance: python capture.py   -> capturer les boutons du jeu")
    print("  2. Lance: python main.py      -> demarrer le bot")
else:
    print("  ✗ Certaines dependances n'ont pas pu etre installees.")
    print("    Installe-les manuellement avec pip.")

print()
input("Appuie sur Entree pour continuer...")
