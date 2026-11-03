from dataclasses import dataclass

import pygame
from pygame import Vector2


@dataclass
class Stats:
    atk: float = 1.0
    spa: float = 1.0
    defense: float = 1.0
    spdef: float = 1.0


class Entity:
    """Base de toute entité : position, hitbox cercle, types, stats, PV."""

    def __init__(self, pos, radius: float, color, types=(), max_hp: float = 100):
        self.pos = Vector2(pos)
        self.radius = radius
        self.color = color
        self.alive = True
        self.types = tuple(types)
        self.stats = Stats()
        self.max_hp = max_hp
        self.hp = max_hp

    @property
    def rect(self) -> pygame.Rect:
        r = int(self.radius)
        return pygame.Rect(self.pos.x - r, self.pos.y - r, r * 2, r * 2)

    def take_damage(self, amount: float) -> bool:
        if amount <= 0:
            return False
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.alive = False
        return True

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(surface, self.color, self.pos, self.radius)
