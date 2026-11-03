"""Menu de récompense : liste à gauche (ligne jaune + curseur), détail à droite,
bandeaux violets haut/bas. Même grammaire que l'écran « Options » d'Écarlate/Violet."""
import pygame

from .. import settings as S
from . import theme as T

LIST_X, LIST_W, ROW_H, ROW_GAP, LIST_Y = 70, 560, 66, 10, 132
DETAIL = pygame.Rect(664, 112, 322, 360)
KIND_GLYPH = {"OBJET": "OB", "CAPSULE": "CT", "SOIN": "+"}


def wrap(font, msg, width):
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
    """handle_event() renvoie le Modifier choisi (ou None)."""

    def __init__(self, choices):
        self.choices = choices
        self.index = 0
        self.rects = [pygame.Rect(LIST_X, LIST_Y + i * (ROW_H + ROW_GAP), LIST_W, ROW_H)
                      for i in range(len(choices))]

    def handle_event(self, e):
        n = len(self.choices)
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_z, pygame.K_w, pygame.K_LEFT, pygame.K_q, pygame.K_a):
                self.index = (self.index - 1) % n
            elif e.key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
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
        surface.blit(T.blurred_backdrop(surface), (0, 0))
        kind = self.choices[0].kind
        T.header(surface, "RÉCOMPENSE", T.VIOLET, T.VIOLET_PAT, "!", sub=kind.value)

        bottom = self.rects[-1].bottom
        T.divider(surface, LIST_X - 14, LIST_X + LIST_W + 14, LIST_Y - 16)
        T.divider(surface, LIST_X - 14, LIST_X + LIST_W + 14, bottom + 16)
        for i, (mod, r) in enumerate(zip(self.choices, self.rects)):
            self._draw_row(surface, mod, r, i == self.index)
        self._draw_detail(surface, self.choices[self.index])

        T.footer(surface, [("↑↓", "Choisir"), ("Entrée", "Valider"), ("1-3", "Sélection rapide")],
                 T.VIOLET, T.VIOLET_PAT)

    def _draw_row(self, surface, mod, r, selected) -> None:
        fg = T.list_row(surface, r, selected)
        accent = T.KIND_COLORS[mod.kind.name]
        icon = pygame.Rect(r.x + 12, r.centery - 22, 44, 44)
        pygame.draw.rect(surface, accent, icon, border_radius=10)
        pygame.draw.rect(surface, T.WHITE, icon, 2, border_radius=10)
        T.text(surface, KIND_GLYPH[mod.kind.name], 18, T.WHITE, center=icon.center)
        T.text(surface, mod.name, 26, fg, midleft=(icon.right + 16, r.centery))
        if mod.badge_type is not None:
            T.type_pill(surface, mod.badge_type, 28, midright=(r.right - 14, r.centery))
        if selected:
            T.cursor(surface, r.x - 44, r.centery)

    def _draw_detail(self, surface, mod) -> None:
        d = DETAIL
        T.alpha_rect(surface, d, T.NAVY, 170, 14)
        T.detail_title(surface, mod.name, d.x + 18, d.y + 18, 22)
        y = d.y + 66
        for line in wrap(T.font(18, False), mod.description, d.w - 36):
            T.text(surface, line, 18, T.WHITE, False, topleft=(d.x + 18, y))
            y += 26
        y = max(y + 14, d.y + 190)
        T.text(surface, "Catégorie", 17, T.LABEL, topleft=(d.x + 18, y))
        T.text(surface, mod.kind.value, 17, T.WHITE, topleft=(d.x + 130, y))
        if mod.badge_type is not None:
            T.text(surface, "Type", 17, T.LABEL, topleft=(d.x + 18, y + 42))
            T.type_pill(surface, mod.badge_type, 26, topleft=(d.x + 130, y + 38))
