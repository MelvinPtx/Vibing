"""Thème visuel des menus, inspiré de la DA de Pokémon Écarlate / Violet :
panneaux blancs très arrondis, accents écarlate et violet, boutons en « pilules »,
fond à rayures diagonales, jauges de PV vert / jaune / rouge, pastilles de type.
Aucune logique de jeu ici : uniquement des helpers de dessin.
"""
import pygame

# --- Palette -----------------------------------------------------------------
SCARLET = (226, 59, 46)
SCARLET_DARK = (168, 36, 30)
VIOLET = (125, 74, 201)
VIOLET_DARK = (84, 46, 150)
PANEL = (250, 249, 245)
PANEL_DIM = (232, 229, 238)
INK = (38, 38, 52)
INK_SOFT = (114, 112, 130)
GOLD = (247, 190, 46)
HP_GREEN, HP_YELLOW, HP_RED = (74, 200, 108), (246, 200, 60), (232, 70, 60)
BAR_BG = (60, 58, 76)

KIND_COLORS = {          # par RewardKind.name
    "OBJET": (244, 146, 52),
    "CAPSULE": VIOLET,
    "SOIN": (60, 180, 110),
}

TYPE_COLORS = {          # par PType.name
    "NORMAL": (168, 168, 120), "FEU": (240, 128, 48), "EAU": (104, 144, 240),
    "ELECTRIK": (248, 208, 48), "PLANTE": (120, 200, 80), "GLACE": (152, 216, 216),
    "COMBAT": (192, 48, 40), "POISON": (160, 64, 160), "SOL": (224, 192, 104),
    "VOL": (168, 144, 240), "PSY": (248, 88, 136), "INSECTE": (168, 184, 32),
    "ROCHE": (184, 160, 56), "SPECTRE": (112, 88, 152), "DRAGON": (112, 56, 248),
    "TENEBRES": (112, 88, 72), "ACIER": (184, 184, 208), "FEE": (238, 153, 172),
}

# --- Polices (première trouvée ; DejaVu en dernier recours) ----------------------
_FONT_NAMES = "nunito,varelaround,quicksand,inter,liberationsans,dejavusans"
_fonts: dict = {}


def font(size: int, bold: bool = False) -> pygame.font.Font:
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont(_FONT_NAMES, size, bold=bold)
    return _fonts[key]


# --- Primitives ----------------------------------------------------------------
def _shadow(surface, rect, radius, offset=(0, 6), alpha=70):
    r = rect.move(*offset)
    s = pygame.Surface(r.size, pygame.SRCALPHA)
    pygame.draw.rect(s, (0, 0, 0, alpha), s.get_rect(), border_radius=radius)
    surface.blit(s, r.topleft)


def panel(surface, rect, color=PANEL, radius=18, border=None, border_w=3, shadow=True, alpha=255):
    rect = pygame.Rect(rect)
    if shadow:
        _shadow(surface, rect, radius)
    if alpha < 255:
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(s, (*color, alpha), s.get_rect(), border_radius=radius)
        surface.blit(s, rect.topleft)
    else:
        pygame.draw.rect(surface, color, rect, border_radius=radius)
    if border:
        pygame.draw.rect(surface, border, rect, border_w, border_radius=radius)
    return rect


def text(surface, msg, size, color=INK, bold=False, **anchor) -> pygame.Rect:
    """Dessine `msg` ; `anchor` = argument de get_rect (center=, topleft=, midtop=...)."""
    img = font(size, bold).render(msg, True, color)
    r = img.get_rect(**anchor)
    surface.blit(img, r)
    return r


def pill(surface, msg, size, bg, fg=PANEL, pad=(14, 6), bold=True, **anchor) -> pygame.Rect:
    img = font(size, bold).render(msg, True, fg)
    r = pygame.Rect(0, 0, img.get_width() + pad[0] * 2, img.get_height() + pad[1] * 2)
    for k, v in anchor.items():
        setattr(r, k, v)
    pygame.draw.rect(surface, bg, r, border_radius=r.h // 2)
    surface.blit(img, img.get_rect(center=r.center))
    return r


def hp_bar(surface, rect, ratio: float) -> None:
    """Jauge de PV façon Pokémon : verte > 50 %, jaune > 20 %, rouge sinon."""
    rect = pygame.Rect(rect)
    ratio = max(0.0, min(1.0, ratio))
    color = HP_GREEN if ratio > 0.5 else HP_YELLOW if ratio > 0.2 else HP_RED
    pygame.draw.rect(surface, BAR_BG, rect, border_radius=rect.h // 2)
    if ratio > 0:
        fill = pygame.Rect(rect.x, rect.y, max(rect.h, int(rect.w * ratio)), rect.h)
        pygame.draw.rect(surface, color, fill, border_radius=rect.h // 2)
    pygame.draw.rect(surface, PANEL, rect, 2, border_radius=rect.h // 2)


def thin_bar(surface, rect, ratio: float, color) -> None:
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, BAR_BG, rect, border_radius=rect.h // 2)
    w = int(rect.w * max(0.0, min(1.0, ratio)))
    if w > 0:
        pygame.draw.rect(surface, color, (rect.x, rect.y, max(w, rect.h), rect.h), border_radius=rect.h // 2)


def type_badge(surface, ptype, **anchor) -> pygame.Rect:
    """Pastille colorée du nom du type (ex. FEU)."""
    return pill(surface, ptype.value.upper(), 13, TYPE_COLORS[ptype.name], (255, 255, 255),
                pad=(12, 4), **anchor)


_stripes_cache: dict = {}


def stripes(surface, rect, color=(255, 255, 255), alpha=14, spacing=26, width=8) -> None:
    """Rayures diagonales du fond des menus Écarlate / Violet."""
    rect = pygame.Rect(rect)
    key = (rect.size, color, alpha, spacing, width)
    if key not in _stripes_cache:
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        for x in range(-rect.h, rect.w, spacing):
            pygame.draw.line(s, (*color, alpha), (x, rect.h), (x + rect.h, 0), width)
        _stripes_cache[key] = s
    surface.blit(_stripes_cache[key], rect.topleft)


def menu_backdrop(surface, w: int, h: int) -> None:
    """Voile violet profond + rayures, derrière un menu."""
    veil = pygame.Surface((w, h), pygame.SRCALPHA)
    veil.fill((30, 20, 58, 205))
    surface.blit(veil, (0, 0))
    stripes(surface, (0, 0, w, h))


def key_hint(surface, label: str, caption: str, x: int, cy: int) -> int:
    """Petite touche arrondie + légende. Renvoie le x de fin."""
    k = pill(surface, label, 14, PANEL, INK, pad=(10, 3), midleft=(x, cy))
    c = text(surface, caption, 15, PANEL, midleft=(k.right + 8, cy))
    return c.right + 22
