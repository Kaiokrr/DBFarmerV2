"""
DBFarmer v2 - Automatic dependency installer
Run: python install.py
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
print("  DBFarmer v2 - Installing dependencies")
print("="*50)
print()

all_ok = True
for lib in LIBRARIES:
    try:
        import_name = lib.replace("-", "_").replace("opencv_python", "cv2").replace("pillow", "PIL")
        __import__(import_name)
        print(f"  ✓ {lib} (already installed)")
    except ImportError:
        print(f"  → Installing {lib}...", end=" ", flush=True)
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", lib, "-q"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            print("OK")
        else:
            print(f"FAILED!\n    {result.stderr.strip()}")
            all_ok = False

print()
if all_ok:
    print("  ✓ All dependencies installed!")
    print()
    print("  Returning to menu in 3 seconds...")
else:
    print("  ✗ Some dependencies could not be installed.")
    print("    Install them manually with pip.")
    print()
    print("  Returning to menu in 5 seconds...")

import time
time.sleep(3 if all_ok else 5)
