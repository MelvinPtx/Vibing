"""Ennemis. Le comportement de poursuite est un steering behavior (Reynolds) :
seek (vers le joueur) + separation (éviter de s'empiler sur ses voisins),
limité par une accélération maximale -> trajectoires courbes et naturelles.
"""
import pygame
from pygame import Vector2

from .. import settings as S
from ..combat.types import PType
from .entity import Entity


class Enemy(Entity):
    speed = 140.0
    accel = 900.0            # px/s² : force de pilotage maximale
    turn_rate = 8.0          # réactivité : vitesse atteinte en ~1/turn_rate s
    contact_damage = 10.0
    contact_cooldown = 0.8   # s entre deux touches
    separation_radius = 46.0

    def __init__(self, pos, radius, color, types, max_hp):
        super().__init__(pos, radius, color, types, max_hp)
        self.vel = Vector2()
        self.spawn_left = S.SPAWN_DELAY
        self.contact_cd = 0.0
        self.flash = 0.0

    @property
    def spawning(self) -> bool:
        return self.spawn_left > 0

    @property
    def vulnerable(self) -> bool:
        return self.alive and not self.spawning

    def take_damage(self, amount: float) -> bool:
        if self.spawning:
            return False
        hit = super().take_damage(amount)
        if hit:
            self.flash = 0.1
        return hit

    # --- steering ---
    def seek(self, target: Vector2) -> Vector2:
        to = target - self.pos
        if to.length_squared() == 0:
            return Vector2()
        return (to.normalize() * self.speed - self.vel) * self.turn_rate

    def separation(self, others) -> Vector2:
        push = Vector2()
        for o in others:
            if o is self or not o.alive:
                continue
            away = self.pos - o.pos
            d = away.length()
            if 0 < d < self.separation_radius:
                push += away / d * (1 - d / self.separation_radius)
        return push * self.speed

    def update(self, dt: float, player=None, others=(), bounds: pygame.Rect | None = None) -> None:
        self.flash = max(0.0, self.flash - dt)
        self.contact_cd = max(0.0, self.contact_cd - dt)
        if self.spawning:
            self.spawn_left -= dt
            return
        if player is None:
            return
        force = self.seek(player.pos) + self.separation(others)
        if force.length() > self.accel:
            force.scale_to_length(self.accel)
        self.vel += force * dt
        if self.vel.length() > self.speed:
            self.vel.scale_to_length(self.speed)
        self.pos += self.vel * dt
        if bounds is not None:
            r = self.radius
            self.pos.x = min(max(self.pos.x, bounds.left + r), bounds.right - r)
            self.pos.y = min(max(self.pos.y, bounds.top + r), bounds.bottom - r)

    def can_touch(self, player) -> bool:
        return (self.vulnerable and self.contact_cd <= 0
                and self.pos.distance_to(player.pos) <= self.radius + player.radius)

    def draw(self, surface) -> None:
        if not self.alive:
            return
        if self.spawning:  # cercle qui se remplit = apparition
            k = 1 - self.spawn_left / S.SPAWN_DELAY
            pygame.draw.circle(surface, self.color, self.pos, max(2, self.radius * k), 2)
            return
        pygame.draw.circle(surface, S.WHITE if self.flash > 0 else self.color, self.pos, self.radius)
        pygame.draw.circle(surface, (20, 20, 20), self.pos, self.radius, 2)
        w = 34
        x, y = self.pos.x - w / 2, self.pos.y - self.radius - 10
        pygame.draw.rect(surface, (60, 20, 20), (x, y, w, 5))
        pygame.draw.rect(surface, S.RED, (x, y, w * self.hp / self.max_hp, 5))


class Rattata(Enemy):
    speed = 150.0

    def __init__(self, pos):
        super().__init__(pos, 14, (160, 110, 190), (PType.NORMAL,), max_hp=60)
