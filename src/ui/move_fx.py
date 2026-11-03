"""Une animation par capacité, d'après sa description officielle dans les jeux (dessinées par le code).

Chaque capacité apprise a son « motif » : Morsure = deux rangées de canines qui se referment, Léchouille =
grand coup de langue, Griffe = trois griffures, Vive-Attaque = traînée de vitesse, Tempête Verte = tempête de
feuilles, Magie Florale = bouquet de fleurs piégé, Lance-Flammes = torrent de flammes, etc. Les couleurs viennent
du type de la capacité. Les capacités sans motif (ennemis, boss) gardent les animations génériques d'attack_fx.
"""
import math
from dataclasses import dataclass

import pygame
from pygame import Vector2

from . import attack_fx as F
from .attack_fx import circle, ease_out, glow, lerp, lines, poly, shape

TAU = math.tau


@dataclass(frozen=True)
class Motif:
    draw: object = None            # draw(fx, surface, anim) pour la phase principale
    dur: float = 0.4               # durée des motifs de mêlée / zone
    impact: object = None          # animation de fin d'un projectile (sinon l'impact générique)
    impact_dur: float = 0.35


# ---------- outils ----------------------------------------------------------------------
def basis(a):
    main, dark, light, name = a.style
    d = Vector2(a.dir)
    d = d.normalize() if d.length_squared() else Vector2(1, 0)
    pos = a.pos()
    origin = Vector2(a.owner.pos) if a.owner is not None else pos - d * 44
    return main, dark, light, d, math.atan2(d.y, d.x), pos, origin


def rot(v: Vector2, deg: float) -> Vector2:
    return v.rotate(deg)


def tapered(s, p0, p1, width, color, alpha, head=1.0, tail=0.0, steps=10):
    """Trait effilé entre p0 et p1, de la fraction `tail` à la fraction `head` de sa longueur."""
    p0, p1 = Vector2(p0), Vector2(p1)
    dv = p1 - p0
    if dv.length() < 1 or head <= tail:
        return
    n = dv.normalize()
    perp = Vector2(-n.y, n.x)
    a, b = p0 + dv * tail, p0 + dv * head
    left, right = [], []
    for i in range(steps + 1):
        u = i / steps
        q, w = a + (b - a) * u, width * math.sin(math.pi * u) * 0.5
        left.append(q + perp * w)
        right.append(q - perp * w)
    poly(s, left + right[::-1], color, alpha)


def slash_mark(s, c, v, length, width, kk, dark, light, alpha=255):
    """Coupure qui se trace puis s'efface (kk de 0 à 1+)."""
    if kk <= 0:
        return
    head = ease_out(min(1.0, kk / 0.6))
    tail = min(0.95, max(0.0, (kk - 0.55) / 0.45))
    al = int(alpha * (1 - max(0.0, (kk - 0.75) / 0.25)))
    p0, p1 = c - v * length / 2, c + v * length / 2
    tapered(s, p0, p1, width * 1.7, dark, al, head, tail)
    tapered(s, p0, p1, width * 0.7, light, al, head, tail)


def star(s, pos, size, color, alpha=255, angle=0.0):
    shape(s, "star", pos, size, angle, color, alpha)


def poly_star(s, c, r_out, r_in, n, rot_a, color, alpha=255):
    pts = []
    for i in range(2 * n):
        r = r_out if i % 2 == 0 else r_in
        a = rot_a + i * math.pi / n
        pts.append((c[0] + math.cos(a) * r, c[1] + math.sin(a) * r))
    poly(s, pts, color, alpha)


def ring(s, c, r, w, color, alpha=255):
    if r > 1:
        circle(s, c, int(r), color, alpha, max(1, int(w)))


def rays(s, c, r0, r1, n, rot_a, color, alpha, width=3):
    for i in range(n):
        a = rot_a + i * TAU / n
        v = Vector2(math.cos(a), math.sin(a))
        lines(s, [c + v * r0, c + v * r1], color, alpha, width)


def note(s, pos, size, color, alpha=255, light=None):
    """Croche : tête ovale, hampe, crochet."""
    x, y = pos
    circle(s, (x, y), max(2, int(size * 0.5)), color, alpha)
    lines(s, [(x + size * 0.45, y), (x + size * 0.45, y - size * 2.2)], color, alpha, max(2, int(size * 0.28)))
    poly(s, [(x + size * 0.45, y - size * 2.2), (x + size * 1.3, y - size * 1.6), (x + size * 0.45, y - size * 1.4)],
         color, alpha)
    if light:
        circle(s, (x - size * 0.1, y - size * 0.1), max(1, int(size * 0.18)), light, alpha)


def heart(s, pos, size, color, alpha=255):
    pts = []
    for i in range(20):
        t = i / 20 * TAU
        pts.append((pos[0] + size * 0.06 * 16 * math.sin(t) ** 3,
                    pos[1] - size * 0.06 * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))))
    poly(s, pts, color, alpha)


def flower(s, pos, size, petal, centre, alpha=255, rot_a=0.0):
    for i in range(5):
        a = rot_a + i * TAU / 5
        circle(s, (pos[0] + math.cos(a) * size * 0.55, pos[1] + math.sin(a) * size * 0.55), max(2, int(size * 0.45)), petal, alpha)
    circle(s, pos, max(2, int(size * 0.35)), centre, alpha)


def p_at(a, i, dist, spread=TAU, center_ang=0.0):
    """i-ième éclat de l'animation : (position relative, taille, rotation) déterministes."""
    ang, sp, sz, rt = a.parts[i % len(a.parts)]
    ang = center_ang + (ang / TAU - 0.5) * spread
    return Vector2(math.cos(ang), math.sin(ang)) * dist * sp, sz, rt


# ---------- MÊLÉE ---------------------------------------------------------------------------
def m_scratch(fx, s, a):
    main, dark, light, d, base, pos, O = basis(a)
    perp = Vector2(-d.y, d.x)
    v = rot(d, 62)
    for i, off in enumerate((-17, 0, 17)):                      # trois griffures parallèles
        slash_mark(s, pos + perp * off + d * (i % 2) * 4, v, 96, 9, (a.k - 0.09 * i) / 0.5, dark, light)
    if a.k > 0.12:
        star(s, pos, 10 + 12 * ease_out((a.k - 0.12) / 0.4), light, int(255 * (1 - a.k)), a.k * 3)


