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
- `src/ui/attack_fx.py` : animations d'attaque dessinées par le code (un style par type).
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
Effets **originaux, dessinés par le code** (aucun asset tiers) dans `src/ui/attack_fx.py` : une coupe en croissant pour
la mêlée, une onde de choc avec éclats pour les zones, une orbe à traînée pour les projectiles (qui finit en impact),
et un flash sur la cible touchée (plus gros si super efficace). Chaque type a sa palette et sa forme d'éclat : flammes,
gouttes, feuilles, éclairs, éclats de glace, bulles, rochers, volutes spectrales, étoiles de fée... Les attaques ennemies
ont un liseré rouge pour qu'on les repère. Les animations vivent plus longtemps que les hitbox (très brèves).

## Niveaux, évolutions et capacités réelles
On démarre au niveau 10. Chaque ennemi vaincu rapporte `expérience de base de l'espèce x son niveau / 7` (comme dans les jeux) ;
les courbes d'expérience sont les vraies (taux de croissance). Les starters **évoluent au niveau 16 puis au niveau 36**
(Sprigatito → Floragato → Meowscarada, Fuecoco → Crocalor → Skeledirge, Quaxly → Quaxwell → Quaquaval) avec l'écran
d'évolution des jeux : nouveaux types, sprite, stats (rapport des vraies stats de base) et capacités. Chaque niveau
donne +2,5 % de stats et +3,5 % de PV ; les ennemis gagnent +10 % de PV par salle.

Les capacités sont de **vraies capacités apprises par chaque forme** dans Écarlate/Violet, débloquées à leur niveau d'apprentissage
réel (par exemple Canon Graine au niveau 20 pour Floragato), sans aucune capacité partagée entre deux lignées. Type, catégorie,
puissance, PP et priorité viennent de la base ; le jeu choisit seulement la forme (mêlée, coup large, zone, projectile). Les capacités
« qui ne ratent jamais » sont à tête chercheuse (Feuille Magik, Magie Florale), Tranch'Aqua et Lame d'Air traversent les ennemis,
Chant Flamboyant et Danse Aquatique donnent un bonus cumulable (Atq. Spé. / vitesse), Magie Florale est toujours critique.

### Sources de données
- [pokemondb/database](https://github.com/pokemondb/database) : types, stats de base, taux de croissance, expérience de base et chiffres de chaque capacité.
  Elle ne contient ni capacités apprises, ni évolutions, ni noms français ; son `pokemon-forms.yaml` est mal formé (ligne 31354), l'outil
  d'import ne lit donc que les blocs utiles.
- [PokeAPI/pokeapi](https://github.com/PokeAPI/pokeapi) (CSV) : capacités apprises par niveau dans Écarlate/Violet, noms français, niveaux d'évolution.
Régénérer : `python -m tools.import_pokemon_data` (réseau + PyYAML) ; le jeu, lui, n'a besoin ni de l'un ni de l'autre.
