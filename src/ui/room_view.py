import pygame

from .. import settings as S
from ..levels import RewardKind, RoomManager
from . import theme as T

ICON = {RewardKind.CAPSULE: "CT", RewardKind.OBJET: "OB", RewardKind.SOIN: "+"}


class RoomView:
    def draw(self, surface, room: RoomManager) -> None:
        a = room.arena
        pygame.draw.rect(surface, S.FLOOR, a)
        pygame.draw.rect(surface, S.WALL, a, 6)
        if room.exits_locked:  # grilles fermées dans le mur du haut
            for cx in (a.centerx - 160, a.centerx + 160):
                r = pygame.Rect(cx - S.DOOR_W // 2, a.top - 4, S.DOOR_W, 8)
                pygame.draw.rect(surface, T.RED, r, border_radius=4)
        for d in room.doors:
            accent = T.KIND_COLORS[d.reward.name]
            ring = d.rect.inflate(10, 10)
            pygame.draw.rect(surface, T.NAVY_DARK, ring, border_radius=14)
            pygame.draw.rect(surface, T.GOLD, ring, 3, border_radius=14)
            pygame.draw.rect(surface, accent, d.rect, border_radius=10)
            T.text(surface, ICON[d.reward], 24, T.WHITE, shadow=True, center=d.rect.center)
            T.pill(surface, d.reward.value, 14, T.NAVY, T.WHITE, pad=(12, 4), alpha=220,
                   midtop=(d.rect.centerx, d.rect.bottom + 24))

    def draw_game_over(self, surface, player, room_number: int = 0) -> None:
        w, h = surface.get_size()
        surface.blit(T.blurred_backdrop(surface), (0, 0))
        T.header(surface, "K.O. !", T.ORANGE, T.ORANGE_PAT, "!")
        box = pygame.Rect(0, 0, 640, 130)           # boîte de dialogue
        box.center = (w // 2, h // 2)
        T.alpha_rect(surface, box, T.NAVY, 225, 16)
        pygame.draw.rect(surface, (255, 255, 255), box, 3, border_radius=16)
        T.text(surface, f"{player.name} n'a plus de PV…", 28, T.WHITE, shadow=True,
               center=(box.centerx, box.y + 46))
        if room_number:
            T.text(surface, f"Tu as atteint la salle {room_number}.", 20, T.GREY, False,
                   center=(box.centerx, box.y + 90))
        T.footer(surface, [("Entrée", "Recommencer"), ("Échap", "Quitter")], T.ORANGE, T.ORANGE_PAT)
