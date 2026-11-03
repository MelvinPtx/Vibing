"""Espèces utilisées par le jeu (numéro de Pokédex national) : données pures, sans pygame.
Les sprites viennent de PMDCollab/SpriteCollab (voir assets/sprites/CREDITS.md)."""
from .combat.types import PType
from .starters import STARTERS

RATTATA_DEX, ZUBAT_DEX, GEODUDE_DEX, GASTLY_DEX, VOLTORB_DEX = 19, 41, 74, 92, 100

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

NAMES = {
    **{s.dex: s.name for s in STARTERS},
    RATTATA_DEX: "Rattata", ZUBAT_DEX: "Zubat", GEODUDE_DEX: "Racaillou",
    GASTLY_DEX: "Fantominus", VOLTORB_DEX: "Voltorbe",
    **{d: n for n, d, _ in DUMMY_ROSTER},
}
ALL_DEX = sorted(NAMES)