def m_impact(heavy):
    def draw(fx, s, a):
        """Charge / Écras'Face / Ultimawashi : élan puis choc."""
        main, dark, light, d, base, pos, O = basis(a)
        k = a.k
        if k < 0.4:                                              # traînées de l'élan
            for i in range(4):
                off = Vector2(-d.y, d.x) * (i - 1.5) * 9
                tapered(s, O + off - d * 24, pos + off - d * 6, 6, light, int(210 * (1 - k / 0.4)), 1.0, 0.0)
        e = ease_out(max(0.0, (k - 0.15) / 0.5))
        glow(s, pos, (36 + 26 * heavy) * (0.6 + e), main, int(170 * (1 - k)))
        ring(s, pos, (14 + 34 * heavy) * (0.3 + e), max(2, 7 * (1 - k)), dark, int(255 * (1 - k)))
        ring(s, pos, (10 + 28 * heavy) * (0.3 + e), 3, light, int(255 * (1 - k)))
        star(s, pos, (12 + 16 * heavy) * (0.5 + e), light, int(255 * (1 - k)), 0.3)
        if heavy > 0.5:
            rays(s, pos, 18, 18 + 48 * e, 10, 0.2, light, int(230 * (1 - k)), 3)
        for i in range(8):
            off, sz, rt = p_at(a, i, 26 + 30 * heavy)
            F.shape(s, "rock", pos + off * e * 1.6, 3 + 2 * sz, rt + k * 4, dark, int(255 * (1 - k)))
    return draw


def m_pound(fx, s, a):
    main, dark, light, d, base, pos, O = basis(a)
    k = a.k
    sw = ease_out(min(1.0, k / 0.35))
    c = pos - d * 28
    ang0, ang1 = base - math.radians(95), base + math.radians(5)       # patte / queue qui s'abat d'en haut
    pts_o, pts_i = [], []
    for i in range(10):
        ang = lerp(ang0, ang0 + (ang1 - ang0) * sw, i / 9)
        w = 8 + 16 * (i / 9)
        pts_o.append((c.x + math.cos(ang) * (56 + w * 0.4), c.y + math.sin(ang) * (56 + w * 0.4)))
        pts_i.append((c.x + math.cos(ang) * (56 - w), c.y + math.sin(ang) * (56 - w)))
    al = int(255 * (1 - max(0.0, (k - 0.5) / 0.5)))
    poly(s, pts_o + pts_i[::-1], dark, al)
    poly(s, [(x * 0.5 + y * 0.5, u * 0.5 + v * 0.5) for (x, u), (y, v) in zip(pts_o, pts_i)] + [pts_i[-1], pts_o[-1]], light, int(al * 0.8))
    if k > 0.3:                                                   # nuage de poussière à l'impact
        e = ease_out((k - 0.3) / 0.6)
        for i in range(7):
            off, sz, rt = p_at(a, i, 40)
            circle(s, pos + Vector2(off.x, off.y * 0.4) * e, int(5 + 7 * sz * (1 - e * 0.5)), (225, 220, 205), int(190 * (1 - e)))
        ring(s, pos, 14 + 30 * e, 4, light, int(220 * (1 - e)))


def m_streak(water):
    def draw(fx, s, a):
        """Vive-Attaque / Aqua-Jet : « fonce si vite qu'on la discerne à peine »."""
        main, dark, light, d, base, pos, O = basis(a)
        k = a.k
        fade = 1 - k
        perp = Vector2(-d.y, d.x)
        for i in range(7):
            off = perp * (i - 3) * 8
            L = 70 + 40 * ((i * 37) % 5) / 4
            tapered(s, O + off - d * L, pos + off + d * 14, 7 if water else 5, main if water else light, int(235 * fade),
                    1.0, min(0.9, k * 1.1))
        if water:                                                 # voile d'eau qui entoure le lanceur
            glow(s, (O + pos) / 2, 62, main, int(150 * fade))
            for i in range(9):
                off, sz, rt = p_at(a, i, 46)
                F.shape(s, "drop", O + off * 0.8 - d * 14 * i * k, 4 + 3 * sz, rt + base, light, int(240 * fade))
        else:
            glow(s, pos, 34, light, int(160 * fade))
        star(s, pos, 8 + 16 * ease_out(k), light, int(255 * fade), k * 4)
    return draw


def m_lick(fx, s, a):
    main, dark, light, d, base, pos, O = basis(a)
    k = a.k
    out = ease_out(min(1.0, k / 0.4))
    back = max(0.0, (k - 0.6) / 0.4)
    ext = out * (1 - back)
    perp = Vector2(-d.y, d.x)
    pts = []
    tip = O + (pos - O + d * 38) * ext
    for i in range(14):
        u = i / 13
        q = O + (tip - O) * u
        pts.append(q + perp * math.sin(u * 7 + a.t * 14) * 7 * u)
    if len(pts) > 1 and ext > 0.02:
        lines(s, pts, dark, 255, 26)
        lines(s, pts, (240, 120, 170), 255, 20)               # grande langue rose
        lines(s, pts, (255, 190, 215), 255, 6)
        circle(s, pts[-1], 17, (240, 120, 170))
        circle(s, pts[-1], 7, (255, 190, 215))
    if 0.35 < k < 0.8:                                           # bave
        for i in range(5):
            off, sz, rt = p_at(a, i, 26)
            F.shape(s, "drop", pos + off * (k - 0.3) * 1.5, 4 + 2 * sz, 1.57, main, int(230 * (1 - k)))
        star(s, pos, 10 + 12 * (k - 0.35), light, int(220 * (1 - k)))


def m_sweep(fx, s, a):
    main, dark, light, d, base, pos, O = basis(a)
    k = a.k
    sw = ease_out(min(1.0, k / 0.4))
    fade = 1 - max(0.0, (k - 0.5) / 0.5)
    c = O + d * 6
    n = 16
    outer, inner = [], []
    for i in range(n + 1):
        u = i / n
        ang = base + math.radians(-105 + 210 * sw * u)
        wd = 14 * math.sin(math.pi * u) + 2
        r = 52
        outer.append((c.x + math.cos(ang) * (r + wd), c.y + math.sin(ang) * (r + wd) * 0.5 + 10))
        inner.append((c.x + math.cos(ang) * (r - wd), c.y + math.sin(ang) * (r - wd) * 0.5 + 10))
    poly(s, outer + inner[::-1], dark, int(235 * fade))
    lines(s, [((o[0] + i[0]) / 2, (o[1] + i[1]) / 2) for o, i in zip(outer, inner)][2:], light, int(255 * fade), 3)
    for i in range(6):                                           # poussière au ras du sol
        off, sz, rt = p_at(a, i, 50)
        circle(s, pos + Vector2(off.x, abs(off.y) * 0.3 + 12), int(4 + 4 * sz), (215, 205, 185), int(170 * fade * sw))


