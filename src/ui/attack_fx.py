"""Animations d'attaque dessinées par le code (aucun fichier image), un style par type.

`AttackFX.spawn(attack)` crée une animation indépendante de la durée de la hitbox (qui est très
courte) : une **coupe en croissant** pour la mêlée, une **onde de choc avec éclats** pour les zones,
une **orbe avec traînée** pour les projectiles (qui se termine en impact), plus un flash d'impact
(`hit`). Chaque type a sa palette et sa forme d'éclat : flammes, gouttes, feuilles, éclairs, éclats de
glace, volutes spectrales, rochers, étoiles de fée...
"""
import math
import random
import weakref
from collections import deque

import pygame
from pygame import Vector2

from ..combat.types import PType

# type -> (couleur principale, couleur sombre, couleur claire, forme des éclats)
STYLES = {
    PType.NORMAL: ((225, 225, 215), (150, 155, 165), (255, 255, 255), "streak"),
    PType.FEU: ((255, 140, 40), (230, 60, 30), (255, 235, 130), "flame"),
    PType.EAU: ((80, 165, 255), (40, 100, 225), (215, 240, 255), "drop"),
    PType.ELECTRIK: ((255, 225, 70), (230, 170, 20), (255, 255, 210), "bolt"),
    PType.PLANTE: ((110, 205, 90), (50, 140, 70), (225, 255, 170), "leaf"),
    PType.GLACE: ((140, 225, 235), (80, 170, 215), (235, 250, 255), "shard"),
    PType.COMBAT: ((215, 70, 90), (150, 30, 55), (255, 185, 140), "star"),
    PType.POISON: ((185, 100, 215), (120, 55, 165), (235, 175, 255), "bubble"),
    PType.SOL: ((215, 150, 80), (150, 100, 55), (245, 215, 150), "rock"),
    PType.VOL: ((185, 205, 250), (120, 150, 225), (255, 255, 255), "wind"),
    PType.PSY: ((255, 110, 165), (200, 50, 120), (255, 200, 225), "ring"),
    PType.INSECTE: ((165, 205, 50), (105, 145, 30), (225, 245, 120), "hex"),
    PType.ROCHE: ((205, 185, 135), (140, 125, 90), (240, 230, 190), "rock"),
    PType.SPECTRE: ((125, 95, 190), (60, 40, 115), (210, 180, 255), "wisp"),
    PType.DRAGON: ((70, 115, 235), (125, 75, 235), (195, 230, 255), "diamond"),
    PType.TENEBRES: ((105, 80, 125), (35, 20, 50), (195, 150, 225), "wisp"),
    PType.ACIER: ((175, 195, 220), (110, 130, 165), (250, 252, 255), "shard"),
    PType.FEE: ((245, 150, 230), (205, 95, 190), (255, 225, 252), "star"),
}

# polygones unitaires (x vers l'avant), orientés par angle puis mis à l'échelle
SHAPES = {
    "leaf": [(1, 0), (0.3, -0.45), (-0.6, -0.35), (-1, 0), (-0.6, 0.35), (0.3, 0.45)],
    "flame": [(1.3, 0), (0.4, -0.55), (-0.3, -0.75), (-0.9, -0.2), (-1, 0.1), (-0.5, 0.65), (0.3, 0.5)],
    "drop": [(1.2, 0), (0.2, -0.55), (-0.5, -0.65), (-0.9, 0), (-0.5, 0.65), (0.2, 0.55)],
    "shard": [(1.3, 0), (0, -0.45), (-0.9, 0), (0, 0.45)],
    "star": [(1, 0), (0.25, 0.25), (0, 1), (-0.25, 0.25), (-1, 0), (-0.25, -0.25), (0, -1), (0.25, -0.25)],
    "rock": [(1, 0.1), (0.5, -0.7), (-0.4, -0.8), (-1, -0.1), (-0.6, 0.7), (0.4, 0.8)],
    "hex": [(math.cos(i * math.pi / 3), math.sin(i * math.pi / 3)) for i in range(6)],
    "streak": [(1.6, 0), (0, -0.16), (-1.6, 0), (0, 0.16)],
    "diamond": [(1, 0), (0, -0.7), (-1, 0), (0, 0.7)],
}

