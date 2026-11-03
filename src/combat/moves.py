"""Fabriques d'attaques : les 3 attaques offensives du joueur (le Dash est dans le contrôleur)."""
from pygame import Vector2

from .attack import Attack, Category
from .types import PType

# cooldowns (s) par emplacement
COOLDOWNS = {"basic": 0.30, "special": 0.90, "cast": 0.60}


def vive_attaque(owner, direction: Vector2) -> Attack:
    return Attack(owner, owner.pos, PType.NORMAL, Category.PHYSICAL, power=20, radius=34,
                  duration=0.12, offset=direction * 44, name="Vive-Attaque")


def tranch_herbe(owner, direction: Vector2) -> Attack:
    return Attack(owner, owner.pos, PType.PLANTE, Category.SPECIAL, power=35, radius=70,
                  duration=0.22, offset=Vector2(), name="Tranch'Herbe")


def balle_ombre(owner, direction: Vector2) -> Attack:
    return Attack(owner, owner.pos + direction * 24, PType.SPECTRE, Category.SPECIAL, power=25,
                  radius=12, duration=1.2, velocity=direction * 520, pierce=False,
                  name="Ball'Ombre")


MOVES = {"basic": vive_attaque, "special": tranch_herbe, "cast": balle_ombre}