def m_double(fx, s, a):
    main, dark, light, d, base, pos, O = basis(a)
    for i in range(2):
        kk = (a.k - 0.38 * i) / 0.5
        if kk <= 0:
            continue
        sign = -1 if i else 1
        c = pos + Vector2(-d.y, d.x) * (-10 * sign)
        slash_mark(s, c, rot(d, 70 * sign), 92, 10, kk, dark, light)
        if 0.1 < kk < 0.7:
            star(s, c, 8 + 10 * kk, light, int(255 * (1 - kk)), kk * 3)


def m_bite(fx, s, a):
    main, dark, light, d, base, pos, O = basis(a)
    k = a.k
    close = ease_out(min(1.0, k / 0.42))
    gap = lerp(64, 4, close)
    fade = 1 - max(0.0, (k - 0.6) / 0.4)
    perp = Vector2(-d.y, d.x)
    for side in (-1, 1):                                         # mâchoire du haut / du bas : 5 canines
        for i in range(6):
            off = (i - 2.5) * 19
            base_pt = pos + perp * side * gap + d * off
            tip = base_pt - perp * side * (34 if i in (1, 4) else 26)      # les canines (1 et 4) sont plus longues
            pts = [base_pt + d * 9, base_pt - d * 9, tip]
            poly(s, pts, (255, 255, 255), int(255 * fade))
            poly(s, pts, (40, 30, 50), int(255 * fade), 2)
    if k > 0.38:
        star(s, pos, 10 + 14 * (k - 0.38) / 0.4, light, int(255 * (1 - k)), 0.5)
        ring(s, pos, 10 + 30 * (k - 0.38), 3, light, int(220 * (1 - k)))


def m_uturn(fx, s, a):
    main, dark, light, d, base, pos, O = basis(a)
    k = a.k
    perp = Vector2(-d.y, d.x)
    out = ease_out(min(1.0, k / 0.38))
    back = ease_out(max(0.0, (k - 0.38) / 0.5))
    fade = 1 - max(0.0, (k - 0.7) / 0.3)
    pts = [O + (pos - O) * out + perp * math.sin(out * math.pi) * 14]
    if back > 0:                                                  # trajet en « U » : il revient en arrière
        pts = [O + (pos - O) * (1 - back * 0.0) * min(1, out)]
        for i in range(10):
            u = i / 9 * back
            pts.append(pos + (O - pos) * u - d * 70 * math.sin(math.pi * u) * 0.0 + perp * 34 * math.sin(math.pi * u))
    if len(pts) > 1:
        lines(s, pts, dark, int(230 * fade), 12)
        lines(s, pts, light, int(255 * fade), 4)
    head = pts[-1]
    poly(s, [head + d * 12 * (1 if back == 0 else -1), head + perp * 9, head - perp * 9], light, int(255 * fade))
    if 0.3 < k < 0.7:
        star(s, pos, 12 + 12 * (k - 0.3), light, int(255 * (1 - k)), k * 5)


def m_slash(dark_variant):
    def draw(fx, s, a):
        """Tranche / Tranche-Nuit : coupure nette, taux de critiques élevé."""
        main, dark, light, d, base, pos, O = basis(a)
        k = a.k
        v = rot(d, -50)
        if dark_variant:                                          # traînée d'ombre
            glow(s, pos, 80, dark, int(150 * (1 - k)))
        slash_mark(s, pos, v, 150, 15, k / 0.5, dark, light)
        slash_mark(s, pos + rot(d, 90) * 9, v, 90, 6, (k - 0.1) / 0.5, dark, light, 180)
        if a.attack is not None and getattr(a.attack, "crit_hit", False):      # coup critique : flash
            star(s, pos, 30 * ease_out(k), (255, 255, 255), int(255 * (1 - k)), 0.4)
        for i in range(6):
            off, sz, rt = p_at(a, i, 46)
            F.shape(s, "diamond", pos + off * ease_out(k), 3 + 2 * sz, rt, light if not dark_variant else main, int(255 * (1 - k)))
    return draw


def m_chop(fx, s, a):
    main, dark, light, d, base, pos, O = basis(a)
    k = a.k
    sw = ease_out(min(1.0, k / 0.3))
    top = pos + Vector2(0, -92) + (1 - sw) * Vector2(0, -20)
    cur = top + (pos - top) * sw
    perp = Vector2(1, 0)
    fade = 1 - max(0.0, (k - 0.55) / 0.45)
    tapered(s, top - Vector2(0, 20), cur + Vector2(0, 8), 30, dark, int(240 * fade), 1.0, max(0.0, sw - 0.65))
    tapered(s, top - Vector2(0, 20), cur + Vector2(0, 8), 12, light, int(255 * fade), 1.0, max(0.0, sw - 0.65))
    if k > 0.25:
        e = ease_out((k - 0.25) / 0.5)
        ring(s, pos, 12 + 30 * e, 4, light, int(230 * (1 - k)))
        for i in range(6):                                        # objet qui saute (Sabotage)
            off, sz, rt = p_at(a, i, 50)
            F.shape(s, "rock", pos + Vector2(off.x, -abs(off.y) * 1.2) * e + Vector2(0, 30 * e * e), 3 + 3 * sz, rt + k * 6, main, int(255 * (1 - k)))