DUR = {"melee": 0.30, "burst": 0.50, "zone": 0.50, "impact": 0.30}


def ease_out(k: float) -> float:
    return 1 - (1 - min(max(k, 0.0), 1.0)) ** 3


def lerp(a, b, k):
    return a + (b - a) * k


# --- primitives (toutes sur la surface de jeu, avec alpha 0-255) --------------------------
def _blit_tmp(surface, rect: pygame.Rect, draw, alpha: int) -> None:
    if alpha <= 0:
        return
    rect = rect.inflate(6, 6)
    tmp = pygame.Surface(rect.size, pygame.SRCALPHA)
    draw(tmp, Vector2(-rect.x, -rect.y))
    if alpha < 255:
        tmp.set_alpha(alpha)
    surface.blit(tmp, rect.topleft)


def poly(surface, pts, color, alpha=255, width=0) -> None:
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    rect = pygame.Rect(min(xs), min(ys), max(xs) - min(xs) + 1, max(ys) - min(ys) + 1)
    _blit_tmp(surface, rect, lambda t, o: pygame.draw.polygon(t, color, [(x + o.x, y + o.y) for x, y in pts], width), alpha)


def circle(surface, c, r, color, alpha=255, width=0) -> None:
    r = max(1, r)
    rect = pygame.Rect(c[0] - r, c[1] - r, 2 * r + 1, 2 * r + 1)
    _blit_tmp(surface, rect, lambda t, o: pygame.draw.circle(t, color, (c[0] + o.x, c[1] + o.y), r, width), alpha)


def lines(surface, pts, color, alpha=255, width=3) -> None:
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    rect = pygame.Rect(min(xs) - width, min(ys) - width, max(xs) - min(xs) + 2 * width, max(ys) - min(ys) + 2 * width)
    _blit_tmp(surface, rect, lambda t, o: pygame.draw.lines(t, color, False, [(x + o.x, y + o.y) for x, y in pts], width), alpha)


_glows: dict = {}


