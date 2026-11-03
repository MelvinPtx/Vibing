"""Constantes globales (aucune logique ici)."""

# Fenêtre / boucle
SCREEN_W, SCREEN_H = 1024, 720
FPS = 60
TITLE = "Pokémon : Hades-like (prototype)"

# Couleurs
BG = (24, 26, 36)
FLOOR = (38, 42, 58)
WALL = (70, 76, 100)
WHITE = (240, 240, 240)
YELLOW = (250, 210, 60)
CYAN = (90, 220, 255)
RED = (230, 70, 70)
GREY = (110, 110, 120)

# Joueur (valeurs de départ, ex. Pikachu-like)
PLAYER_RADIUS = 16
PLAYER_SPEED = 280.0          # px/s
PLAYER_MAX_HP = 100

# Dash
DASH_SPEED = 900.0            # px/s
DASH_DURATION = 0.16          # s : durée du déplacement
DASH_IFRAMES = 0.22           # s : invincibilité (déborde un peu après le dash)
DASH_COOLDOWN = 0.60          # s : mesuré depuis le début du dash

# Arène (rectangle jouable)
ARENA_MARGIN = 60
