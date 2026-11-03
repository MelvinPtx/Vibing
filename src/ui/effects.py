"""Effets visuels : éclats et onde de choc à la mort d'un ennemi."""
import math
import random

import pygame
from pygame import Vector2

RING_TIME = 0.4


class Effects:
    def __init__(self):
        self.particles: list = []
        self.rings: list = []
        self._layer = None

    def burst(self, pos, color, n: int = 14) -> None:
        """Gerbe d'éclats (couleur du type + blanc) et onde de choc."""
        for _ in range(n):
            ang, speed, life = random.uniform(0, math.tau), random.uniform(90, 260), random.uniform(0.45, 0.8)
            self.particles.append({"p": Vector2(pos), "v": Vector2(math.cos(ang), math.sin(ang)) * speed,
                                   "life": life, "max": life, "r": random.uniform(3, 7),
                                   "c": random.choice((color, color, (255, 255, 255)))})
        self.rings.append({"p": Vector2(pos), "c": color, "t": 0.0})

    @property
    def active(self) -> bool:
        return bool(self.particles or self.rings)

    def update(self, dt: float) -> None:
        for q in self.particles:
            q["p"] += q["v"] * dt
            q["v"] *= max(0.0, 1 - 3.2 * dt)           # frottement
            q["life"] -= dt
        for r in self.rings:
            r["t"] += dt
        self.particles = [q for q in self.particles if q["life"] > 0]
        self.rings = [r for r in self.rings if r["t"] < RING_TIME]

    def draw(self, surface) -> None:
        if not self.active:
            return
        if self._layer is None or self._layer.get_size() != surface.get_size():
            self._layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        self._layer.fill((0, 0, 0, 0))
        for r in self.rings:
            k = r["t"] / RING_TIME
            pygame.draw.circle(self._layer, (*r["c"], int(210 * (1 - k))), r["p"],
                               int(14 + 70 * k), max(1, int(5 * (1 - k))))
        for q in self.particles:
            k = q["life"] / q["max"]
            pygame.draw.circle(self._layer, (*q["c"], int(255 * k)), q["p"], max(1, q["r"] * (0.4 + 0.6 * k)))
        surface.blit(self._layer, (0, 0))
