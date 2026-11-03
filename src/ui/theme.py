"""Thème visuel des interfaces, calqué sur la DA de Pokémon Écarlate / Violet :

- panneaux bleu nuit translucides posés sur un décor flouté ;
- ligne sélectionnée = bandeau jaune plein + curseur triangulaire vert/cyan ;
- bandeaux haut/bas violets (Violet) ou orange (Écarlate), motif discret + liseré doré ;
- jauge de PV verte avec le chiffre à l'intérieur, pastilles « Lv. », pastilles de type ;
- étiquettes jaunes + valeurs blanches, titre précédé d'une barre jaune ;
- coins dorés façon écran de combat, indications de touches en bas à droite.

Uniquement des helpers de dessin : aucune logique de jeu.
"""
import pygame

# --- Palette -----------------------------------------------------------------
NAVY = (22, 30, 54)
NAVY_DARK = (12, 18, 36)
NAVY_ROW = (36, 48, 84)
YELLOW = (244, 196, 22)
YELLOW_TXT = (38, 32, 16)
LABEL = (250, 190, 40)
WHITE = (255, 255, 255)
GREY = (160, 168, 190)
VIOLET, VIOLET_PAT = (112, 44, 172), (138, 74, 198)      # Violet
ORANGE, ORANGE_PAT = (236, 124, 34), (250, 156, 74)      # Écarlate
GOLD = (250, 198, 30)
LIME, CYAN = (176, 228, 64), (64, 200, 224)
GREEN, AMBER, RED = (62, 206, 62), (246, 150, 30), (232, 60, 52)

KIND_COLORS = {          # par RewardKind.name
    "OBJET": (244, 146, 52),
    "CAPSULE": (130, 86, 214),
    "SOIN": (60, 184, 112),
}
TYPE_COLORS = {          # par PType.name
    "NORMAL": (168, 168, 120), "FEU": (240, 128, 48), "EAU": (104, 144, 240),
    "ELECTRIK": (248, 208, 48), "PLANTE": (120, 200, 80), "GLACE": (110, 204, 214),
    "COMBAT": (192, 48, 40), "POISON": (160, 64, 160), "SOL": (224, 192, 104),
    "VOL": (168, 144, 240), "PSY": (248, 88, 136), "INSECTE": (168, 184, 32),
    "ROCHE": (184, 160, 56), "SPECTRE": (112, 88, 152), "DRAGON": (112, 56, 248),
    "TENEBRES": (104, 84, 72), "ACIER": (150, 164, 196), "FEE": (238, 120, 168),
}

# --- Polices -------------------------------------------------------------------
_FONT_NAMES = "nunito,varelaround,quicksand,inter,liberationsans,dejavusans"
_fonts: dict = {}


def font(size: int, bold: bool = True) -> pygame.font.Font:
    key = (size, bold)
    if key not in _fonts:
        _fonts[key] = pygame.font.SysFont(_FONT_NAMES, size, bold=bold)
    return _fonts[key]


# --- Texte & formes de base ----------------------------------------------------
def text(surface, msg, size=18, color=WHITE, bold=True, shadow=False, **anchor) -> pygame.Rect:
    """`anchor` = argument de Rect (center=, topleft=, midright=...)."""
    f = font(size, bold)
    img = f.render(msg, True, color)
    r = img.get_rect(**anchor)
    if shadow:
        surface.blit(f.render(msg, True, (8, 10, 22)), r.move(1, 2))
    surface.blit(img, r)
    return r


def alpha_rect(surface, rect, color=NAVY, alpha=185, radius=12) -> pygame.Rect:
    rect = pygame.Rect(rect)
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(s, (*color, alpha), s.get_rect(), border_radius=radius)
    surface.blit(s, rect.topleft)
    return rect


