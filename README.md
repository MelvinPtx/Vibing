# Pokémon × Hades (prototype Pygame)

## Lancer
```
pip install -r requirements.txt
python main.py                 # partie : salles + Rattata
python main.py --training      # mannequins d'entraînement (phase 2)
python -m tests.test_dash      # tests headless du déplacement / dash
python -m tests.test_combat    # tests headless table des types / dégâts
python -m tests.test_rooms     # tests headless ennemis / salles / portes
```
Contrôles : ZQSD / WASD / flèches = bouger · Espace / Maj / clic droit = Dash · Échap = quitter.

## Architecture
- `src/settings.py` : constantes (vitesse, durée du dash, i-frames, cooldown…).
- `src/game.py` : boucle 60 FPS ; seul endroit qui lit le clavier et le traduit en `Intent`.
- `src/entities/` : `Entity` (base), `Player` (données + rendu), `PlayerController` (logique move/dash).
- `src/combat/` : (phase 2) types, attaques, dégâts.
- `src/levels/` : (phase 3) salles, RoomManager.
- `src/ui/` : HUD / menus.
