"""Classe Attack : une hitbox (cercle) active pendant `duration` secondes."""
from enum import Enum

from pygame import Vector2

from .types import PType


class Category(Enum):
    PHYSICAL = "Physique"
    SPECIAL = "Spécial"


class Attack:
    def __init__(self, owner, pos, element: PType, category: Category, power: float,
                 radius: float, duration: float, velocity=None, offset=None,
                 pierce: bool = True, name: str = "", slot: str | None = None,
                 kind: str = "melee"):
        self.owner = owner
        self.pos = Vector2(pos)
        self.element = element
        self.category = category
        self.power = power
        self.radius = radius
        self.duration = duration
        self.time_left = duration
        self.velocity = Vector2(velocity) if velocity is not None else Vector2()
        self.offset = Vector2(offset) if offset is not None else None  # colle au lanceur
        self.pierce = pierce          # False : disparaît au premier impact
        self.name = name
        self.kind = kind              # "melee" | "burst" | "zone" (posée au sol) | "projectile" : sert au rendu
        self.slot = slot              # "basic" | "special" | "cast" (lu par les modificateurs)
        self.hit: set[int] = set()    # une cible n'est touchée qu'une fois par attaque
        self.on_hit = []              # hooks (phase 4 : effets des objets, brûlure...)

    @property
    def active(self) -> bool:
        return self.time_left > 0

    def update(self, dt: float) -> None:
        self.time_left -= dt
        if self.offset is not None:
            self.pos = self.owner.pos + self.offset
        else:
            self.pos += self.velocity * dt

    def overlaps(self, target) -> bool:
        return self.pos.distance_to(target.pos) <= self.radius + target.radius

    def kill(self) -> None:
        self.time_left = 0
