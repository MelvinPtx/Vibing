"""Starters jouables (ceux d'Écarlate / Violet) : types, stats et capacités propres.
Les trois emplacements d'attaque sont les mêmes pour tous : "basic" (clic gauche, mêlée),
"special" (E, zone), "cast" (R, projectile)."""
from dataclasses import dataclass, field

from .combat import moves as M
from .combat.types import PType


@dataclass(frozen=True)
class Starter:
    name: str
    dex: int
    types: tuple
    description: str
    moves: dict = field(repr=False)
    max_hp: float = 100.0
    speed_mult: float = 1.0
    atk: float = 1.0
    spa: float = 1.0
    defense: float = 1.0
    spdef: float = 1.0


SPRIGATITO = Starter(
    "Sprigatito", 906, (PType.PLANTE,),
    "Pokémon Chat Herbe. Équilibré et précis : sa zone Plante balaie les groupes.",
    {"basic": M.VIVE_ATTAQUE, "special": M.TRANCH_HERBE, "cast": M.BALLE_OMBRE},
    max_hp=100, speed_mult=1.00, atk=1.00, spa=1.10)
FUECOCO = Starter(
    "Fuecoco", 909, (PType.FEU,),
    "Pokémon Croco Feu. Robuste et lent, mais ses flammes font très mal.",
    {"basic": M.MORSURE, "special": M.LANCE_FLAMMES, "cast": M.FLAMMECHE},
    max_hp=125, speed_mult=0.92, atk=1.00, spa=1.10, defense=1.10)
QUAXLY = Starter(
    "Quaxly", 912, (PType.EAU,),
    "Pokémon Caneton. Rapide et physique : Aqua-Jet et Cru-Aile pour garder ses distances.",
    {"basic": M.AQUA_JET, "special": M.SURF, "cast": M.CRU_AILE},
    max_hp=95, speed_mult=1.08, atk=1.12, spa=0.95)

STARTERS = [SPRIGATITO, FUECOCO, QUAXLY]
DEFAULT_STARTER = SPRIGATITO
