import math

import pygame
from pygame import Vector2

from .. import settings as S
from ..levels import RewardKind, RoomManager
from . import theme as T

ICON = {RewardKind.CAPSULE: "CT", RewardKind.OBJET: "OB", RewardKind.SOIN: "+"}


class RoomView:
    def draw(self, surface, room: RoomManager) -> None:
        a = room.arena
        pygame.draw.rect(surface, S.FLOOR, a)
        pygame.draw.rect(surface, S.WALL, a, 6)
        self.draw_obstacles(surface, room.obstacles)
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

    def draw_obstacles(self, surface, obstacles) -> None:
        """Rochers : ombre portée, dalle avec liseré et reflet, quelques fissures."""
        for r in obstacles:
            T.alpha_rect(surface, r.move(5, 9), (0, 0, 0), 80, 12)
            pygame.draw.rect(surface, (92, 98, 124), r, border_radius=12)
            pygame.draw.rect(surface, (56, 60, 82), r, 4, border_radius=12)
            pygame.draw.line(surface, (128, 136, 166), (r.x + 12, r.y + 7), (r.right - 12, r.y + 7), 3)
            k = (r.x * 7 + r.y * 13) % 5                     # fissures déterministes
            cx, cy = r.x + r.w * (0.3 + 0.1 * k), r.y + r.h * 0.45
            pygame.draw.lines(surface, (62, 66, 90), False,
                              [(cx, cy), (cx + 10, cy + 12), (cx + 2, cy + 22), (cx + 12, cy + 34)], 2)

    def draw_telegraphs(self, surface, telegraphs) -> None:
        """Zones de danger annoncées par un boss : rouge translucide qui se remplit jusqu'au coup."""
        if not telegraphs:
            return
        layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        for t in telegraphs:
            k = t.progress
            if t.kind == "circle":
                pygame.draw.circle(layer, (230, 60, 50, 55), t.pos, t.radius)
                pygame.draw.circle(layer, (240, 80, 60, 110), t.pos, max(2, t.radius * k))
                pygame.draw.circle(layer, (255, 110, 90, 230), t.pos, t.radius, 3)
            else:
                d = Vector2(t.direction)
                perp = Vector2(-d.y, d.x) * t.radius
                a, b = t.pos + perp, t.pos - perp
                pts = [a, b, b + d * t.length, a + d * t.length]
                pygame.draw.polygon(layer, (230, 60, 50, 55), pts)
                fill = [a, b, b + d * t.length * k, a + d * t.length * k]
                pygame.draw.polygon(layer, (240, 80, 60, 110), fill)
                pygame.draw.polygon(layer, (255, 110, 90, 230), pts, 3)
        surface.blit(layer, (0, 0))

    def draw_banner(self, surface, msg: str, sub: str = "", alpha: int = 255) -> None:
        """Bandeau d'annonce (arrivée d'un boss)."""
        w = surface.get_width()
        box = pygame.Rect(0, 0, 560, 96)
        box.center = (w // 2, 200)
        layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
        T.alpha_rect(layer, box, T.NAVY, 225, 18)
        pygame.draw.rect(layer, T.RED, (box.x + 10, box.y + 10, box.w - 20, 46), border_radius=14)
        T.text(layer, msg, 30, T.WHITE, shadow=True, center=(box.centerx, box.y + 33))
        if sub:
            T.text(layer, sub, 17, T.GREY, False, center=(box.centerx, box.y + 76))
        layer.set_alpha(alpha)
        surface.blit(layer, (0, 0))

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
