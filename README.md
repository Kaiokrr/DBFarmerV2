# DBFarmer v2 🐉
**Dragon Ball Legends - Story Farmer pour BlueStacks 5**  
Basé sur le projet original de LUXTACO, modernisé et adapté.

---

## ⚡ Installation rapide

### 1. Double-clique sur `start.bat` → choix 1 (installer les dépendances)

Ou manuellement dans un terminal :
```
pip install pyautogui opencv-python pillow numpy pygetwindow
```

---

## 📸 Étape 1 : Capturer les boutons

Lance `start.bat` → choix 2, ou :
```
python capture.py
```

Une interface s'ouvre. Pour chaque bouton dans la liste :
1. Sélectionne-le dans la liste
2. Clique sur **"Capturer (Sélection zone)"**
3. La fenêtre se cache → dessine un rectangle autour du bouton dans le jeu
4. La zone est sauvegardée automatiquement ✓

### Boutons à capturer (16 au total) :

| Image | Description |
|-------|-------------|
| `menu.png` | Bouton menu/maison sur l'écran principal |
| `story.png` | Bouton "Histoire" |
| `continue.png` | Bouton "Continuer" (reprendre la quête) |
| `yes.png` | Bouton "Oui" / confirmation |
| `no.png` | Bouton "Non" |
| `demo.png` | Case "Combat démo" / auto-battle |
| `startbattle.png` | Bouton "Combattre" |
| `legendspointer.png` | Zone de référence pour l'équipe |
| `ready.png` | Bouton "Prêt" |
| `finishedpointer.png` | Indicateur fin de combat |
| `tap.png` | Flèche "Appuyer pour continuer" |
| `okbattle.png` | Bouton "OK" résultats |
| `skip.png` | Bouton "Skip" (cinématiques) |
| `storyslide.png` | ⭐ Indicateur de slide d'histoire (boite de dialogue, fond avec texte narratif) |
| `slidetap.png` | ⭐ Icône ou zone "Appuyer pour continuer" sur un slide |
| `nextlevel.png` | ⭐ Bouton "Niveau suivant" / flèche après un niveau cinématique fini |
| `arrow.png` | Flèche de navigation |
| `close.png` | Bouton X (fermer popup) |
| `mission.png` | Le stage à sélectionner |

> ⭐ = Nouvelles images pour la gestion des niveaux cinématiques (slides d'histoire sans combat)

> **Conseil** : Capture les images avec le jeu en mode fenêtré (pas plein écran) pour de meilleurs résultats.

---

## 🎬 Niveaux cinématiques (slides d'histoire)

Certains niveaux du mode histoire n'ont **pas de combat** : ce sont des slides de dialogue ou de narration. Le bot détecte automatiquement ce type de niveau et :

1. Tape en boucle sur les slides pour les faire avancer
2. Utilise le bouton **Skip** si disponible pour accélérer
3. Clique sur **Niveau suivant** une fois les slides terminés

Pour que cela fonctionne, tu dois capturer :
- `storyslide.png` : n'importe quel élément qui apparaît **uniquement** sur les slides (ex: la boite de dialogue en bas, le fond spécifique, un personnage narrateur)
- `slidetap.png` : l'icône "appuyer" si elle est distincte
- `nextlevel.png` : le bouton pour passer au niveau suivant après les slides

---

## 🤖 Étape 2 : Lancer le bot

```
python main.py
```
ou `start.bat` → choix 3.

Avant de lancer :
- ✅ BlueStacks 5 est ouvert
- ✅ Le jeu est sur le **menu principal** (pas en combat)
- ✅ Ton équipe est déjà configurée dans le jeu
- ✅ Tu as de l'énergie/stamina pour jouer

**CTRL+C** pour arrêter le bot à tout moment.  
**Souris en coin haut-gauche** = arrêt d'urgence (failsafe pyautogui).

---

## ⚙️ Configuration (config.json)

| Paramètre | Défaut | Description |
|-----------|--------|-------------|
| `window_name` | `BlueStacks App Player` | Titre de la fenêtre BlueStacks |
| `confidence` | `0.75` | Seuil de détection d'image (0.5–0.95) |
| `loop_delay` | `1.0` | Délai entre chaque vérification (sec) |
| `click_delay` | `0.5` | Délai après un clic (sec) |
| `anti_stuck_delay` | `60.0` | Fréquence de l'anti-stuck (sec) |
| `combat_timeout` | `600` | Timeout max d'un combat (sec) |
| `overlay_enabled` | `true` | Afficher l'overlay d'info |

### Trouver le bon `window_name` :
Si BlueStacks ne se trouve pas, lance `python main.py` et il te listera toutes les fenêtres ouvertes.

---

## 🛡 Fonctionnalités

- **Detection par image** : OpenCV template matching (plus fiable que l'original)
- **Anti-stuck** : Compare 2 screenshots toutes les 60s, clic intelligent si bloqué
- **Overlay** : Fenêtre info en temps réel (draggable)
- **Logs** : Fichier log par session dans le dossier `logs/`
- **Failsafe** : Souris coin haut-gauche = arrêt immédiat

---

## ❓ Problèmes courants

**"Fenêtre BlueStacks introuvable"**  
→ Vérifie que BlueStacks 5 est ouvert et cherche le bon titre dans la liste affichée.

**Le bot clique au mauvais endroit**  
→ Refais la capture de cette image avec `python capture.py`.

**La détection est trop sensible / pas assez**  
→ Ajuste `confidence` dans `config.json` (augmenter = plus strict, diminuer = plus souple).

**Le bot se bloque**  
→ L'anti-stuck devrait corriger automatiquement. Sinon CTRL+C et relance.
