"""Espèces utilisées par le jeu (numéro de Pokédex national) : données pures, sans pygame.
Les sprites viennent de PMDCollab/SpriteCollab (voir assets/sprites/CREDITS.md)."""
from .combat.types import PType

PLAYER_DEX = 133          # Évoli (Normal)
RATTATA_DEX = 19          # Rattata (Normal)

# Mannequins d'entraînement : un vrai Pokémon par cas de test de la table des types.
# (nom, n° Pokédex, types)
DUMMY_ROSTER = [
    ("Ronflex", 143, (PType.NORMAL,)),
    ("Salamèche", 4, (PType.FEU,)),
    ("Carapuce", 7, (PType.EAU,)),
    ("Germignon", 152, (PType.PLANTE,)),
    ("Feuforêve", 200, (PType.SPECTRE,)),
    ("Paras", 46, (PType.INSECTE, PType.PLANTE)),
]

NAMES = {PLAYER_DEX: "Évoli", RATTATA_DEX: "Rattata", **{d: n for n, d, _ in DUMMY_ROSTER}}
ALL_DEX = sorted(NAMES)
