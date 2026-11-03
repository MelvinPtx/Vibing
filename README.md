# Pokémon × Hades (prototype Pygame)

## Lancer
```
pip install -r requirements.txt
python main.py                 # partie : salles + Rattata
python main.py --training      # mannequins d'entraînement (phase 2)
python -m tests.test_dash      # tests headless du déplacement / dash
python -m tests.test_combat    # tests headless table des types / dégâts
python -m tests.test_rooms     # tests headless ennemis / salles / portes
python -m tests.test_items     # tests headless modificateurs / récompenses
python -m tests.test_ui        # tests headless menus (navigation, pause, rendu)
python -m tests.test_sprites   # tests headless sprites (découpage, animations, crédits)
python -m tests.test_content   # tests headless starters, ennemis, mort, icônes de type
```
Au lancement, on choisit son starter (Sprigatito, Fuecoco ou Quaxly). Contrôles : ZQSD / WASD / flèches = bouger · Espace / Maj / clic droit = Dash · clic gauche / E / R = attaques · Échap = menu pause (Reprendre / Statut / Quitter).

## Architecture
- `src/settings.py` : constantes (vitesse, durée du dash, i-frames, cooldown…).
- `src/game.py` : boucle 60 FPS ; seul endroit qui lit le clavier et le traduit en `Intent`.
- `src/entities/` : `Entity` (base), `Player` (données + rendu), `PlayerController` (logique move/dash).
- `src/combat/` : (phase 2) types, attaques, dégâts.
- `src/levels/` : (phase 3) salles, RoomManager.
- `src/items/` : modificateurs passifs (`on_attack` / `on_update` / `on_pickup`) et catalogue de récompenses.
- `src/starters.py` : les 3 starters (types, stats, capacités propres) ; STAB x1,5 pour les capacités de son type.
- `src/species.py` : espèces utilisées (n° de Pokédex) : Évoli (joueur), Rattata, mannequins.
- `src/ui/sprites.py` : sprites animés PMD (8 directions, Idle/Walk/Attack/Swing/Shoot/Hurt).
- `src/ui/` : interface au style Pokémon Écarlate/Violet : `theme.py` (palette, bandeaux, curseur, jauges, pastilles de type), `hud.py`, `reward_menu.py`, `pause_menu.py` (menu + statut), `room_view.py`.

## Sprites et licence
Les sprites viennent de [PMDCollab/SpriteCollab](https://github.com/PMDCollab/SpriteCollab)
([sprites.pmdcollab.org](https://sprites.pmdcollab.org/)), **CC BY-NC 4.0 : usage non commercial uniquement,
avec attribution** (voir `assets/sprites/CREDITS.md`). Les Pokémon sont © Nintendo / Creatures Inc. / GAME FREAK inc. ;
ce projet est un prototype de fan sans but lucratif.

Ceux des 8 espèces du jeu sont déjà dans `assets/sprites/`. Pour en ajouter (n° de Pokédex national) :
```
python -m tools.fetch_sprites 25 6     # Pikachu, Dracaufeu... (crédits mis à jour automatiquement)
```
Sans sprite pour une espèce, le jeu retombe sur un simple cercle coloré.

## Ennemis
Rattata (poursuite), Zubat (zigzag), Racaillou (lent, Déf x2, charge), Fantominus (garde ses distances, tire des
Ball'Ombre typées : le dash les esquive), Voltorbe (mèche puis explosion de zone, désamorçable en le tuant).
Ils apparaissent progressivement selon le numéro de salle (`ENEMY_TABLE` dans `src/levels/room.py`).
À leur mort : flash, éclats colorés selon le type, puis animation « Faint » (ou écrasement si l'espèce n'en a pas).

## Icônes de type
`assets/icons/types/` : 18 icônes rondes (128 px), découpées depuis une planche fournie pour le projet
(auteur d'origine non renseigné ; usage non commercial, prototype de fan). Elles servent dans les pastilles de
type, le HUD, l'écran de choix du starter et le statut.