def m_hug(fx, s, a):
    main, dark, light, d, base, pos, O = basis(a)
    k = a.k
    e = ease_out(k)
    fade = 1 - max(0.0, (k - 0.6) / 0.4)
    for i in range(7):                                            # nuage de bagarre
        off, sz, rt = p_at(a, i, 22)
        circle(s, pos + off * (0.5 + 0.5 * math.sin(k * 20 + i)) * 0.7, int(11 + 8 * sz), (255, 245, 250), int(235 * fade))
        circle(s, pos + off * 0.7, int(7 + 5 * sz), (255, 215, 235), int(200 * fade))
    for i in range(6):                                            # cœurs et étoiles
        off, sz, rt = p_at(a, i + 8, 60)
        pp = pos + off * e + Vector2(0, -26 * e)
        if i % 2 == 0:
            heart(s, pp, 7 + 5 * sz, main, int(255 * fade))
        else:
            star(s, pp, 5 + 4 * sz, light, int(255 * fade), rt + k * 5)


def m_wings(fx, s, a):
    main, dark, light, d, base, pos, O = basis(a)
    k = a.k
    sw = ease_out(min(1.0, k / 0.4))
    fade = 1 - max(0.0, (k - 0.55) / 0.45)
    perp = Vector2(-d.y, d.x)
    for side in (-1, 1):                                          # deux grandes ailes déployées
        for i in range(7):
            u = i / 6
            ang = base + side * math.radians(25 + 80 * u * sw)
            v = Vector2(math.cos(ang), math.sin(ang))
            L = 78 - 18 * u
            tapered(s, pos - d * 8, pos - d * 8 + v * L, 12, (255, 255, 255), int(255 * fade), 1.0, 0.0)
            tapered(s, pos - d * 8, pos - d * 8 + v * L, 12, dark, int(120 * fade), 1.0, 0.0)
    glow(s, pos, 46, light, int(150 * fade))
    for i in range(6):
        off, sz, rt = p_at(a, i, 60)
        F.shape(s, "leaf", pos + off * ease_out(k), 4 + 2 * sz, rt + k * 4, (255, 255, 255), int(230 * fade))


def m_flurry(fists):
    def draw(fx, s, a):
        """Acrobatie : attaque agile ; Close Combat : corps à corps sans se protéger."""
        main, dark, light, d, base, pos, O = basis(a)
        k = a.k
        n = 9
        for i in range(n):
            t0 = i / n * 0.55
            kk = (k - t0) / 0.3
            if kk <= 0 or kk >= 1:
                continue
            off, sz, rt = p_at(a, i, 34)
            c = pos + off
            if fists:
                star(s, c, 7 + 10 * ease_out(kk), light, int(255 * (1 - kk)), rt)
                ring(s, c, 4 + 16 * kk, 3, main, int(255 * (1 - kk)))
            else:
                slash_mark(s, c, Vector2(math.cos(rt), math.sin(rt)), 64, 7, kk, dark, light)
        if not fists:
            ring(s, pos, 28 + 24 * ease_out(k), 3, light, int(200 * (1 - k)))
        else:
            for i in range(3):
                tapered(s, O + Vector2(-d.y, d.x) * (i - 1) * 12, pos + Vector2(-d.y, d.x) * (i - 1) * 6, 6, light, int(200 * (1 - k)), 1.0, k)
    return draw


def m_slam_water(fx, s, a):
    main, dark, light, d, base, pos, O = basis(a)
    k = a.k
    sw = ease_out(min(1.0, k / 0.4))
    fade = 1 - max(0.0, (k - 0.5) / 0.5)
    pts_o, pts_i = [], []
    for i in range(16):                                           # vague qui s'abat
        u = i / 15
        ang = base + math.radians(-130 + 150 * sw * u)
        r = 62
        w = 20 * math.sin(math.pi * u) + 3
        pts_o.append((pos.x - d.x * 30 + math.cos(ang) * (r + w), pos.y - d.y * 30 + math.sin(ang) * (r + w)))
        pts_i.append((pos.x - d.x * 30 + math.cos(ang) * (r - w), pos.y - d.y * 30 + math.sin(ang) * (r - w)))
    poly(s, pts_o + pts_i[::-1], main, int(230 * fade))
    lines(s, pts_o, light, int(255 * fade), 4)
    if k > 0.3:
        e = ease_out((k - 0.3) / 0.6)
        ring(s, pos, 14 + 40 * e, 4, light, int(230 * (1 - k)))
        for i in range(14):
            off, sz, rt = p_at(a, i, 66)
            F.shape(s, "drop", pos + Vector2(off.x, -abs(off.y)) * e + Vector2(0, 34 * e * e), 4 + 3 * sz, 1.57, light, int(255 * (1 - k)))


def m_wave_crash(fx, s, a):
    main, dark, light, d, base, pos, O = basis(a)
    k = a.k
    fade = 1 - max(0.0, (k - 0.65) / 0.35)
    if k < 0.55:                                                  # se recouvre d'eau
        for i in range(3):
            r = 20 + (k * 2.2 + i * 0.33) % 1 * 40
            ring(s, O, r, 4, main, int(220 * (1 - r / 64)))
        glow(s, O, 56, main, int(180 * min(1, k * 3)))
        for i in range(10):
            off, sz, rt = p_at(a, i, 40)
            F.shape(s, "drop", O + off * (0.4 + k) - Vector2(0, 30 * k), 4 + 2 * sz, rt, light, 230)
    else:                                                         # charge enveloppée d'une vague
        e = ease_out((k - 0.55) / 0.45)
        cur = O + (pos - O) * e
        glow(s, cur, 70, main, int(200 * fade))
        for i in range(5):
            u = i / 4 - 0.5
            tip = cur + Vector2(-d.y, d.x) * u * 70 - d * (10 + abs(u) * 30)
            F.shape(s, "drop", tip, 9 + 4 * (1 - abs(u)), base, main, int(255 * fade))
        ring(s, pos, 20 + 40 * e, 5, light, int(255 * fade))
        for i in range(10):
            off, sz, rt = p_at(a, i + 10, 70)
            F.shape(s, "drop", pos + Vector2(off.x, -abs(off.y)) * e, 5 + 3 * sz, 1.57, light, int(255 * fade))


