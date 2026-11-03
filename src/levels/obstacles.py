"""Obstacles de salle : rochers rectangulaires, navigation et générateur de dispositions
(les collisions cercle/rectangle sont dans src/geometry.py).

Les obstacles sont de simples `pygame.Rect`. Ils bloquent le joueur, les ennemis terrestres et les
projectiles ; les ennemis volants passent au-dessus. `NavGrid` (carte de distances par BFS depuis
le joueur) permet aux ennemis terrestres de contourner les murs au lieu de s'y coller.
Chaque disposition est vérifiée : zone des portes et point de départ dégagés, tout le sol atteignable.
"""
import math
import random
from collections import deque

import pygame
from pygame import Vector2

from ..geometry import circle_hits_rect, push_out, resolve  # noqa: F401 (réexportés)

LAYOUTS = ("open", "pillars", "scatter", "walls", "blocks")
LAYOUT_WEIGHTS = {"open": 1, "pillars": 3, "scatter": 3, "walls": 2, "blocks": 2}
DOOR_ZONE = 130        # px du haut de l'arène gardés libres (portes de récompense)
START_ZONE = 130       # rayon dégagé autour du point d'arrivée du joueur
MIN_GAP = 76           # écart minimal entre deux obstacles (le joueur et les ennemis doivent passer)
WALL_MARGIN = 50       # écart minimal avec les murs de l'arène


