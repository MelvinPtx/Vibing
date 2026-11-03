import pygame

from .. import settings as S
from ..levels import RewardKind, RoomManager
from . import theme as T

ICON = {  # lettre affichée sur la porte (assets/ plus tard)
    RewardKind.CAPSULE: "CT",
    RewardKind.OBJET: "OB",
    RewardKind.SOIN: "+",
}


class RoomView:
    def draw(self, surface, room: RoomManager) -> None:
        a = room.arena
        pygame.draw.rect(surface, S.FLOOR, a)
        pygame.draw.rect(surface, S.WALL, a, 6)
        if room.exits_locked:  # grilles fermées dans le mur du haut
            for cx in (a.centerx - 160, a.centerx + 160):
                r = pygame.Rect(cx - S.DOOR_W // 2, a.top - 4, S.DOOR_W, 8)
                pygame.draw.rect(surface, T.SCARLET_DARK, r, border_radius=4)
        for d in room.doors:
            accent = T.KIND_COLORS[d.reward.name]
            T.panel(surface, d.rect.inflate(10, 10), T.PANEL, radius=16)
            pygame.draw.rect(surface, accent, d.rect, border_radius=12)
            T.text(surface, ICON[d.reward], 24, T.PANEL, True, center=d.rect.center)
            T.pill(surface, d.reward.value, 14, T.PANEL, T.INK, pad=(12, 4),
                   midtop=(d.rect.centerx, d.rect.bottom + 22))

    def draw_overlay(self, surface, msg, sub="") -> None:
        T.menu_backdrop(surface, S.SCREEN_W, S.SCREEN_H)
        r = pygame.Rect(0, 0, 460, 150)
        r.center = (S.SCREEN_W // 2, S.SCREEN_H // 2)
        T.panel(surface, r, T.PANEL, radius=26)
        band = pygame.Rect(r.x + 10, r.y + 10, r.w - 20, 62)
        pygame.draw.rect(surface, T.SCARLET, band, border_radius=18)
        T.text(surface, msg, 34, T.PANEL, True, center=band.center)
        if sub:
            T.pill(surface, sub, 16, T.INK, T.PANEL, pad=(16, 6), center=(r.centerx, r.bottom - 40))
