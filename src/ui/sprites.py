"""Sprites PMD (PMDCollab/SpriteCollab) : chargement des planches, animation, rendu.

Format d'une planche `<Anim>-Anim.png` : une colonne par image, 8 lignes = 8 directions
dans l'ordre S, SE, E, NE, N, NO, O, SO. `AnimData.xml` donne la taille des images et leurs
durées (en 1/60 s) ; une animation peut être la copie d'une autre (`CopyOf`).

`SpriteRenderer` dessine n'importe quelle entité qui expose `species` (n° de Pokédex),
`pos`, `radius`, `facing` et `sprite_anim` -> (nom d'animation, vitesse). Sans sprite
disponible, `draw()` renvoie False et l'appelant dessine le cercle de secours.
"""
import math
import weakref
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import pygame

from .. import settings as S

ASSET_DIR = Path(__file__).resolve().parents[2] / "assets" / "sprites"
TICK = 1 / 60
LOOPING = frozenset({"Idle", "Walk"})
FALLBACKS = {"Swing": ("Attack",), "Shoot": ("Attack",), "Attack": ("Idle",),
             "Hurt": ("Idle",), "Walk": ("Idle",), "Faint": ("Hurt", "Idle"), "Charge": ("Attack", "Idle")}
DEATH_FLASH = 0.12   # s : flash blanc au moment de la mort
CYAN_TINT = (0, 70, 90)


def direction_index(v) -> int:
    """Vecteur écran (y vers le bas) -> ligne de la planche : 0=S, 1=SE, 2=E, 3=NE, 4=N, 5=NO, 6=O, 7=SO."""
    if v.length_squared() == 0:
        return 0
    return round((90 - math.degrees(math.atan2(v.y, v.x))) / 45) % 8


@dataclass
class Anim:
    name: str
    frames: list            # frames[direction][i] -> Surface (taille d'origine)
    durations: list         # secondes

    @property
    def total(self) -> float:
        return sum(self.durations)

    def index_at(self, t: float, loop: bool) -> int:
        last = len(self.durations) - 1
        if self.total <= 0:
            return 0
        if loop:
            t %= self.total
        elif t >= self.total:
            return last
        acc = 0.0
        for i, d in enumerate(self.durations):
            acc += d
            if t < acc:
                return i
        return last


class SpriteSet:
    """Toutes les animations d'une espèce + cache des images mises à l'échelle."""

    def __init__(self, dex: int, anims: dict):
        self.dex = dex
        self.anims = anims
        self._scaled: dict = {}

    def anim(self, name: str):
        for n in (name, *FALLBACKS.get(name, ()), "Idle"):
            if n in self.anims:
                return self.anims[n]
        return None

    def frame(self, anim: Anim, direction: int, idx: int, scale: int) -> pygame.Surface:
        key = (anim.name, direction, idx, scale)
        if key not in self._scaled:
            src = anim.frames[direction % len(anim.frames)][idx]
            self._scaled[key] = pygame.transform.scale(src, (src.get_width() * scale,
                                                             src.get_height() * scale))
        return self._scaled[key]


def _parse_anim_data(path: Path) -> dict:
    raw = {}
    for a in ET.parse(path).getroot().iter("Anim"):
        raw[a.findtext("Name")] = {
            "copy": a.findtext("CopyOf"),
            "w": int(a.findtext("FrameWidth") or 0),
            "h": int(a.findtext("FrameHeight") or 0),
            "dur": [int(d.text) for d in a.iter("Duration")],
        }
    return raw


def load_sprite_set(dex: int, root: Path = ASSET_DIR):
    """Charge une espèce ; None si ses fichiers ne sont pas dans assets/sprites/."""
    folder = Path(root) / f"{dex:04d}"
    data = folder / "AnimData.xml"
    if not data.exists():
        return None
    raw = _parse_anim_data(data)
    anims = {}
    for name in raw:
        sheet_name, spec, seen = name, raw[name], {name}
        while spec["copy"] and spec["copy"] in raw and spec["copy"] not in seen:
            sheet_name = spec["copy"]
            seen.add(sheet_name)
            spec = raw[sheet_name]
        sheet = folder / f"{sheet_name}-Anim.png"
        if not sheet.exists() or not spec["w"] or not spec["dur"]:
            continue
        img = pygame.image.load(str(sheet))
        if pygame.display.get_surface() is not None:
            img = img.convert_alpha()
        fw, fh = spec["w"], spec["h"]
        cols, rows = img.get_width() // fw, max(1, img.get_height() // fh)
        n = min(len(spec["dur"]), cols)
        frames = [[img.subsurface((i * fw, (d if rows >= 8 else 0) * fh, fw, fh)).copy()
                   for i in range(n)] for d in range(8)]
        anims[name] = Anim(name, frames, [t * TICK for t in spec["dur"][:n]])
    return SpriteSet(dex, anims) if anims else None


