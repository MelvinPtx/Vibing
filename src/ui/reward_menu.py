import pygame

from .. import settings as S
from . import theme as T

CARD_W, CARD_H, GAP = 258, 300, 28
KIND_ICON = {"OBJET": "OB", "CAPSULE": "CT", "SOIN": "+"}


def _wrap(font, msg, width):
    lines, line = [], ""
    for word in msg.split():
        test = f"{line} {word}".strip()
        if font.size(test)[0] > width and line:
            lines.append(line)
            line = word
        else:
            line = test
    return lines + [line]


class RewardMenu:
    """Choix d'une récompense parmi N cartes. handle_event() renvoie le Modifier choisi."""

    def __init__(self, choices):
        self.choices = choices
        self.index = 0
        total = len(choices) * CARD_W + (len(choices) - 1) * GAP
        x0 = (S.SCREEN_W - total) // 2
        self.rects = [pygame.Rect(x0 + i * (CARD_W + GAP), 225, CARD_W, CARD_H)
                      for i in range(len(choices))]

    def handle_event(self, e):
        n = len(self.choices)
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT, pygame.K_q, pygame.K_a):
                self.index = (self.index - 1) % n
            elif e.key in (pygame.K_RIGHT, pygame.K_d):
                self.index = (self.index + 1) % n
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return self.choices[self.index]
            elif pygame.K_1 <= e.key <= pygame.K_9 or pygame.K_KP1 <= e.key <= pygame.K_KP9:
                i = e.key - (pygame.K_1 if e.key <= pygame.K_9 else pygame.K_KP1)
                if i < n:
                    return self.choices[i]
        elif e.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.rects):
                if r.collidepoint(e.pos):
                    self.index = i
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.rects):
                if r.collidepoint(e.pos):
                    return self.choices[i]
        return None

    # --- rendu ---------------------------------------------------------------
    def draw(self, surface) -> None:
        T.menu_backdrop(surface, S.SCREEN_W, S.SCREEN_H)
        self._draw_title(surface)
        for i, (mod, r) in enumerate(zip(self.choices, self.rects)):
            self._draw_card(surface, mod, r, i, selected=(i == self.index))
        self._draw_hints(surface)

    def _draw_title(self, surface) -> None:
        r = pygame.Rect(0, 0, 440, 62)
        r.center = (S.SCREEN_W // 2, 128)
        T.panel(surface, r, T.PANEL, radius=31)
        tab = pygame.Rect(r.x + 8, r.y + 8, 46, r.h - 16)   # pastille écarlate à gauche
        pygame.draw.rect(surface, T.SCARLET, tab, border_radius=(r.h - 16) // 2)
        T.text(surface, "!", 28, T.PANEL, True, center=tab.center)
        T.text(surface, "Choisis ta récompense", 26, T.INK, True,
               center=(r.centerx + 26, r.centery))

    def _draw_card(self, surface, mod, rect, i, selected) -> None:
        kind = mod.kind.name
        accent = T.KIND_COLORS[kind]
        r = rect.move(0, -14 if selected else 0)          # la carte sélectionnée se soulève
        T.panel(surface, r, T.PANEL, radius=22,
                border=T.SCARLET if selected else T.PANEL_DIM, border_w=5 if selected else 3)

        # bandeau coloré avec rayures + pastille d'icône
        head = pygame.Rect(r.x + 8, r.y + 8, r.w - 16, 92)
        pygame.draw.rect(surface, accent, head, border_radius=16)
        clip = surface.get_clip()
        surface.set_clip(head)
        T.stripes(surface, head, (255, 255, 255), 28, 22, 7)
        surface.set_clip(clip)
        icon = pygame.Rect(0, 0, 60, 60)
        icon.midleft = (head.x + 16, head.centery)
        pygame.draw.circle(surface, T.PANEL, icon.center, 30)
        pygame.draw.circle(surface, T.INK, icon.center, 30, 3)
        T.text(surface, KIND_ICON[kind], 22, accent, True, center=icon.center)
        name_w = head.w - icon.w - 44
        size = 20 if all(T.font(20, True).size(w)[0] <= name_w for w in mod.name.split()) else 17
        for j, line in enumerate(_wrap(T.font(size, True), mod.name, name_w)):
            T.text(surface, line, size, T.PANEL, True,
                   topleft=(icon.right + 12, head.y + 22 + j * (size + 4)))

        # catégorie + pastille de type
        cat = T.pill(surface, mod.kind.value, 13, T.PANEL_DIM, T.INK_SOFT, pad=(10, 4),
                     topleft=(r.x + 16, head.bottom + 14))
        if mod.badge_type is not None:
            T.type_badge(surface, mod.badge_type, topleft=(cat.right + 8, cat.y))

        # description
        for j, line in enumerate(_wrap(T.font(16), mod.description, r.w - 36)):
            T.text(surface, line, 16, T.INK, topleft=(r.x + 18, cat.bottom + 14 + j * 22))

        # touche de raccourci
        T.pill(surface, str(i + 1), 15, T.SCARLET if selected else T.INK_SOFT, T.PANEL,
               pad=(11, 3), bottomright=(r.right - 14, r.bottom - 14))
        if selected:  # curseur
            pygame.draw.polygon(surface, T.SCARLET,
                                [(r.centerx - 12, r.bottom + 12), (r.centerx + 12, r.bottom + 12),
                                 (r.centerx, r.bottom + 28)])

    def _draw_hints(self, surface) -> None:
        bar = pygame.Rect(0, 0, 640, 46)
        bar.center = (S.SCREEN_W // 2, 600)
        T.panel(surface, bar, T.INK, radius=23, shadow=False, alpha=235)
        x = bar.x + 22
        x = T.key_hint(surface, "← →", "Choisir", x, bar.centery)
        x = T.key_hint(surface, "Entrée", "Valider", x, bar.centery)
        T.key_hint(surface, "1-3", "Sélection directe", x, bar.centery)