# --- navigation -----------------------------------------------------------------
class NavGrid:
    """Grille de 32 px ; les cellules proches d'un obstacle sont bloquées. `update_target`
    calcule les distances (BFS) jusqu'à la cellule de la cible ; `next_point` donne la prochaine
    cellule à viser pour s'en approcher."""

    NEIGHBORS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))

    def __init__(self, arena: pygame.Rect, obstacles, cell: int = 32, margin: int = 22):
        self.arena, self.cell, self.obstacles = arena, cell, list(obstacles)
        self.margin = margin
        self.cols, self.rows = math.ceil(arena.w / cell), math.ceil(arena.h / cell)
        grown = [o.inflate(2 * margin, 2 * margin) for o in self.obstacles]
        self.blocked = [[any(pygame.Rect(arena.x + c * cell, arena.y + r * cell, cell, cell).colliderect(g)
                             for g in grown) for r in range(self.rows)] for c in range(self.cols)]
        self.dist = None
        self._grown = grown

    def cell_of(self, pos) -> tuple:
        c = min(max(int((pos[0] - self.arena.x) // self.cell), 0), self.cols - 1)
        r = min(max(int((pos[1] - self.arena.y) // self.cell), 0), self.rows - 1)
        return c, r

    def center(self, c: int, r: int) -> Vector2:
        return Vector2(self.arena.x + (c + 0.5) * self.cell, self.arena.y + (r + 0.5) * self.cell)

    def is_free(self, pos) -> bool:
        c, r = self.cell_of(pos)
        return not self.blocked[c][r]

    def _bfs(self, start):
        dist = {start: 0}
        q = deque([start])
        while q:
            c, r = q.popleft()
            for dc, dr in self.NEIGHBORS[:4]:
                n = (c + dc, r + dr)
                if (0 <= n[0] < self.cols and 0 <= n[1] < self.rows and n not in dist
                        and not self.blocked[n[0]][n[1]]):
                    dist[n] = dist[(c, r)] + 1
                    q.append(n)
        return dist

    def update_target(self, pos) -> None:
        start = self.cell_of(pos)
        if self.blocked[start[0]][start[1]]:     # cible sur une cellule bloquée : la plus proche libre
            free = [(c, r) for c in range(self.cols) for r in range(self.rows) if not self.blocked[c][r]]
            if not free:
                self.dist = {}
                return
            start = min(free, key=lambda cr: (cr[0] - start[0]) ** 2 + (cr[1] - start[1]) ** 2)
        self.dist = self._bfs(start)

    def reachable_cells(self, from_pos):
        start = self.cell_of(from_pos)
        return self._bfs(start) if not self.blocked[start[0]][start[1]] else {}

    def all_free_reachable(self, from_pos) -> bool:
        reach = self.reachable_cells(from_pos)
        free = sum(not self.blocked[c][r] for c in range(self.cols) for r in range(self.rows))
        return bool(reach) and len(reach) == free

    def line_clear(self, a, b, radius: float = 0.0) -> bool:
        """Aucun obstacle (agrandi du rayon) entre a et b : on peut foncer en ligne droite."""
        for o in self.obstacles:
            if o.inflate(2 * radius, 2 * radius).clipline(tuple(a), tuple(b)):
                return False
        return True

    def next_point(self, pos, fallback) -> Vector2:
        if not self.dist:
            return Vector2(fallback)
        cur = self.cell_of(pos)
        here = self.dist.get(cur)
        if here is None:                          # sur une cellule bloquée/inconnue : vers la meilleure voisine
            cands = [(c, r) for c, r in ((cur[0] + dc, cur[1] + dr) for dc, dr in self.NEIGHBORS)
                     if (c, r) in self.dist]
            return self.center(*min(cands, key=self.dist.get)) if cands else Vector2(fallback)
        best, best_d = None, here
        for dc, dr in self.NEIGHBORS:
            n = (cur[0] + dc, cur[1] + dr)
            d = self.dist.get(n)
            if d is None or d >= best_d:
                continue
            if dc and dr and (self.blocked[cur[0] + dc][cur[1]] or self.blocked[cur[0]][cur[1] + dr]):
                continue                           # pas de coupe-coin en diagonale
            best, best_d = n, d
        return self.center(*best) if best else Vector2(fallback)


# --- générateur -------------------------------------------------------------------
def _keepouts(arena: pygame.Rect):
    door = pygame.Rect(arena.left, arena.top, arena.w, DOOR_ZONE)
    start = pygame.Rect(0, 0, 2 * START_ZONE, 2 * START_ZONE)
    start.center = (arena.centerx, arena.bottom - 60)
    return door, start


def _ok(rect: pygame.Rect, placed, arena: pygame.Rect) -> bool:
    if not arena.inflate(-2 * WALL_MARGIN, -2 * WALL_MARGIN).contains(rect):
        return False
    if any(rect.colliderect(k) for k in _keepouts(arena)):
        return False
    return all(not rect.inflate(MIN_GAP, MIN_GAP).colliderect(p) for p in placed)


def _random_rects(arena, rng, count, size_range, placed):
    out = []
    for _ in range(count * 25):
        if len(out) == count:
            break
        w, h = rng.randint(*size_range), rng.randint(*size_range)
        r = pygame.Rect(rng.randint(arena.left, arena.right - w), rng.randint(arena.top, arena.bottom - h), w, h)
        if _ok(r, placed + out, arena):
            out.append(r)
    return out


def _walls(arena, rng):
    """Deux murs horizontaux avec un passage à des endroits aléatoires -> des couloirs."""
    out = []
    for y in (arena.top + 210, arena.top + 340):
        gap_x = rng.randint(arena.left + 180, arena.right - 180)
        left = pygame.Rect(arena.left + WALL_MARGIN, y, max(0, gap_x - 70 - arena.left - WALL_MARGIN), 38)
        right = pygame.Rect(gap_x + 70, y, max(0, arena.right - WALL_MARGIN - gap_x - 70), 38)
        out += [r for r in (left, right) if r.w > 60]
    return out


def _blocks(arena, rng):
    """Deux gros blocs de part et d'autre du centre."""
    h = rng.randint(150, 220)
    y = rng.randint(arena.top + 200, arena.bottom - h - 150)
    w = rng.randint(100, 150)
    return [pygame.Rect(arena.left + 150, y, w, h), pygame.Rect(arena.right - 150 - w, y + rng.randint(-40, 40), w, h)]


def generate_layout(kind: str, arena: pygame.Rect, rng: random.Random):
    """Liste de Rect pour la disposition `kind` ; [] si aucune version valide n'est trouvée."""
    for _ in range(30):
        if kind == "pillars":
            rects = _random_rects(arena, rng, rng.randint(3, 6), (52, 64), [])
        elif kind == "scatter":
            rects = _random_rects(arena, rng, rng.randint(4, 7), (48, 110), [])
        elif kind == "walls":
            rects = _walls(arena, rng)
        elif kind == "blocks":
            rects = _blocks(arena, rng)
        else:
            return []
        door, start = _keepouts(arena)
        inner = arena.inflate(-2 * WALL_MARGIN // 2, -2 * WALL_MARGIN // 2)
        if (rects and all(inner.contains(r) and not r.colliderect(door) and not r.colliderect(start)
                          for r in rects)
                and NavGrid(arena, rects).all_free_reachable((arena.centerx, arena.bottom - 60))):
            return rects
    return []


def pick_layout(rng: random.Random, room_number: int, boss: bool = False) -> str:
    if boss:
        return "pillars"                      # des abris contre les projectiles du boss
    if room_number <= 1:
        return "open"
    return rng.choices(list(LAYOUT_WEIGHTS), weights=list(LAYOUT_WEIGHTS.values()))[0]