class SpriteRenderer:
    def __init__(self, root: Path = ASSET_DIR, scale: int = 3):
        self.root, self.scale = Path(root), scale
        self._sets: dict = {}
        self._state = weakref.WeakKeyDictionary()   # entité -> [anim, t, vitesse, nonce]
        self._tinted: dict = {}
        self._shadows: dict = {}

    def get(self, dex):
        if dex not in self._sets:
            self._sets[dex] = load_sprite_set(dex, self.root) if dex else None
        return self._sets[dex]

    def update(self, dt: float) -> None:
        for st in self._state.values():
            st[1] += dt * st[2]

    # --- helpers ---------------------------------------------------------------
    def _tint(self, frame: pygame.Surface, tint) -> pygame.Surface:
        key = (id(frame), tint)
        if key not in self._tinted:
            t = frame.copy()
            t.fill(tint, special_flags=pygame.BLEND_RGB_ADD)
            self._tinted[key] = (t, frame)       # on garde `frame` : l'id reste valide
        return self._tinted[key][0]

    def _shadow(self, surface, center, w: int, h: int) -> None:
        if (w, h) not in self._shadows:
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            pygame.draw.ellipse(s, (0, 0, 0, 90), s.get_rect())
            self._shadows[(w, h)] = s
        surface.blit(self._shadows[(w, h)], self._shadows[(w, h)].get_rect(center=center))

    # --- entités -----------------------------------------------------------------
    def draw(self, surface, entity) -> bool:
        sset = self.get(getattr(entity, "species", None))
        if sset is None or not entity.sprite_visible:
            return False
        if getattr(entity, "dying", False):
            return self._draw_dying(surface, entity, sset)
        name, speed = entity.sprite_anim
        anim = sset.anim(name)
        nonce = getattr(entity, "sprite_nonce", 0)
        st = self._state.get(entity)
        if st is None or st[0] != name or st[3] != nonce:
            st = self._state[entity] = [name, 0.0, speed, nonce]
        st[2] = speed
        idx = anim.index_at(st[1], anim.name in LOOPING)
        frame = sset.frame(anim, direction_index(entity.facing), idx, getattr(entity, "sprite_scale", self.scale))

        x, y = round(entity.pos.x), round(entity.pos.y)
        r = entity.radius
        self._shadow(surface, (x, y + int(r * 0.55)), int(r * 2.0), int(r * 0.75))
        for gpos, life in getattr(entity, "trail", ()):           # images rémanentes du dash
            ghost = self._tint(frame, CYAN_TINT)
            ghost.set_alpha(int(120 * life))
            surface.blit(ghost, ghost.get_rect(center=(round(gpos.x), round(gpos.y))))
            ghost.set_alpha(255)
        if getattr(entity, "sprite_blink", False):                 # clignote quand touché
            return True
        tint = getattr(entity, "sprite_tint", None)
        img = self._tint(frame, tint) if tint else frame
        surface.blit(img, img.get_rect(center=(x, y)))
        return True

    def _draw_dying(self, surface, entity, sset) -> bool:
        """Mort : flash blanc, puis l'animation « Faint » si l'espèce en a une (sinon la pose
        « Hurt » qui s'écrase), pendant que le sprite s'estompe."""
        t, total = entity.death_t, S.DEATH_DURATION
        faint = sset.anims.get("Faint")
        direction = direction_index(entity.facing)
        if faint:
            anim, idx = faint, faint.index_at(t * max(1.0, faint.total / 0.5), False)
        else:
            anim, idx = sset.anim("Hurt"), 0
        frame = sset.frame(anim, direction, idx, getattr(entity, "sprite_scale", self.scale))
        x, y = round(entity.pos.x), round(entity.pos.y)
        k = max(0.0, min(1.0, (t - DEATH_FLASH) / (total - DEATH_FLASH)))   # 0 -> 1 pendant le fondu
        r = entity.radius
        if k < 0.6:
            self._shadow(surface, (x, y + int(r * 0.55)), int(r * 2.0), int(r * 0.75))
        img = self._tint(frame, (210, 210, 210)) if t < DEATH_FLASH else frame
        rect = img.get_rect(center=(x, y))
        if k > 0:
            if not faint:                                   # écrasement vertical, pieds au sol
                h = max(2, int(frame.get_height() * (1 - 0.45 * k)))
                img = pygame.transform.scale(img, (frame.get_width(), h))
                rect = img.get_rect(midbottom=(x, y + frame.get_height() // 2))
            else:
                img = img.copy()
            img.set_alpha(int(255 * (1 - k)))
        surface.blit(img, rect)
        return True

    # --- icônes d'interface (HUD, menus) -------------------------------------------
    def draw_icon(self, surface, dex, center, anim: str = "Idle", direction: int = 0,
                  scale: int | None = None, shadow: bool = True) -> bool:
        sset = self.get(dex)
        if sset is None:
            return False
        a = sset.anim(anim)
        idx = a.index_at(pygame.time.get_ticks() / 1000, True)
        frame = sset.frame(a, direction, idx, scale or self.scale)
        if shadow:
            self._shadow(surface, (center[0], center[1] + frame.get_height() // 3),
                         int(frame.get_width() * 0.9), max(6, frame.get_height() // 6))
        surface.blit(frame, frame.get_rect(center=center))
        return True
