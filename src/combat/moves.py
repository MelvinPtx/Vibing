"""Capacités. Un `MoveSpec` décrit une attaque (élément, catégorie, forme, puissance, cooldown,
animation) ; `build()` en crée l'`Attack` (hitbox) pour un lanceur et une direction.
Le Dash est géré par le contrôleur du joueur, pas ici."""
from dataclasses import dataclass

from pygame import Vector2

from .attack import Attack, Category
from .types import PType

P, S = Category.PHYSICAL, Category.SPECIAL


@dataclass(frozen=True)
class MoveSpec:
    name: str
    element: PType
    category: Category
    power: float
    kind: str            # "melee" (devant soi) | "burst" (zone autour de soi) | "projectile"
    cooldown: float      # s
    anim: str            # animation PMD jouée par le lanceur (Attack / Swing / Shoot)
    radius: float
    duration: float      # durée active de la hitbox (durée de vie d'un projectile)
    reach: float = 44.0  # melee : distance devant le lanceur
    speed: float = 0.0   # projectile : px/s

    def build_at(self, owner, pos) -> Attack:
        """Zone posée à un endroit fixe (Séisme, éboulement...), qui ne suit pas le lanceur."""
        return Attack(owner=owner, element=self.element, category=self.category, power=self.power,
                      radius=self.radius, duration=self.duration, name=self.name, pos=Vector2(pos))

    def build(self, owner, direction: Vector2) -> Attack:
        common = dict(owner=owner, element=self.element, category=self.category, power=self.power,
                      radius=self.radius, duration=self.duration, name=self.name)
        if self.kind == "melee":
            return Attack(pos=owner.pos, offset=direction * self.reach, **common)
        if self.kind == "burst":
            return Attack(pos=owner.pos, offset=Vector2(), **common)
        return Attack(pos=owner.pos + direction * 24, velocity=direction * self.speed,
                      pierce=False, **common)


# --- Capacités des starters -------------------------------------------------------
VIVE_ATTAQUE = MoveSpec("Vive-Attaque", PType.NORMAL, P, 20, "melee", 0.30, "Attack", 34, 0.12)
TRANCH_HERBE = MoveSpec("Tranch'Herbe", PType.PLANTE, S, 35, "burst", 0.90, "Swing", 70, 0.22)
BALLE_OMBRE = MoveSpec("Ball'Ombre", PType.SPECTRE, S, 25, "projectile", 0.60, "Shoot", 12, 1.2,
                       speed=520)

MORSURE = MoveSpec("Morsure", PType.TENEBRES, P, 24, "melee", 0.34, "Attack", 34, 0.12)
LANCE_FLAMMES = MoveSpec("Lance-Flammes", PType.FEU, S, 38, "burst", 0.95, "Swing", 72, 0.22)
FLAMMECHE = MoveSpec("Flammèche", PType.FEU, S, 22, "projectile", 0.55, "Shoot", 12, 1.1, speed=480)

AQUA_JET = MoveSpec("Aqua-Jet", PType.EAU, P, 20, "melee", 0.28, "Attack", 34, 0.12, reach=46)
SURF = MoveSpec("Surf", PType.EAU, S, 34, "burst", 0.90, "Swing", 74, 0.22)
CRU_AILE = MoveSpec("Cru-Aile", PType.VOL, P, 26, "projectile", 0.60, "Shoot", 14, 1.0, speed=540)

# --- Capacités d'ennemis -----------------------------------------------------------
ENEMY_BALLE_OMBRE = MoveSpec("Ball'Ombre", PType.SPECTRE, S, 14, "projectile", 2.4, "Shoot", 10, 2.5,
                             speed=250)
EXPLOSION = MoveSpec("Explosion", PType.NORMAL, P, 32, "burst", 0.0, "Attack", 90, 0.20)


# --- Capacités de boss --------------------------------------------------------------
JET_PIERRES = MoveSpec("Jet-Pierres", PType.ROCHE, P, 15, "projectile", 0.0, "Shoot", 14, 2.4, speed=310)
SEISME = MoveSpec("Séisme", PType.SOL, P, 26, "burst", 0.0, "Swing", 230, 0.25)
EBOULEMENT = MoveSpec("Éboulement", PType.ROCHE, P, 22, "burst", 0.0, "Attack", 62, 0.2)
BOSS_BALLE_OMBRE = MoveSpec("Ball'Ombre", PType.SPECTRE, S, 15, "projectile", 0.0, "Shoot", 11, 3.0,
                            speed=270)
POING_OMBRE = MoveSpec("Poing Ombre", PType.SPECTRE, P, 24, "burst", 0.0, "Attack", 110, 0.22)
BOMBE_BEURK = MoveSpec("Bombe Beurk", PType.POISON, S, 18, "burst", 0.0, "Swing", 70, 0.2)


# Fabriques historiques (utilisées par les tests)
def vive_attaque(owner, direction):
    return VIVE_ATTAQUE.build(owner, direction)


def tranch_herbe(owner, direction):
    return TRANCH_HERBE.build(owner, direction)


def balle_ombre(owner, direction):
    return BALLE_OMBRE.build(owner, direction)
