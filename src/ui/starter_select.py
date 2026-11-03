"""Écran de choix du starter : liste à gauche (ligne jaune + curseur), détail à droite
(sprite animé, types, stats, capacités avec leur icône de type)."""
import pygame

from .. import settings as S
from ..starters import STARTERS
from . import theme as T
from .reward_menu import wrap

LIST_X, LIST_Y, ROW_W, ROW_H, ROW_GAP = 70, 116, 400, 104, 14
DETAIL = pygame.Rect(520, 80, 466, 570)
STAT_ROWS = (("PV", "max_hp", 140, "{:.0f}"), ("Attaque", "atk", 1.2, "{:.0f}%"),
             ("Atq. Spé.", "spa", 1.2, "{:.0f}%"), ("Vitesse", "speed_mult", 1.15, "{:.0f}%"))
SLOT_KEYS = (("basic", "Clic G"), ("special", "E"), ("cast", "R"))
KIND_LABEL = {"melee": "Mêlée", "burst": "Zone", "projectile": "Projectile"}


class StarterSelect:
    """handle_event() renvoie le `Starter` choisi (ou None)."""

    def __init__(self, starters=STARTERS):
        self.starters = list(starters)
        self.index = 0
        self.rects = [pygame.Rect(LIST_X, LIST_Y + i * (ROW_H + ROW_GAP), ROW_W, ROW_H)
                      for i in range(len(self.starters))]

    def handle_event(self, e):
        n = len(self.starters)
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_UP, pygame.K_z, pygame.K_w, pygame.K_LEFT, pygame.K_q, pygame.K_a):
                self.index = (self.index - 1) % n
            elif e.key in (pygame.K_DOWN, pygame.K_s, pygame.K_RIGHT, pygame.K_d):
                self.index = (self.index + 1) % n
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                return self.starters[self.index]
            elif pygame.K_1 <= e.key <= pygame.K_9 and e.key - pygame.K_1 < n:
                return self.starters[e.key - pygame.K_1]
        elif e.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.rects):
                if r.collidepoint(e.pos):
                    self.index = i
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.rects):
                if r.collidepoint(e.pos):
                    return self.starters[i]
        return None

    # --- rendu ---------------------------------------------------------------
    def draw(self, surface, sprites=None) -> None:
        T.pattern_fill(surface, (0, 0, S.SCREEN_W, S.SCREEN_H), T.NAVY_DARK, (40, 52, 98), 70)
        T.header(surface, "CHOISIS TON POKÉMON", T.VIOLET, T.VIOLET_PAT, "★", sub="Starter")
        for i, (st, r) in enumerate(zip(self.starters, self.rects)):
            self._draw_row(surface, st, r, i == self.index, sprites)
        self._draw_detail(surface, self.starters[self.index], sprites)
        T.footer(surface, [("↑↓", "Choisir"), ("Entrée", "Confirmer"), ("1-3", "Sélection rapide")],
                 T.VIOLET, T.VIOLET_PAT)

    def _draw_row(self, surface, st, r, selected, sprites) -> None:
        fg = T.list_row(surface, r, selected)
        if sprites:
            sprites.draw_icon(surface, st.dex, (r.x + 62, r.centery + 2), "Idle", 0, 3)
        T.text(surface, st.name, 30, fg, topleft=(r.x + 124, r.y + 16))
        x = r.x + 124
        for t in st.types:
            x = T.type_pill(surface, t, 28, topleft=(x, r.y + 60)).right + 8
        if selected:
            T.cursor(surface, r.x - 46, r.centery)

    def _draw_detail(self, surface, st, sprites) -> None:
        d = DETAIL
        T.alpha_rect(surface, d, T.NAVY, 185, 16)
        # portrait animé
        if sprites:
            sprites.draw_icon(surface, st.dex, (d.centerx, d.y + 112), "Idle", 0, 5)
        # nom, types, description
        y = d.y + 206
        T.detail_title(surface, st.name, d.x + 22, y, 26)
        x = d.right - 22
        for t in reversed(st.types):
            x = T.type_pill(surface, t, 28, topright=(x, y + 2)).left - 8
        ty = y + 44
        for line in wrap(T.font(16, False), st.description, d.w - 44):
            T.text(surface, line, 16, T.WHITE, False, topleft=(d.x + 22, ty))
            ty += 22
        # stats
        sy = d.y + 300
        for label, attr, top, fmt in STAT_ROWS:
            v = getattr(st, attr)
            T.text(surface, label, 17, T.LABEL, topleft=(d.x + 22, sy))
            T.thin_bar(surface, (d.x + 140, sy + 6, 230, 10), v / top, T.LIME)
            shown = fmt.format(v * 100 if "%" in fmt else v)
            T.text(surface, shown, 17, T.WHITE, topright=(d.right - 22, sy))
            sy += 27
        # capacités
        T.text(surface, "Capacités", 17, T.LABEL, topleft=(d.x + 22, d.y + 416))
        my = d.y + 440
        for slot, key in SLOT_KEYS:
            m = st.moves[slot]
            rr = pygame.Rect(d.x + 16, my, d.w - 32, 38)
            T.alpha_rect(surface, rr, T.NAVY_ROW, 200, 9)
            T.draw_type_icon(surface, m.element, (rr.x + 22, rr.centery), 30)
            T.text(surface, m.name, 18, T.WHITE, midleft=(rr.x + 48, rr.centery))
            T.text(surface, f"[{key}] {KIND_LABEL[m.kind]} · {m.category.value} · {m.power:.0f}",
                   13, T.GREY, False, midright=(rr.right - 12, rr.centery))
            my += 42
