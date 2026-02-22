# DBFarmer v2 🐉
**Dragon Ball Legends - Story Mode Farmer pour BlueStacks 5**

Fork modernisé du projet original de [LUXTACO](https://github.com/LUXTACO/DBFarmer), entièrement réécrit pour BlueStacks 5 et la version actuelle du jeu.

---

## ✨ Changements vs l'original

- ✅ Compatible **BlueStacks 5** (La fenêtre de BS doit s'appeler "Bluestacks App Player")
- ✅ Détection par **OpenCV** template matching (plus précis que pyautogui seul)
- ✅ Gestion automatique des **niveaux cinématiques** (slides sans combat)
- ✅ Détection intelligente du type de niveau (combat ou cinématique)
- ✅ Vérification de l'état de la case **Play Demo** avant chaque combat
- ✅ Gestion des **TAP multiples** après combat (level up, objectifs)
- ✅ **Overlay** temps réel avec stats et logs (draggable)
- ✅ **Anti-stuck** par comparaison de pixels
- ✅ Outil de **capture d'images** intégré (`capture.py`)
- ✅ Suppression de la dépendance Discord
- ✅ Logs par session dans le dossier `logs/`

---

## ⚡ Installation rapide

Double-clique sur `start.bat` → choix **1** (installer les dépendances)

Ou manuellement :
```
pip install pyautogui opencv-python pillow numpy pygetwindow
```

---

## 📸 Étape 1 : Capturer les boutons

Lance `start.bat` → choix **2**, ou :
```
python capture.py
```

Une interface graphique s'ouvre. Pour chaque bouton :
1. Sélectionne-le dans la liste
2. Clique sur **"Capturer (Sélection zone)"**
3. La fenêtre se cache → dessine un rectangle autour du bouton dans le jeu
4. La zone est sauvegardée automatiquement ✓

### Boutons à capturer :

| Image | Description |
|-------|-------------|
| `story.png` | Bouton "Histoire" sur l'écran d'accueil |
| `continue.png` | Bouton "Continuer" (reprendre la quête) |
| `yes.png` | Bouton "Oui" / confirmation |
| `no.png` | Bouton "Non" |
| `demo.png` | Case **"Play Demo" vide** (décochée — état requis pour lancer le combat auto) |
| `demo_checked.png` | Case **"Play Demo" cochée** (avec la coche jaune — le bot la décochera) |
| `startbattle.png` | Bouton "Start Battle" / "Combattre" |
| `legendspointer.png` | Zone de référence pour la sélection de l'équipe |
| `ready.png` | Bouton "Prêt" / "Ready" |
| `finishedpointer.png` | Indicateur de fin de combat |
| `tap.png` | Bouton "TAP" / flèche après combat (level up, objectifs) |
| `okbattle.png` | Bouton "OK" sur l'écran de résultats |
| `storyslide.png` | Indicateur de slide d'histoire (boite de dialogue, fond narratif) |
| `arrow.png` | Flèche de navigation générale |
| `close.png` | Bouton X (fermer un popup) |
| `mission.png` | Le stage/niveau à sélectionner |

> **Note** : `demo.png` et `demo_checked.png` sont déjà inclus dans le dossier `images/` — pas besoin de les recapturer.

> **Conseil** : Capture les images avec BlueStacks en mode **fenêtré** (pas plein écran).

---

## ⚙️ Configurer le Skip (important)

Le bouton **Skip** des cinématiques est cliqué par coordonnées fixes (plus fiable que la détection image). Tu dois mesurer sa position **une seule fois** :

1. Lance le jeu sur un niveau cinématique (slide visible avec le bouton Skip)
2. Dans un terminal Python :
```python
import pyautogui, time
time.sleep(3)
print(pyautogui.position())
```
3. Dans les 3 secondes, place ta souris **sur le bouton Skip**
4. Note les coordonnées affichées et mets-les dans `config.json` :

```json
"skip_position": {
    "mode": "absolute",
    "x": 1120,
    "y": 70
}
```

---

## 🤖 Étape 2 : Lancer le bot

```
python main.py
```
ou `start.bat` → choix **3**.

Avant de lancer :
- ✅ BlueStacks 5 est ouvert en mode **plein écran**
- ✅ Le jeu est sur l'**écran d'accueil** (pas en combat)
- ✅ Tu as de l'énergie pour jouer

**CTRL+C** pour arrêter proprement.  
**Souris en coin haut-gauche** = arrêt d'urgence (failsafe pyautogui).

---

## 🔄 Fonctionnement

### Séquence de démarrage (une fois)
```
Accueil → Histoire → Continuer → Oui
```

### Boucle principale
Le bot détecte automatiquement le type de chaque niveau :

**Niveau COMBAT** :
```
Vérif Play Demo décochée → Start Battle → Oui → Équipe → Prêt → Oui
→ [combat auto] →
FinishedPointer → TAP(s) si level up → OK → TAP(s) → OK → Oui (rejouer)
→ [prochain niveau]
```

**Niveau CINÉMATIQUE** (slides sans combat) :
```
Skip → Oui
```

---

## ⚙️ Configuration (config.json)

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `window_name` | `BlueStacks App Player` | Titre de la fenêtre BlueStacks |
| `confidence` | `0.75` | Seuil de détection OpenCV (0.5–0.95) |
| `click_delay` | `0.5` | Délai après chaque clic (sec) |
| `anti_stuck_delay` | `60.0` | Fréquence de l'anti-stuck (sec) |
| `combat_timeout` | `600` | Timeout max d'un combat (sec) |
| `overlay_enabled` | `true` | Afficher l'overlay |
| `skip_position` | `x:1120, y:70` | Coordonnées absolues du bouton Skip |

---

## ❓ Problèmes courants

**"Fenêtre BlueStacks introuvable"**  
→ Vérifie que BlueStacks 5 est ouvert. Lance `python main.py` pour voir la liste des fenêtres et ajuste `window_name` dans `config.json`.

**Le bot lance le combat alors que Play Demo est cochée**  
→ Recapture `demo.png` (case vide) et `demo_checked.png` (case avec coche jaune) en incluant le texte "Play Demo" dans la sélection.

**Le Skip ne clique pas au bon endroit**  
→ Mesure les coordonnées exactes du bouton Skip et mets-les dans `config.json` → `skip_position`.

**La détection est trop sensible / pas assez**  
→ Ajuste `confidence` dans `config.json` (augmenter = plus strict, diminuer = plus souple).

**Le bot se bloque**  
→ L'anti-stuck se déclenche automatiquement toutes les 60s. Sinon CTRL+C et relance.

---

## 📦 Dépendances

- Python 3.8+
- pyautogui
- opencv-python
- pillow
- numpy
- pygetwindow

---

## 🙏 Crédits

Basé sur [DBFarmer](https://github.com/LUXTACO/DBFarmer) de **LUXTACO**.
