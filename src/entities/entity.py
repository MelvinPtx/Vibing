from dataclasses import dataclass

import pygame
from pygame import Vector2

from .. import settings as S


@dataclass
class Stats:
    atk: float = 1.0
    spa: float = 1.0
    defense: float = 1.0
    spdef: float = 1.0


class Entity:
    """Base de toute entité : position, hitbox cercle, types, stats, PV."""

    name = ""
    species = None            # n° de Pokédex du sprite (None = cercle de secours)

    def __init__(self, pos, radius: float, color, types=(), max_hp: float = 100):
        self.pos = Vector2(pos)
        self.radius = radius
        self.color = color
        self.alive = True
        self.facing = Vector2(0, 1)
        self.types = tuple(types)
        self.stats = Stats()
        self.max_hp = max_hp
        self.hp = max_hp
        self.death_t = None        # secondes écoulées depuis la mort (None = vivant)
        self.death_fresh = False   # True le temps d'une frame : l'UI y lance les effets de mort
        self.burn_left = 0.0
        self.burn_dps = 0.0
        self._burn_tick = 0.0

    # --- infos lues par le rendu de sprites (src/ui/sprites.py) ---
    @property
    def sprite_visible(self) -> bool:
        return self.alive or self.dying

    @property
    def sprite_anim(self) -> tuple:
        """(nom d'animation PMD, vitesse de lecture)."""
        return ("Idle", 1.0)

    @property
    def rect(self) -> pygame.Rect:
        r = int(self.radius)
        return pygame.Rect(self.pos.x - r, self.pos.y - r, r * 2, r * 2)

    def stat(self, name: str) -> float:
        """Valeur effective d'une stat (atk, spa, defense, spdef) ; le joueur y ajoute ses bonus temporaires."""
        return getattr(self.stats, name)

    def take_damage(self, amount: float) -> bool:
        if amount <= 0:
            return False
        self.hp = max(0, self.hp - amount)
        if self.hp == 0:
            self.alive = False
            self.death_t, self.death_fresh = 0.0, True
        return True

    @property
    def dying(self) -> bool:
        """Mort depuis moins de DEATH_DURATION : l'animation de mort est en cours."""
        return not self.alive and self.death_t is not None and self.death_t < S.DEATH_DURATION

    def tick_death(self, dt: float) -> None:
        if not self.alive and self.death_t is not None:
            self.death_t += dt

    def apply_burn(self, duration: float, dps: float) -> None:
        self.burn_left = max(self.burn_left, duration)
        self.burn_dps = max(self.burn_dps, dps)

    def tick_status(self, dt: float) -> None:
        """Brûlure : dégâts bruts toutes les 0,5 s (hors table des types)."""
        if self.burn_left <= 0 or not self.alive:
            self.burn_left, self.burn_dps = 0.0, 0.0
            return
        self.burn_left -= dt
        self._burn_tick += dt
        if self._burn_tick >= 0.5:
            self._burn_tick -= 0.5
            self.take_damage(self.burn_dps * 0.5)

    def draw_status(self, surface) -> None:
        if self.burn_left > 0 and self.alive:
            pygame.draw.circle(surface, (255, 140, 30), self.pos, self.radius + 4, 3)

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.circle(surface, self.color, self.pos, self.radius)
