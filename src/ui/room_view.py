import pygame

from .. import settings as S
from ..levels import RewardKind, RoomManager

ICON = {  # couleur + lettre : placeholders d'icônes (assets/ plus tard)
    RewardKind.CAPSULE: ((80, 140, 255), "CT"),
    RewardKind.OBJET: ((250, 200, 60), "OB"),
    RewardKind.SOIN: ((90, 200, 110), "+"),
}


class RoomView:
    def __init__(self):
        self.font = pygame.font.SysFont("monospace", 15, bold=True)
        self.big = pygame.font.SysFont("monospace", 26, bold=True)

    def draw(self, surface, room: RoomManager) -> None:
        a = room.arena
        pygame.draw.rect(surface, S.FLOOR, a)
        pygame.draw.rect(surface, S.WALL, a, 6)
        if room.exits_locked:  # grille fermée au milieu du mur du haut
            for cx in (a.centerx - 160, a.centerx + 160):
                r = pygame.Rect(cx - S.DOOR_W // 2, a.top - 3, S.DOOR_W, 6)
                pygame.draw.rect(surface, (150, 50, 50), r)
        for d in room.doors:
            color, letter = ICON[d.reward]
            pygame.draw.rect(surface, (15, 15, 20), d.rect.inflate(8, 8))
            pygame.draw.rect(surface, color, d.rect, border_radius=8)
            t = self.big.render(letter, True, (20, 20, 20))
            surface.blit(t, t.get_rect(center=d.rect.center))
            lab = self.font.render(d.reward.value, True, S.WHITE)
            surface.blit(lab, lab.get_rect(midtop=(d.rect.centerx, d.rect.bottom + 28)))

    def draw_overlay(self, surface, text, sub="") -> None:
        t = self.big.render(text, True, S.WHITE)
        surface.blit(t, t.get_rect(center=(S.SCREEN_W // 2, S.SCREEN_H // 2 - 20)))
        if sub:
            s = self.font.render(sub, True, S.GREY)
            surface.blit(s, s.get_rect(center=(S.SCREEN_W // 2, S.SCREEN_H // 2 + 14)))
