# Pokémon × Hades (prototype Pygame)

## Lancer
```
pip install -r requirements.txt
python main.py                 # partie : salles + Rattata
python main.py --training      # mannequins d'entraînement (phase 2)
python main.py --room 5        # démarre directement à la salle 5 (premier boss)
python -m tests.test_dash      # tests headless du déplacement / dash
python -m tests.test_combat    # tests headless table des types / dégâts
python -m tests.test_rooms     # tests headless ennemis / salles / portes
python -m tests.test_items     # tests headless modificateurs / récompenses
python -m tests.test_ui        # tests headless menus (navigation, pause, rendu)
python -m tests.test_sprites   # tests headless sprites (découpage, animations, crédits)
python -m tests.test_content   # tests headless starters, ennemis, mort, icônes de type
python -m tests.test_bosses    # tests headless obstacles, navigation, boss
python -m tests.test_fx        # tests headless animations d'attaque
python -m tests.test_progression  # tests headless niveaux, évolutions, capacités réelles
python -m tests.test_moves     # tests headless effets réels des capacités
```
Au lancement, on choisit son starter (Sprigatito, Fuecoco ou Quaxly). Contrôles : ZQSD / WASD / flèches = bouger · Espace / Maj / clic droit = Dash · clic gauche / E / R = attaques · Échap = menu pause (Reprendre / Statut / Quitter).

## Architecture
- `src/settings.py` : constantes (vitesse, durée du dash, i-frames, cooldown…).
- `src/game.py` : boucle 60 FPS ; seul endroit qui lit le clavier et le traduit en `Intent`.
- `src/entities/` : `Entity` (base), `Player` (données + rendu), `PlayerController` (logique move/dash).
- `src/combat/` : (phase 2) types, attaques, dégâts.
- `src/levels/` : (phase 3) salles, RoomManager.
- `src/items/` : modificateurs passifs (`on_attack` / `on_update` / `on_pickup`) et catalogue de récompenses.
- `src/geometry.py` : collisions cercle/rectangle.
- `src/levels/obstacles.py` : rochers, navigation (BFS) et générateur de dispositions.
- `src/entities/boss.py` : boss à phases (Onix, Ectoplasma) et zones de danger annoncées.
- `src/starters.py` : les 3 lignées de starters (9 formes) avec leurs vraies capacités ; STAB x1,5 pour les capacités de son type.
- `src/progression.py` : niveaux, expérience (vraies courbes), mise à l'échelle des stats et des ennemis.
- `src/data/pokedex.py` : données Pokémon **générées** (`python -m tools.import_pokemon_data`).
- `src/ui/evolution.py` : écran d'évolution.
- `src/species.py` : espèces utilisées (n° de Pokédex) : Évoli (joueur), Rattata, mannequins.
- `src/ui/attack_fx.py` : moteur d'animations d'attaque dessinées par le code (style par type, flash d'impact).
- `src/ui/move_fx.py` : une animation propre à chacune des 42 capacités apprises, d'après leur description officielle.
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

## Salles à obstacles
Dès la salle 2, la salle reçoit une disposition aléatoire : piliers, rochers, murs à passages, gros blocs (`LAYOUTS`).
Chaque disposition est validée : zone des portes et point d'arrivée dégagés, tout le sol atteignable.
Les rochers bloquent le joueur (dash compris), les ennemis terrestres et **tous les projectiles** (ils servent d'abris
contre Fantominus ou les boss) ; Zubat et Fantominus volent au-dessus. Les ennemis terrestres contournent les murs
(navigation par BFS depuis le joueur, recalculée 5 fois par seconde).

## Boss
Une salle de boss toutes les 5 salles (`BOSS_EVERY`), les boss alternent et gagnent 60 % de PV à chaque cycle.
Chacun a 3 phases (à 60 % et 30 % de PV) et ses attaques sont **annoncées au sol** en rouge avant de frapper :
- **Onix** (Roche/Sol, Déf x2,2) : Jets de pierres, Séisme (grande zone, à fuir ou à traverser en dash), Charge en
  ligne droite, Éboulements ; invoque des Racaillou.
- **Ectoplasma** (Spectre/Poison, vole) : volées et anneau de Ball'Ombre, téléportation + Poing Ombre, bombes
  toxiques ; invoque des Fantominus. Normal est sans effet sur lui.
Vaincre un boss rend la moitié des PV.

## Animations d'attaque
Effets **originaux, dessinés par le code** (aucun asset tiers). `src/ui/attack_fx.py` fournit le moteur (coupe, onde, projectile à
traînée, flash d'impact, style de couleur par type) ; `src/ui/move_fx.py` donne à **chacune des 42 capacités apprises** son propre motif,
conçu d'après sa description officielle française : Griffe = trois griffures, Morsure = deux rangées de canines qui se referment,
Léchouille = grand coup de langue, Vive-Attaque / Aqua-Jet = traînée de vitesse (voile d'eau pour Aqua-Jet), Cru-Ailes = deux ailes
déployées, Câlinerie = nuage de bagarre et cœurs, Close Combat = rafale de coups, Aquatacle = enveloppé d'eau puis vague, Danse
Aquatique = ondulations et bulles, Chant Canon = notes de musique, Mégaphone = anneaux d'écho, Aboiement = arcs sonores sombres,
Calcination = flammes qui calcinent la zone, Feuille Magik = feuilles multicolores qui poursuivent, Canon Graine = déluge de graines,
Tempête Verte = tourbillon de feuilles, Magie Florale = bouquet piégé qui éclate en pétales, Lance-Flammes = torrent de flammes,
Déflagration = étoile de feu, Chant Flamboyant = notes enflammées, Tranch'Aqua / Lame d'Air = lames en croissant, etc.
Les capacités des ennemis et des boss gardent les animations génériques (liseré rouge pour les repérer).
