"""Géométrie des collisions cercle / rectangle (module neutre : utilisé par le combat, les entités
et les salles sans créer de dépendance circulaire)."""
import math

import pygame
from pygame import Vector2


def push_out(pos: Vector2, radius: float, rect: pygame.Rect) -> bool:
    """Repousse `pos` (modifié sur place) hors du rectangle. True s'il y avait contact."""
    cx = min(max(pos.x, rect.left), rect.right)
    cy = min(max(pos.y, rect.top), rect.bottom)
    dx, dy = pos.x - cx, pos.y - cy
    d2 = dx * dx + dy * dy
    if d2 >= radius * radius:
        return False
    if d2 > 1e-9:
        d = math.sqrt(d2)
        pos.x += dx / d * (radius - d)
        pos.y += dy / d * (radius - d)
    else:                                   # centre à l'intérieur : sort par le bord le plus proche
        gaps = {"l": pos.x - rect.left, "r": rect.right - pos.x, "t": pos.y - rect.top,
                "b": rect.bottom - pos.y}
        side = min(gaps, key=gaps.get)
        if side == "l":
            pos.x = rect.left - radius
        elif side == "r":
            pos.x = rect.right + radius
        elif side == "t":
            pos.y = rect.top - radius
        else:
            pos.y = rect.bottom + radius
    return True


def circle_hits_rect(pos: Vector2, radius: float, rect: pygame.Rect) -> bool:
    cx = min(max(pos.x, rect.left), rect.right)
    cy = min(max(pos.y, rect.top), rect.bottom)
    return (pos.x - cx) ** 2 + (pos.y - cy) ** 2 < radius * radius


def resolve(pos: Vector2, radius: float, obstacles) -> None:
    for _ in range(2):                      # 2 passes : coins entre deux obstacles proches
        for o in obstacles:
            push_out(pos, radius, o)