def glow(surface, c, r, color, alpha=255) -> None:
    """Halo doux (dégradé radial mis en cache)."""
    r = max(4, int(r) // 2 * 2)
    key = (r, color)
    if key not in _glows:
        s = pygame.Surface((2 * r, 2 * r), pygame.SRCALPHA)
        for i in range(r, 0, -2):
            pygame.draw.circle(s, (*color, int(230 * (1 - i / r) ** 2)), (r, r), i)
        _glows[key] = s
    g = _glows[key]
    if alpha < 255:
        g = g.copy()
        g.set_alpha(alpha)
    surface.blit(g, g.get_rect(center=(round(c[0]), round(c[1]))))


def shape(surface, name, pos, size, angle, color, alpha=255) -> None:
    pts = SHAPES.get(name)
    if pts is None:
        return
    ca, sa = math.cos(angle), math.sin(angle)
    poly(surface, [(pos[0] + (x * ca - y * sa) * size, pos[1] + (x * sa + y * ca) * size) for x, y in pts], color, alpha)


def bolt(surface, a, b, color, alpha, rng, width=3, segs=6) -> None:
    a, b = Vector2(a), Vector2(b)
    d = b - a
    if d.length_squared() < 4:
        return
    perp = Vector2(-d.y, d.x).normalize()
    pts = [a + d * (i / segs) + (perp * rng.uniform(-8, 8) if 0 < i < segs else Vector2()) for i in range(segs + 1)]
    lines(surface, pts, color, alpha, width)


def particle(surface, style, name, pos, size, angle, alpha, rng=None) -> None:
    """Un éclat dans la forme propre au type (flamme, goutte, feuille...)."""
    main, dark, light, _ = style
    if name in SHAPES:
        shape(surface, name, pos, size, angle, dark, alpha)
        shape(surface, name, pos, size * 0.62, angle, main, alpha)
        if name in ("flame", "star", "streak"):
            shape(surface, name, pos, size * 0.3, angle, light, alpha)
    elif name == "bubble":
        circle(surface, pos, size, main, alpha // 2)
        circle(surface, pos, size, light, alpha, 2)
        circle(surface, (pos[0] - size * 0.3, pos[1] - size * 0.3), max(1, size // 4), light, alpha)
    elif name == "ring":
        circle(surface, pos, size, main, alpha, 3)
    elif name == "wisp":
        glow(surface, pos, size * 2.2, main, alpha)
        glow(surface, pos, size * 1.1, light, alpha)
    elif name == "wind":
        a = Vector2(math.cos(angle), math.sin(angle)) * size
        b = Vector2(-a.y, a.x) * 0.4
        lines(surface, [pos - a, pos - a * 0.3 + b, pos + a * 0.4 + b * 1.2, pos + a], light, alpha, 3)
    elif name == "bolt":
        a = Vector2(math.cos(angle), math.sin(angle)) * size
        bolt(surface, pos - a, pos + a, main, alpha, rng or random, 3, 4)
        bolt(surface, pos - a, pos + a, light, alpha, rng or random, 1, 4)


# --- une animation -------------------------------------------------------------------
class _Anim:
    def __init__(self, kind, element, attack=None, pos=None, direction=None, radius=30.0, hostile=False,
                 strong=False, motif=None):
        self.kind, self.hostile, self.strong = kind, hostile, strong
        self.motif = motif                      # animation propre à la capacité (src/ui/move_fx.py) ou None
        self.element = element
        self.style = STYLES[element]
        self.attack, self.t = attack, 0.0
        self.radius = radius
        self.dir = Vector2(direction) if direction is not None and Vector2(direction).length_squared() else Vector2(1, 0)
        self.owner, self.off, self.fixed = None, None, Vector2(pos) if pos is not None else Vector2()
        self.rng = random.Random((id(attack) if attack else id(self)) & 0xFFFF)
        self.trail: deque = deque(maxlen=9)
        self.spin = self.rng.uniform(-6, 6)
        self.done = False
        self.dur = DUR.get(kind, 0.4)
        if kind in ("burst", "zone") and radius > 100:
            self.dur = 0.75
        if motif is not None:
            self.dur = motif.impact_dur if kind == "impact" else motif.dur
        n = {"melee": 7, "burst": int(min(26, 8 + radius / 8)), "zone": int(min(26, 8 + radius / 8)),
             "impact": 10 if strong else 6}.get(kind, 0)
        if motif is not None:
            n = 24
        self.parts = [(self.rng.uniform(0, math.tau), self.rng.uniform(0.55, 1.0), self.rng.uniform(0.7, 1.3),
                       self.rng.uniform(-4, 4)) for _ in range(n)]
        if attack is not None and kind in ("melee", "burst"):
            self.owner = attack.owner
            self.off = Vector2(attack.offset) if attack.offset is not None else Vector2()

    def pos(self) -> Vector2:
        if self.owner is not None and self.off is not None:
            return self.owner.pos + self.off
        if self.kind == "projectile" and self.attack is not None and self.attack.active:
            return Vector2(self.attack.pos)
        return Vector2(self.fixed)

    @property
    def k(self) -> float:
        return min(1.0, self.t / self.dur)


class AttackFX:
    def __init__(self):
        self.anims: list = []

    # --- création ---
    def spawn(self, attack, hostile: bool = False) -> None:
        from .move_fx import MOTIFS                        # (import tardif : move_fx dépend de ce module)
        element = PType.FEU if attack.name == "Explosion" else attack.element     # l'explosion est de feu
        motif = MOTIFS.get(attack.move_id)                  # animation propre à la vraie capacité, si elle en a une
        if attack.kind == "projectile":
            a = _Anim("projectile", element, attack, attack.pos, attack.velocity, attack.radius, hostile, motif=motif)
        elif attack.kind == "melee":
            a = _Anim("melee", element, attack, attack.pos, attack.offset, attack.radius, hostile, motif=motif)
        else:                                      # "burst" (autour du lanceur) ou "zone" (posée au sol)
            a = _Anim(attack.kind, element, attack, attack.pos, None, attack.radius, hostile, motif=motif)
        self.anims.append(a)

    def hit(self, pos, element, strong: bool = False) -> None:
        """Flash d'impact sur une cible touchée (plus gros si super efficace)."""
        self.anims.append(_Anim("impact", element, None, pos, None, 44 if strong else 28, strong=strong))

    # --- vie ---
    def update(self, dt: float) -> None:
        for a in self.anims:
            if a.kind == "projectile":
                if a.attack.active:
                    p = a.pos()
                    if not a.trail or p.distance_to(a.trail[-1]) > 5:
                        a.trail.append(p)
                    a.fixed = p
                    a.t += dt
                else:                                              # fin du projectile -> petit impact
                    a.done = True
                    imp = a.motif if a.motif is not None and a.motif.impact is not None else None
                    self.anims.append(_Anim("impact", a.element, None, a.fixed, None, 24 + a.radius, motif=imp))
            else:
                a.t += dt
                a.done = a.t >= a.dur
        self.anims = [a for a in self.anims if not a.done]

    # --- rendu ---
    def draw(self, surface) -> None:
        for a in self.anims:
            m = a.motif
            fn = (m.impact if a.kind == "impact" else m.draw) if m is not None else None
            if fn is not None:
                fn(self, surface, a)
                if a.kind != "impact":
                    self._warn(surface, a, a.pos(), a.radius)
            else:
                getattr(self, "_draw_" + a.kind)(surface, a)

    def _warn(self, surface, a, pos, r) -> None:
        if a.hostile:                                              # liseré rouge : attention, ça fait mal
            circle(surface, pos, int(r) + 3, (255, 90, 80), 150, 2)

    def _draw_melee(self, surface, a: _Anim) -> None:
        main, dark, light, name = a.style
        k, pos = a.k, a.pos()
        d = a.dir.normalize()
        base = math.atan2(d.y, d.x)
        centre = a.owner.pos if a.owner is not None else pos - d * 40
        R = (pos - centre).length() + 14
        head = ease_out(min(1.0, k / 0.55))
        fade = 1 - max(0.0, (k - 0.45) / 0.55)
        a0, a1 = math.radians(-78), math.radians(78)
        ha = lerp(a0, a1, head)
        ta = max(a0, ha - math.radians(120))
        n = 14
        outer, inner = [], []
        for i in range(n + 1):
            u = i / n
            ang = base + lerp(ta, ha, u)
            w = 17 * (u ** 0.8)                                    # fin à la queue, épais à la tête
            c, s = math.cos(ang), math.sin(ang)
            outer.append((centre.x + c * (R + w * 0.4), centre.y + s * (R + w * 0.4)))
            inner.append((centre.x + c * (R - w), centre.y + s * (R - w)))
        glow(surface, pos, a.radius * 1.6, main, int(120 * fade))
        poly(surface, outer + inner[::-1], dark, int(230 * fade))
        mid = [((o[0] + i[0]) / 2, (o[1] + i[1]) / 2) for o, i in zip(outer, inner)]
        lines(surface, mid[2:], light, int(255 * fade), 3)
        if k > 0.12:                                               # étoile d'impact + éclats
            e = ease_out((k - 0.12) / 0.5)
            shape(surface, "star", pos, 8 + 16 * e, base + k * 2, light, int(255 * (1 - e)))
            for ang, sp, sz, rot in a.parts:
                pa = base + (ang - math.pi) * 0.5
                pp = pos + Vector2(math.cos(pa), math.sin(pa)) * (10 + 46 * sp * e)
                particle(surface, a.style, name, pp, 5 * sz * (1 - 0.5 * k), pa + rot * k, int(255 * (1 - k)), a.rng)
        self._warn(surface, a, pos, a.radius)

    def _draw_burst(self, surface, a: _Anim) -> None:
        main, dark, light, name = a.style
        k, c = a.k, a.pos()
        e = ease_out(k)
        R = a.radius
        r = R * (0.3 + 0.7 * e)
        fade = 1 - k * k
        glow(surface, c, R * 1.1, main, int(150 * fade))
        circle(surface, c, int(r), main, int(70 * fade))
        w = max(3, int(14 * (1 - k)))
        circle(surface, c, int(r), dark, int(255 * fade), w)                    # anneau en deux tons :
        circle(surface, c, int(r), main, int(255 * fade), max(2, w // 2))       # lisible aussi pour les types sombres
        circle(surface, c, int(r * 0.82), light, int(200 * fade), 3)
        if name == "bolt":                                         # éclairs radiaux
            for i, (ang, sp, sz, rot) in enumerate(a.parts[:6]):
                bolt(surface, c, c + Vector2(math.cos(ang), math.sin(ang)) * r, light, int(255 * fade), a.rng, 3)
        for ang, sp, sz, rot in a.parts:
            pr = r * (0.55 + 0.45 * sp)
            pa = ang + (a.t * 5 if name in ("leaf", "wind", "diamond") else 0)      # certains tournent
            pp = c + Vector2(math.cos(pa), math.sin(pa)) * pr
            particle(surface, a.style, name, pp, (8 + R / 14) * sz * (1 - 0.45 * k), pa + rot * k, int(255 * fade), a.rng)
        self._warn(surface, a, c, R)

    _draw_zone = _draw_burst

    def _draw_impact(self, surface, a: _Anim) -> None:
        main, dark, light, name = a.style
        k, c = a.k, a.pos()
        e = ease_out(k)
        fade = 1 - k
        glow(surface, c, a.radius * 1.4, light, int(200 * fade))
        circle(surface, c, int(a.radius * (0.2 + 0.8 * e)), main, int(255 * fade), max(2, int(6 * fade)))
        shape(surface, "star", c, 6 + a.radius * 0.5 * e, a.t * 6, light, int(255 * fade))
        for ang, sp, sz, rot in a.parts:
            pp = c + Vector2(math.cos(ang), math.sin(ang)) * (a.radius * 0.5 + a.radius * 1.1 * sp * e)
            particle(surface, a.style, name, pp, 4.5 * sz * (1 - 0.4 * k), ang + rot * k, int(255 * fade), a.rng)

    def _draw_projectile(self, surface, a: _Anim) -> None:
        main, dark, light, name = a.style
        pos = a.pos()
        d = a.dir.normalize()
        ang = math.atan2(d.y, d.x)
        r = a.radius
        n = len(a.trail)
        for i, p in enumerate(a.trail):                            # traînée qui rétrécit et s'estompe
            u = (i + 1) / (n + 1)
            if name in ("bubble", "drop"):
                circle(surface, p + Vector2(a.rng.uniform(-3, 3), a.rng.uniform(-3, 3)), max(1, int(r * 0.5 * u)), main, int(150 * u), 2)
            elif name == "bolt":
                if i:
                    bolt(surface, a.trail[i - 1], p, main, int(220 * u), a.rng, 2, 2)
            else:
                glow(surface, p, r * (0.6 + 1.6 * u), dark, int(150 * u))
        glow(surface, pos, r * 3.2, main, 150)
        if name == "flame":
            wob = 1 + 0.18 * math.sin(a.t * 40)
            shape(surface, "flame", pos, r * 1.7 * wob, ang, dark)
            shape(surface, "flame", pos, r * 1.1 * wob, ang, main)
            shape(surface, "flame", pos, r * 0.55, ang, light)
        elif name in ("leaf", "shard", "rock", "hex", "diamond", "star"):
            spin = ang + a.t * (14 if name in ("leaf", "star", "rock", "hex") else 0)
            shape(surface, name, pos, r * 1.5, spin, dark)
            shape(surface, name, pos, r * 1.0, spin, main)
            circle(surface, pos, max(1, int(r * 0.3)), light)
        elif name == "bolt":
            circle(surface, pos, int(r * 1.1), main)
            circle(surface, pos, int(r * 0.6), light)
            for _ in range(3):
                bolt(surface, pos, pos + Vector2(a.rng.uniform(-1, 1), a.rng.uniform(-1, 1)).normalize() * r * 2.4, light, 230, a.rng, 2, 3)
        elif name == "wisp":
            glow(surface, pos, r * 2.6, dark, 220)
            circle(surface, pos, int(r * 1.05), dark)
            circle(surface, pos, int(r * 1.15), light, 255, 2)                  # liseré clair : visible sur fond sombre
            circle(surface, pos, int(r * 0.7), main)
            circle(surface, pos, int(r * 0.32), light)
        elif name == "wind":
            particle(surface, a.style, "wind", pos, r * 2.2, ang, 255)
        else:                                                      # drop, bubble, ring, streak : orbe
            circle(surface, pos, int(r * 1.15), dark)
            circle(surface, pos, int(r * 0.85), main)
            circle(surface, pos - Vector2(r * 0.25, r * 0.25), max(1, int(r * 0.3)), light)
        self._warn(surface, a, pos, r * 1.2)
