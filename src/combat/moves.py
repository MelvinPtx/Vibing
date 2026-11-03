"""Capacités. Un `MoveSpec` décrit une attaque (élément, catégorie, forme, puissance, cooldown,
animation) ; `build()` en crée l'`Attack` (hitbox) pour un lanceur et une direction.
`from_db()` fabrique la capacité d'un VRAI move à partir des chiffres de pokemondb (type, catégorie,
puissance, PP, priorité, précision) : le jeu ne fait que choisir sa forme (mêlée, zone, projectile).
Le Dash est géré par le contrôleur du joueur, pas ici."""
import math
import random
from dataclasses import dataclass

from pygame import Vector2

from .attack import Attack, Category
from ..data.pokedex import MOVES as DB
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
    pierce: bool = False       # projectile qui traverse les ennemis (Tranch'Aqua, Lame d'Air)
    homing: float = 0.0        # rad/s : le projectile se courbe vers l'ennemi le plus proche (ne rate jamais)
    crit: float = 1.0          # multiplicateur de dégâts (coup critique garanti : Magie Florale)
    burn: float = 0.0          # chance de brûler la cible
    buff: tuple | None = None  # (stat, bonus) : améliore le lanceur à chaque utilisation (Chant Flamboyant)
    move_id: str = ""          # identifiant pokemondb de la vraie capacité (vide pour les capacités génériques)

    def build_at(self, owner, pos) -> Attack:
        """Zone posée à un endroit fixe (Séisme, éboulement...), qui ne suit pas le lanceur."""
        return Attack(owner=owner, element=self.element, category=self.category, power=self.power,
                      radius=self.radius, duration=self.duration, name=self.name, pos=Vector2(pos),
                      kind="zone")

    def build(self, owner, direction: Vector2) -> Attack:
        common = dict(owner=owner, element=self.element, category=self.category,
                      power=self.power * self.crit, radius=self.radius, duration=self.duration,
                      name=self.name, kind=self.kind)
        if self.kind == "melee":
            atk = Attack(pos=owner.pos, offset=direction * self.reach, **common)
        elif self.kind == "burst":
            atk = Attack(pos=owner.pos, offset=Vector2(), **common)
        else:
            atk = Attack(pos=owner.pos + direction * 24, velocity=direction * self.speed,
                         pierce=self.pierce, **common)
            atk.homing = self.homing
        if self.burn:
            atk.on_hit.append(_burn_hook(self.burn))
        return atk


def _burn_hook(chance: float):
    def hook(attack, target, result) -> None:       # les types Feu sont immunisés à la brûlure
        if result.multiplier > 0 and PType.FEU not in target.types and random.random() < chance:
            target.apply_burn(3.0, 5.0)
    return hook


POWER_SCALE = 0.45          # puissance réelle -> puissance en jeu
_TYPES = {"normal": PType.NORMAL, "fire": PType.FEU, "water": PType.EAU, "electric": PType.ELECTRIK,
          "grass": PType.PLANTE, "ice": PType.GLACE, "fighting": PType.COMBAT, "poison": PType.POISON,
          "ground": PType.SOL, "flying": PType.VOL, "psychic": PType.PSY, "bug": PType.INSECTE,
          "rock": PType.ROCHE, "ghost": PType.SPECTRE, "dragon": PType.DRAGON, "dark": PType.TENEBRES,
          "steel": PType.ACIER, "fairy": PType.FEE}
SHAPES = ("melee", "wide", "zone", "bolt")


def from_db(move_id: str, shape: str, **extra) -> MoveSpec:
    """La capacité `move_id` (identifiant pokemondb) sous la forme `shape` :
    melee (coup devant soi), wide (large coup balayé), zone (onde autour de soi), bolt (projectile).
    Type, catégorie et puissance viennent de la base ; la priorité raccourcit le cooldown (Vive-Attaque,
    Aqua-Jet) et les PP faibles l'allongent (les gros coups sont rares)."""
    d = DB[move_id]
    power = d["power"]
    cd = 0.18 + power * 0.0045
    cd *= 0.65 if d["priority"] > 0 else 1.0
    cd *= 1.25 if d["pp"] <= 10 else 1.0
    base = dict(name=d["name"], element=_TYPES[d["type"]],
                category=Category.PHYSICAL if d["category"] == "physical" else Category.SPECIAL,
                power=round(power * POWER_SCALE, 1))
    if d["accuracy"] and d["accuracy"] > 100:               # « ne rate jamais » : projectile à tête chercheuse
        extra.setdefault("homing", 3.5 if shape == "bolt" else 0.0)
    if shape == "melee":
        spec = dict(kind="melee", cooldown=cd, anim="Attack", radius=30 + power * 0.10, duration=0.12, reach=44.0)
    elif shape == "wide":
        spec = dict(kind="melee", cooldown=cd * 1.25, anim="Attack", radius=40 + power * 0.20, duration=0.16, reach=50.0)
    elif shape == "zone":
        spec = dict(kind="burst", cooldown=cd * 1.6, anim="Swing", radius=62 + power * 0.30, duration=0.22)
    elif shape == "bolt":
        spec = dict(kind="projectile", cooldown=cd * 1.15, anim="Shoot", radius=9 + power * 0.05, duration=1.2,
                    speed=470.0)
    else:
        raise ValueError(shape)
    spec["cooldown"] = round(min(max(spec["cooldown"], 0.2), 2.0), 3)
    spec["radius"] = round(spec["radius"], 1)
    return MoveSpec(**base, **spec, move_id=move_id, **extra)


# --- Capacités génériques (tests, ennemis ; les starters utilisent from_db) -------------------------------------------------------
VIVE_ATTAQUE = MoveSpec("Vive-Attaque", PType.NORMAL, P, 20, "melee", 0.30, "Attack", 34, 0.12)
TRANCH_HERBE = MoveSpec("Tranch'Herbe", PType.PLANTE, P, 35, "burst", 0.90, "Swing", 70, 0.22)
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