def pill(surface, msg, size, bg, fg=WHITE, pad=(14, 5), alpha=255, **anchor) -> pygame.Rect:
    img = font(size).render(msg, True, fg)
    r = pygame.Rect(0, 0, img.get_width() + pad[0] * 2, img.get_height() + pad[1] * 2)
    for k, v in anchor.items():
        setattr(r, k, v)
    if alpha < 255:
        alpha_rect(surface, r, bg, alpha, r.h // 2)
    else:
        pygame.draw.rect(surface, bg, r, border_radius=r.h // 2)
    surface.blit(img, img.get_rect(center=r.center))
    return r


def lv_pill(surface, msg, size=14, **anchor) -> pygame.Rect:
    """Pastille sombre « Lv. 17 »."""
    return pill(surface, msg, size, NAVY_DARK, WHITE, pad=(12, 3), alpha=225, **anchor)


def divider(surface, x1, x2, y, color=(205, 210, 226)) -> None:
    pygame.draw.line(surface, color, (x1, y), (x2, y), 2)


def detail_title(surface, msg, x, y, size=22) -> pygame.Rect:
    """Barre jaune + titre blanc (volet de détail à droite des listes)."""
    pygame.draw.rect(surface, YELLOW, (x, y + 3, 6, size + 4), border_radius=2)
    return text(surface, msg, size, WHITE, topleft=(x + 16, y))


# --- Lignes de liste & curseur -------------------------------------------------
def list_row(surface, rect, selected: bool):
    """Ligne de liste : jaune plein si sélectionnée, bleu nuit translucide sinon.
    Renvoie la couleur de texte à utiliser."""
    rect = pygame.Rect(rect)
    if selected:
        pygame.draw.rect(surface, YELLOW, rect, border_radius=9)
        return YELLOW_TXT
    alpha_rect(surface, rect, NAVY_ROW, 200, 9)
    return WHITE


def cursor(surface, x: int, cy: int, h: int = 38) -> None:
    """Curseur triangulaire à liseré vert -> cyan."""
    w = int(h * 0.9)
    pts = [(x, cy - h / 2), (x + w, cy), (x, cy + h / 2)]
    gx, gy = x + w / 3, cy
    pygame.draw.polygon(surface, CYAN, [(px + 3, py + 3) for px, py in pts])
    pygame.draw.polygon(surface, LIME, pts)
    inner = [(gx + (px - gx) * 0.52, gy + (py - gy) * 0.52) for px, py in pts]
    pygame.draw.polygon(surface, NAVY_DARK, inner)


# --- Jauges ----------------------------------------------------------------------
def hp_bar(surface, rect, ratio: float, label: str | None = None) -> None:
    """Jauge de PV : verte > 50 %, orange > 20 %, rouge sinon ; chiffre à l'intérieur."""
    r = pygame.Rect(rect)
    ratio = max(0.0, min(1.0, ratio))
    pygame.draw.rect(surface, (18, 22, 34), r, border_radius=4)
    inner = r.inflate(-4, -4)
    color = GREEN if ratio > 0.5 else AMBER if ratio > 0.2 else RED
    if ratio > 0:
        pygame.draw.rect(surface, color, (inner.x, inner.y, max(4, int(inner.w * ratio)), inner.h),
                         border_radius=3)
    pygame.draw.rect(surface, (236, 246, 236), r, 2, border_radius=4)
    if label:
        text(surface, label, max(11, int(r.h * 0.62)), WHITE, shadow=True,
             midright=(r.right - 8, r.centery))


def thin_bar(surface, rect, ratio: float, color) -> None:
    r = pygame.Rect(rect)
    pygame.draw.rect(surface, (18, 22, 34), r, border_radius=r.h // 2)
    w = int(r.w * max(0.0, min(1.0, ratio)))
    if w > 0:
        pygame.draw.rect(surface, color, (r.x, r.y, max(w, r.h), r.h), border_radius=r.h // 2)


# --- Pastilles de type ------------------------------------------------------------
def type_pill(surface, ptype, h: int = 26, **anchor) -> pygame.Rect:
    col = TYPE_COLORS[ptype.name]
    label = ptype.value.upper()
    f = font(max(9, int(h * 0.5)))
    w = f.size(label)[0] + h + 14
    r = pygame.Rect(0, 0, w, h)
    for k, v in anchor.items():
        setattr(r, k, v)
    pygame.draw.rect(surface, col, r, border_radius=h // 2)
    c = (r.x + h // 2, r.centery)
    pygame.draw.circle(surface, (255, 255, 255), c, h // 2 - 3)
    text(surface, ptype.value[0].upper(), max(9, int(h * 0.5)), col, center=c)
    text(surface, label, max(9, int(h * 0.5)), WHITE, shadow=True,
         center=(r.x + h + (r.w - h) // 2 - 2, r.centery))
    return r


def type_pills(surface, types, center_x: int, top: int, h: int = 18, gap: int = 4) -> None:
    f = font(max(9, int(h * 0.5)))
    widths = [f.size(t.value.upper())[0] + h + 14 for t in types]
    x = center_x - (sum(widths) + gap * (len(types) - 1)) // 2
    for t, w in zip(types, widths):
        type_pill(surface, t, h, topleft=(x, top))
        x += w + gap


# --- Bandeaux haut / bas -----------------------------------------------------------
_pat_cache: dict = {}


def band(surface, rect, color, pat, line_at: str = "top") -> pygame.Rect:
    """Bandeau plein + motif de cercles discret + liseré doré sur le bord extérieur."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, color, rect)
    key = (rect.size, pat)
    if key not in _pat_cache:
        s = pygame.Surface(rect.size, pygame.SRCALPHA)
        for row, y in enumerate(range(10, rect.h, 30)):
            for x in range(15 if row % 2 else 0, rect.w + 30, 30):
                pygame.draw.circle(s, (*pat, 95), (x, y), 11, 3)
        _pat_cache[key] = s
    surface.blit(_pat_cache[key], rect.topleft)
    ly = rect.top if line_at == "top" else rect.bottom - 4
    pygame.draw.rect(surface, GOLD, (rect.x, ly, rect.w, 4))
    return rect


def header(surface, title: str, color, pat, glyph: str = "!", sub: str | None = None) -> None:
    w = surface.get_width()
    band(surface, (0, 0, w, 62), color, pat, "top")
    pygame.draw.circle(surface, WHITE, (46, 33), 17)
    text(surface, glyph, 22, color, center=(46, 33))
    text(surface, title, 26, WHITE, shadow=True, midleft=(80, 33))
    if sub:
        pill(surface, sub, 15, NAVY_DARK, WHITE, pad=(16, 5), alpha=200, midright=(w - 30, 33))


def _glyph_w(g: str, size: int = 18) -> int:
    return max(size + 12, font(size - 4).size(g)[0] + 18)


def _draw_glyph(surface, g: str, x: int, cy: int, size: int = 18) -> int:
    w, h = _glyph_w(g, size), size + 12
    r = pygame.Rect(x, cy - h // 2, w, h)
    pygame.draw.rect(surface, WHITE, r, border_radius=h // 2)
    text(surface, g, size - 4, NAVY, center=r.center)
    return w


def prompts_width(hints, gap: int = 26, size: int = 18) -> int:
    return (sum(_glyph_w(g, size) + 8 + font(size).size(c)[0] for g, c in hints)
            + gap * (len(hints) - 1))


def draw_prompts(surface, hints, right: int, cy: int, gap: int = 26, size: int = 18) -> None:
    x = right - prompts_width(hints, gap, size)
    for g, c in hints:
        x += _draw_glyph(surface, g, x, cy, size) + 8
        x = text(surface, c, size, WHITE, shadow=True, midleft=(x, cy)).right + gap


def footer(surface, hints, color, pat) -> None:
    w, h = surface.get_size()
    band(surface, (0, h - 56, w, 56), color, pat, "bottom")
    draw_prompts(surface, hints, w - 36, h - 28)


def prompt_bar(surface, hints, right: int, bottom: int, size: int = 15) -> pygame.Rect:
    """Petite barre flottante d'indications de touches (translucide)."""
    tw = prompts_width(hints, 18, size)
    r = pygame.Rect(right - tw - 32, bottom - 38, tw + 32, 38)
    alpha_rect(surface, r, NAVY, 190, 19)
    draw_prompts(surface, hints, r.right - 16, r.centery, 18, size)
    return r


def corner_brackets(surface, margin: int = 12, size: int = 54, th: int = 5) -> None:
    """Coins dorés (haut gauche / bas droite) de l'écran de combat."""
    w, h = surface.get_size()
    m = margin
    pygame.draw.rect(surface, GOLD, (m, m, size, th))
    pygame.draw.rect(surface, GOLD, (m, m, th, size))
    pygame.draw.rect(surface, GOLD, (w - m - size, h - m - th, size, th))
    pygame.draw.rect(surface, GOLD, (w - m - th, h - m - size, th, size))


def blurred_backdrop(surface, tint=(14, 20, 44), alpha: int = 120, k: int = 6) -> pygame.Surface:
    """Copie floutée + teintée de l'écran : le décor derrière les menus."""
    w, h = surface.get_size()
    small = pygame.transform.smoothscale(surface, (max(1, w // k), max(1, h // k)))
    big = pygame.transform.smoothscale(small, (w, h))
    veil = pygame.Surface((w, h), pygame.SRCALPHA)
    veil.fill((*tint, alpha))
    big.blit(veil, (0, 0))
    return big