def m_water_dance(fx, s, a):
    main, dark, light, d, base, pos, O = basis(a)
    k = a.k
    fade = 1 - max(0.0, (k - 0.6) / 0.4)
    for i in range(3):                                            # ondulations de pas de danse
        r = 22 + ((k * 1.6 + i / 3) % 1) * 58
        circle(s, O, int(r), main, int(70 * (1 - r / 80)), 0)
        ring(s, O, r, 3, light, int(230 * (1 - r / 80)) * (1 if fade else 0))
    for i in range(14):                                           # bulles en spirale
        u = (i / 14 + k * 0.8) % 1
        ang = i * 0.9 + k * 7
        rr = 14 + u * 60
        F.particle(s, a.style, "bubble", O + Vector2(math.cos(ang), math.sin(ang)) * rr, 4 + 3 * (1 - u), ang, int(235 * (1 - u) * fade))
    slash_mark(s, pos, rot(d, 75), 100, 9, (k - 0.1) / 0.5, dark, light)


# ---------- ZONES -----------------------------------------------------------------------------
def z_notes(fx, s, a):
    main, dark, light, d, base, pos, O = basis(a)
    k = a.k
    e = ease_out(k)
    R = a.radius
    fade = 1 - max(0.0, (k - 0.6) / 0.4)
    ring(s, pos, R * (0.3 + 0.7 * e), 3, main, int(120 * fade))
    for i in range(10):                                           # notes de musique qui s'écartent
        ang = i / 10 * TAU + k * 2.4
        rr = R * (0.25 + 0.75 * e) * (0.7 + 0.3 * ((i * 7) % 3) / 2)
        pp = pos + Vector2(math.cos(ang), math.sin(ang)) * rr
        note(s, pp + Vector2(0, -6), 6 + (i % 3) * 1.5, main if i % 2 else light, int(255 * fade), dark)


def z_howl(fx, s, a):
    main, dark, light, d, base, pos, O = basis(a)
    k = a.k
    R = a.radius
    fade = 1 - k
    for j in range(3):                                            # arcs sonores sombres, du centre vers l'extérieur
        kk = k - j * 0.12
        if kk <= 0:
            continue
        r = R * (0.25 + 0.75 * ease_out(kk))
        for i in range(8):
            ang = i / 8 * TAU + 0.2
            pts = [pos + Vector2(math.cos(ang + da), math.sin(ang + da)) * r for da in (-0.22, -0.11, 0, 0.11, 0.22)]
            lines(s, pts, dark, int(250 * (1 - kk)), 9)
            lines(s, pts, main, int(255 * (1 - kk)), 4)
    glow(s, pos, R * 0.9, dark, int(120 * fade))
    for i in range(10):
        off, sz, rt = p_at(a, i, R * 0.9)
        F.shape(s, "shard", pos + off * ease_out(k), 4 + 2 * sz, rt, light, int(230 * fade))


def z_echo(fx, s, a):
    main, dark, light, d, base, pos, O = basis(a)
    k = a.k
    R = a.radius
    for j in range(4):                                            # anneaux concentriques : l'écho du cri
        kk = k - j * 0.1
        if kk <= 0:
            continue
        r = R * (0.2 + 0.8 * ease_out(kk))
        ring(s, pos, r, max(3, 12 * (1 - kk)), dark, int(230 * (1 - kk)))
        ring(s, pos, r, max(2, 6 * (1 - kk)), main, int(255 * (1 - kk)))
    rays(s, pos, R * 0.2, R * (0.35 + 0.6 * ease_out(k)), 14, k * 0.5, light, int(220 * (1 - k)), 3)
    glow(s, pos, R * 0.7, light, int(110 * (1 - k)))


def z_scorch(fx, s, a):
    main, dark, light, d, base, pos, O = basis(a)
    k = a.k
    R = a.radius
    fade = 1 - max(0.0, (k - 0.55) / 0.45)
    glow(s, pos, R * 1.15, main, int(150 * fade))
    for i in range(18):                                           # flammes qui calcinent la zone
        off, sz, rt = p_at(a, i, R * 0.95)
        grow = ease_out(min(1.0, (k - 0.04 * (i % 6)) / 0.35))
        flick = 1 + 0.2 * math.sin(a.t * 30 + i)
        pp = pos + Vector2(off.x, off.y * 0.7)
        shape(s, "flame", pp - Vector2(0, 10 * grow), (8 + 8 * sz) * grow * flick, -math.pi / 2, dark, int(255 * fade))
        shape(s, "flame", pp - Vector2(0, 10 * grow), (5 + 5 * sz) * grow * flick, -math.pi / 2, main, int(255 * fade))
        shape(s, "flame", pp - Vector2(0, 8 * grow), (2.5 + 2 * sz) * grow * flick, -math.pi / 2, light, int(255 * fade))


# ---------- PROJECTILES --------------------------------------------------------------------------
def pinfo(a):
    main, dark, light, name = a.style
    pos = a.pos()
    d = Vector2(a.dir)
    d = d.normalize() if d.length_squared() else Vector2(1, 0)
    return main, dark, light, pos, d, math.atan2(d.y, d.x), a.radius


def _trail(s, a, color, size=1.0, alpha=140):
    n = len(a.trail)
    for i, p in enumerate(a.trail):
        u = (i + 1) / (n + 1)
        glow(s, p, a.radius * (0.8 + 1.6 * u) * size, color, int(alpha * u))


def p_leaves(count, rainbow=False, big=False):
    def draw(fx, s, a):
        main, dark, light, pos, d, ang, r = pinfo(a)
        _trail(s, a, main, 1.0, 110)
        R = (34 if big else 12 if not rainbow else 18)
        spin = a.t * (14 if big else 9)
        for i in range(count):
            th = spin + i * TAU / count
            off = Vector2(math.cos(th), math.sin(th)) * R * (0.6 + 0.4 * ((i * 5) % 3) / 2)
            if big:
                off = Vector2(math.cos(th), math.sin(th) * 0.7) * (R * (0.4 + 0.6 * (i / count)))
            col = main
            if rainbow:                                           # feuilles étranges : toutes les couleurs
                hue = (a.t * 1.2 + i / count) % 1.0
                col = pygame.Color(0)
                col.hsva = (hue * 360, 55, 100, 100)
                col = (col.r, col.g, col.b)
            sz = r * (1.3 if not big else 1.1)
            shape(s, "leaf", pos + off, sz, th + 1.2, dark if not rainbow else (255, 255, 255), 255)
            shape(s, "leaf", pos + off, sz * 0.7, th + 1.2, col, 255)
        if rainbow or big:
            glow(s, pos, r * 3.4, main if not rainbow else (255, 255, 255), 120)
        if big:                                                   # anneaux de vent de la tempête
            for j in range(2):
                ring(s, pos, 22 + 14 * ((a.t * 2 + j * 0.5) % 1), 2, light, int(180 * (1 - ((a.t * 2 + j * 0.5) % 1))))
    return draw


