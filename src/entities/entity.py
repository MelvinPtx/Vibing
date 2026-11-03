import pygame
from pygame import Vector2


class Entity:
    """Base de toute entité : position, rayon (hitbox cercle), rendu et update."""

    def __init__(self, pos, radius: float, color):
        self.pos = Vector2(pos)
        self.radius = radius
        self.color = color
        self.alive = True

    @property
    def rect(self) -> pygame.Rect:
        r = int(self.radius)
        return pygame.Rect(self.pos.x - r, self.pos.y - r, r * 2, r * 2)

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(surface, self.color, self.pos, self.radius)