def p_seed(fx, s, a):
    main, dark, light, pos, d, ang, r = pinfo(a)
    _trail(s, a, (200, 170, 60), 0.9, 100)
    shape(s, "drop", pos, r * 1.6, ang + 3.14, (70, 50, 25), 255)               # grosse graine
    shape(s, "drop", pos, r * 1.15, ang + 3.14, (206, 168, 70), 255)
    circle(s, pos + d * r * 0.2, max(1, int(r * 0.25)), (255, 240, 180))
    shape(s, "leaf", pos - d * r * 0.8 + Vector2(0, -r * 0.9), r * 0.7, -1.0, main, 255)


def p_orb(spin_ring, color_core=None):
    def draw(fx, s, a):
        main, dark, light, pos, d, ang, r = pinfo(a)
        _trail(s, a, dark, 1.0, 120)
        pul = 1 + 0.08 * math.sin(a.t * 18)
        glow(s, pos, r * 3.8 * pul, main, 160)
        circle(s, pos, int(r * 1.35 * pul), dark)
        circle(s, pos, int(r * 1.0 * pul), main)
        circle(s, pos, int(r * 0.55 * pul), color_core or light)
        if spin_ring:
            for i in range(5):
                th = a.t * 9 + i * TAU / 5
                F.particle(s, a.style, "star" if a.style[3] != "wisp" else "wisp", pos + Vector2(math.cos(th), math.sin(th)) * r * 2.0, 3, th, 235)
        circle(s, pos, int(r * 1.5), light, 255, 2)
    return draw


def p_ghostfire(fx, s, a):
    main, dark, light, pos, d, ang, r = pinfo(a)
    _trail(s, a, dark, 1.0, 120)
    for i in range(3):                                            # feux follets violets qui tournent
        th = a.t * 8 + i * TAU / 3
        pp = pos + Vector2(math.cos(th), math.sin(th)) * r * 1.5
        shape(s, "flame", pp, r * 1.6, th + 1.2, dark, 255)
        shape(s, "flame", pp, r * 1.0, th + 1.2, main, 255)
        shape(s, "flame", pp, r * 0.45, th + 1.2, light, 255)
    glow(s, pos, r * 3.2, main, 140)


def p_flower(fx, s, a):
    main, dark, light, pos, d, ang, r = pinfo(a)
    _trail(s, a, (255, 190, 230), 1.0, 110)
    glow(s, pos, r * 3.5, (255, 200, 235), 150)
    for i in range(5):                                            # bouquet : fleurs roses et blanches qui tournent
        th = a.t * 7 + i * TAU / 5
        pp = pos + Vector2(math.cos(th), math.sin(th)) * r * 1.25
        flower(s, pp, r * 1.15, (255, 170, 215) if i % 2 else (255, 255, 255), (255, 220, 90), 255, th)
    flower(s, pos, r * 1.2, (255, 255, 255), (255, 200, 60), 255, a.t * 4)
    shape(s, "leaf", pos - d * r * 1.8, r * 0.9, ang + 3.4, (90, 190, 90), 255)


def p_fire(big=False, torrent=False, ember=False):
    def draw(fx, s, a):
        main, dark, light, pos, d, ang, r = pinfo(a)
        flick = 1 + 0.22 * math.sin(a.t * 40)
        if torrent:                                               # torrent continu de flammes
            for i in range(9):
                back = pos - d * (i * 15 + 4)
                sz = r * (0.9 + (8 - i) * 0.30) * (1 + 0.2 * math.sin(a.t * 35 + i))
                jitter = Vector2(-d.y, d.x) * math.sin(a.t * 24 + i * 1.7) * (3 + (8 - i) * 1.0)
                shape(s, "flame", back + jitter, sz, ang, dark, int(255 - i * 18))
                shape(s, "flame", back + jitter, sz * 0.65, ang, main, int(255 - i * 18))
                shape(s, "flame", back + jitter, sz * 0.3, ang, light, int(255 - i * 18))
            glow(s, pos, r * 3.4, main, 150)
            return
        _trail(s, a, main, 0.8 if ember else 1.2, 120)
        glow(s, pos, r * (3.4 if big else 2.6), main, 160)
        shape(s, "flame", pos, r * (2.4 if big else 1.8) * flick, ang, dark, 255)
        shape(s, "flame", pos, r * (1.6 if big else 1.2) * flick, ang, main, 255)
        shape(s, "flame", pos, r * (0.8 if big else 0.6), ang, light, 255)
        if big:                                                   # Surchauffe : cœur chauffé à blanc
            circle(s, pos, int(r * 0.9), (255, 255, 235))
            ring(s, pos, r * (1.8 + (a.t * 3) % 1 * 1.4), 3, light, 200)
    return draw


def p_firestar(fx, s, a):
    main, dark, light, pos, d, ang, r = pinfo(a)
    _trail(s, a, main, 1.0, 120)
    glow(s, pos, r * 4.4, main, 170)
    spin = a.t * 3
    poly_star(s, pos, r * 3.0, r * 1.1, 5, spin, dark)               # étoile de feu (le « 大 » de Déflagration)
    poly_star(s, pos, r * 2.4, r * 0.9, 5, spin, main)
    poly_star(s, pos, r * 1.4, r * 0.6, 5, spin, light)
    for i in range(6):
        th = a.t * 10 + i
        shape(s, "flame", pos + Vector2(math.cos(th), math.sin(th)) * r * 2.8, r * 0.5, th, main, 220)


def p_notes(fx, s, a):
    main, dark, light, pos, d, ang, r = pinfo(a)
    n = len(a.trail)
    for i, p in enumerate(a.trail):                               # traînée de flammes
        u = (i + 1) / (n + 1)
        shape(s, "flame", p + Vector2(0, -3 * math.sin(a.t * 12 + i)), r * (0.5 + 1.1 * u), ang, dark, int(180 * u))
        shape(s, "flame", p, r * (0.3 + 0.7 * u), ang, main, int(220 * u))
    glow(s, pos, r * 3.2, main, 150)
    wob = math.sin(a.t * 14) * 4
    note(s, pos + Vector2(0, wob), r * 1.35, dark, 255)                       # notes de musique enflammées
    note(s, pos + Vector2(0, wob), r * 1.0, main, 255, light)
    note(s, pos + Vector2(-r * 2.4, -wob * 0.8 + 4), r * 0.9, main, 200, light)


def p_stream(water):
    def draw(fx, s, a):
        main, dark, light, pos, d, ang, r = pinfo(a)
        perp = Vector2(-d.y, d.x)
        for i in range(10):                                       # jet : gouttes alignées derrière la tête
            u = i / 10
            q = pos - d * (i * 11 + 2) + perp * math.sin(a.t * 22 + i * 1.3) * (1 + i * 0.7)
            shape(s, "drop", q, r * (1.5 - u * 0.9), ang, dark, int(255 - i * 20))
            shape(s, "drop", q, r * (1.0 - u * 0.6), ang, main, int(255 - i * 20))
        shape(s, "drop", pos, r * 1.5, ang, light, 255)
        glow(s, pos, r * 3, main, 100)
    return draw


def p_pulse(fx, s, a):
    main, dark, light, pos, d, ang, r = pinfo(a)
    _trail(s, a, main, 0.9, 100)
    glow(s, pos, r * 3.6, main, 150)
    circle(s, pos, int(r * 1.3), dark)
    circle(s, pos, int(r * 1.0), main)
    circle(s, pos, int(r * 0.5), light)
    for j in range(3):                                            # ondes qui s'étendent depuis le projectile
        ph = (a.t * 2.2 + j / 3) % 1
        ring(s, pos, r * (1.4 + 2.2 * ph), 3, light, int(230 * (1 - ph)))


def p_blade(air):
    def draw(fx, s, a):
        main, dark, light, pos, d, ang, r = pinfo(a)
        perp = Vector2(-d.y, d.x)
        R = r * 3.2
        outer, inner = [], []
        for i in range(14):                                       # lame en croissant, pointes vers l'arrière
            u = i / 13
            th = ang + math.radians(-80 + 160 * u)
            w = 6 * math.sin(math.pi * u) + 1
            c = pos - d * R * 0.6
            outer.append((c.x + math.cos(th) * (R + w), c.y + math.sin(th) * (R + w)))
            inner.append((c.x + math.cos(th) * (R - w), c.y + math.sin(th) * (R - w)))
        col, edge = ((235, 255, 240), (150, 230, 190)) if air else (main, light)
        glow(s, pos, R * 1.1, edge, 100)
        poly(s, outer + inner[::-1], col, 235)
        lines(s, outer, light if not air else (255, 255, 255), 255, 3)
        for i in range(4):                                        # traits de vent / gouttelettes
            q = pos - d * (14 + i * 14) + perp * (i - 1.5) * 12
            if air:
                tapered(s, q, q - d * 26, 3, (255, 255, 255), 190)
            else:
                shape(s, "drop", q, 3.5, ang, light, 200)
    return draw


# ---------- IMPACTS de projectiles (fin de trajectoire) ----------------------------------------
def i_pop(name, count=10, dist=34, size=5, glow_col=None):
    def draw(fx, s, a):
        main, dark, light, _ = a.style
        k, c = a.k, a.pos()
        e = ease_out(k)
        glow(s, c, 40 + dist * e, glow_col or main, int(180 * (1 - k)))
        ring(s, c, 10 + dist * e, max(2, 5 * (1 - k)), light, int(255 * (1 - k)))
        for i in range(count):
            off, sz, rt = p_at(a, i, dist)
            F.particle(s, a.style, name, c + off * e, size * sz * (1 - 0.4 * k), rt + k * 5, int(255 * (1 - k)), a.rng)
    return draw


def i_seed_rain(fx, s, a):
    """« Déluge de graines explosives » : les graines tombent puis éclatent."""
    main, dark, light, _ = a.style
    k, c = a.k, a.pos()
    if k < 0.3:                                                   # la graine éclate d'abord au point d'impact
        glow(s, c, 50, (255, 210, 90), int(230 * (1 - k / 0.3)))
        ring(s, c, 8 + 40 * k / 0.3, 4, (255, 235, 140), int(255 * (1 - k / 0.3)))
    for i in range(10):
        off, sz, rt = p_at(a, i, 44)
        t0 = i * 0.035
        kk = (k - t0) / 0.5
        land = c + Vector2(off.x * 0.9, off.y * 0.55)
        if 0 < kk < 0.55:                                         # la graine tombe
            drop = land + Vector2(0, -90 * (1 - kk / 0.55))
            shape(s, "drop", drop, 8, 1.57, (70, 50, 25), 255)
            shape(s, "drop", drop, 6, 1.57, (206, 168, 70), 255)
        elif kk >= 0.55 and kk < 1:                               # elle explose
            e = (kk - 0.55) / 0.45
            ring(s, land, 6 + 22 * e, 3, (255, 230, 120), int(255 * (1 - e)))
            glow(s, land, 26, (255, 210, 90), int(220 * (1 - e)))
            for j in range(4):
                th = j * TAU / 4 + i
                shape(s, "leaf", land + Vector2(math.cos(th), math.sin(th)) * 16 * e, 4, th, main, int(255 * (1 - e)))


def i_petals(fx, s, a):
    main, dark, light, _ = a.style
    k, c = a.k, a.pos()
    e = ease_out(k)
    glow(s, c, 60, (255, 200, 235), int(200 * (1 - k)))
    star(s, c, 14 + 26 * e, (255, 255, 255), int(255 * (1 - k)), k * 2)
    for i in range(16):                                           # pétales qui s'envolent
        off, sz, rt = p_at(a, i, 56)
        pp = c + off * e + Vector2(0, 10 * k * k * 10)
        shape(s, "leaf", pp, 5 + 3 * sz, rt + k * 6, (255, 170, 215) if i % 2 else (255, 255, 255), int(255 * (1 - k)))


def i_firestar(fx, s, a):
    main, dark, light, _ = a.style
    k, c = a.k, a.pos()
    e = ease_out(k)
    glow(s, c, 80 + 40 * e, main, int(220 * (1 - k)))
    poly_star(s, c, 20 + 60 * e, 8 + 24 * e, 5, 0.3, dark, int(255 * (1 - k)))
    poly_star(s, c, 14 + 46 * e, 6 + 18 * e, 5, 0.3, main, int(255 * (1 - k)))
    poly_star(s, c, 8 + 26 * e, 4 + 10 * e, 5, 0.3, light, int(255 * (1 - k)))
    ring(s, c, 14 + 56 * e, 5, light, int(240 * (1 - k)))


def i_flare(fx, s, a):
    main, dark, light, _ = a.style
    k, c = a.k, a.pos()
    e = ease_out(k)
    glow(s, c, 120 * (0.5 + e), (255, 255, 230), int(230 * (1 - k)))
    glow(s, c, 100 * (0.5 + e), main, int(220 * (1 - k)))
    for j in range(3):
        ring(s, c, 16 + (30 + j * 18) * e, 6 - j * 1.5, light if j == 0 else main, int(255 * (1 - k)))
    rays(s, c, 10, 30 + 80 * e, 12, 0.1, light, int(240 * (1 - k)), 4)
    for i in range(12):
        off, sz, rt = p_at(a, i, 80)
        shape(s, "flame", c + off * e, 6 + 4 * sz, rt, main, int(255 * (1 - k)))


def i_notes(fx, s, a):
    main, dark, light, _ = a.style
    k, c = a.k, a.pos()
    e = ease_out(k)
    glow(s, c, 50 + 30 * e, main, int(190 * (1 - k)))
    for i in range(7):
        off, sz, rt = p_at(a, i, 52)
        note(s, c + off * e + Vector2(0, -12 * e), 5 + 2 * sz, main if i % 2 else light, int(255 * (1 - k)), dark)
    for i in range(6):
        off, sz, rt = p_at(a, i + 8, 40)
        shape(s, "flame", c + off * e, 5 + 3 * sz, rt, main, int(255 * (1 - k)))


def i_splash(fx, s, a):
    main, dark, light, _ = a.style
    k, c = a.k, a.pos()
    e = ease_out(k)
    ring(s, c, 8 + 30 * e, max(2, 6 * (1 - k)), light, int(255 * (1 - k)))
    circle(s, c, int(12 + 14 * e), main, int(150 * (1 - k)))
    for i in range(12):
        off, sz, rt = p_at(a, i, 44)
        pp = c + Vector2(off.x, -abs(off.y)) * e + Vector2(0, 26 * e * e)
        shape(s, "drop", pp, 4 + 3 * sz, 1.57, light if i % 2 else main, int(255 * (1 - k)))


def i_dark(fx, s, a):
    main, dark, light, _ = a.style
    k, c = a.k, a.pos()
    e = ease_out(k)
    glow(s, c, 70 + 30 * e, dark, int(240 * (1 - k)))
    circle(s, c, int(10 + 26 * e), dark, int(230 * (1 - k)))
    ring(s, c, 10 + 44 * e, 4, light, int(255 * (1 - k)))
    for i in range(10):
        off, sz, rt = p_at(a, i, 56)
        shape(s, "shard", c + off * e, 5 + 3 * sz, rt, light if i % 2 else main, int(255 * (1 - k)))


# ---------- table : identifiant de capacité -> motif ----------------------------------------------
MOTIFS = {
    # mêlée
    "scratch": Motif(m_scratch, 0.42),
    "tackle": Motif(m_impact(0.0), 0.36),
    "pound": Motif(m_pound, 0.42),
    "mega-kick": Motif(m_impact(1.0), 0.5),
    "quick-attack": Motif(m_streak(False), 0.34),
    "aqua-jet": Motif(m_streak(True), 0.4),
    "lick": Motif(m_lick, 0.5),
    "low-sweep": Motif(m_sweep, 0.42),
    "double-hit": Motif(m_double, 0.62),
    "bite": Motif(m_bite, 0.55),
    "u-turn": Motif(m_uturn, 0.6),
    "slash": Motif(m_slash(False), 0.42),
    "night-slash": Motif(m_slash(True), 0.46),
    "knock-off": Motif(m_chop, 0.48),
    "play-rough": Motif(m_hug, 0.66),
    "wing-attack": Motif(m_wings, 0.5),
    "acrobatics": Motif(m_flurry(False), 0.55),
    "close-combat": Motif(m_flurry(True), 0.65),
    "liquidation": Motif(m_slam_water, 0.55),
    "wave-crash": Motif(m_wave_crash, 0.7),
    "aqua-step": Motif(m_water_dance, 0.7),
    # zones
    "round": Motif(z_notes, 0.7),
    "snarl": Motif(z_howl, 0.65),
    "hyper-voice": Motif(z_echo, 0.75),
    "incinerate": Motif(z_scorch, 0.85),
    # projectiles
    "leafage": Motif(p_leaves(3), impact=i_pop("leaf", 7, 30, 5)),
    "magical-leaf": Motif(p_leaves(5, rainbow=True), impact=i_pop("leaf", 12, 40, 5)),
    "leaf-storm": Motif(p_leaves(12, big=True), impact=i_pop("leaf", 18, 70, 7), impact_dur=0.5),
    "seed-bomb": Motif(p_seed, impact=i_seed_rain, impact_dur=0.8),
    "energy-ball": Motif(p_orb(True), impact=i_pop("star", 10, 44, 5)),
    "shadow-ball": Motif(p_orb(False, (230, 210, 255)), impact=i_dark, impact_dur=0.45),
    "hex": Motif(p_ghostfire, impact=i_pop("flame", 10, 40, 6)),
    "flower-trick": Motif(p_flower, impact=i_petals, impact_dur=0.6),
    "ember": Motif(p_fire(ember=True), impact=i_pop("flame", 8, 28, 5)),
    "flamethrower": Motif(p_fire(torrent=True), impact=i_pop("flame", 10, 40, 6)),
    "fire-blast": Motif(p_firestar, impact=i_firestar, impact_dur=0.55),
    "overheat": Motif(p_fire(big=True), impact=i_flare, impact_dur=0.6),
    "torch-song": Motif(p_notes, impact=i_notes, impact_dur=0.55),
    "water-gun": Motif(p_stream(True), impact=i_splash),
    "water-pulse": Motif(p_pulse, impact=i_splash),
    "aqua-cutter": Motif(p_blade(False), impact=i_splash),
    "air-slash": Motif(p_blade(True), impact=i_pop("wind", 6, 36, 14)),
}
