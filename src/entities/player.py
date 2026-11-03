"""Joueur : `Player` = données/rendu, `PlayerController` = logique de déplacement.

Le contrôleur ne lit PAS le clavier lui-même : il reçoit un `Intent`
(direction + dash demandé). Ainsi on peut le piloter depuis le clavier,
une manette, une IA ou un test automatisé.
"""
from dataclasses import dataclass, field

import pygame
from pygame import Vector2

from .. import settings as S
from .entity import Entity


@dataclass
class Intent:
    move: Vector2 = field(default_factory=Vector2)
    dash: bool = False


class Player(Entity):
    def __init__(self, pos):
        super().__init__(pos, S.PLAYER_RADIUS, S.YELLOW)
        self.hp = S.PLAYER_MAX_HP
        self.max_hp = S.PLAYER_MAX_HP
        self.facing = Vector2(1, 0)
        # État du dash (écrit par le contrôleur, lu par le rendu / le combat)
        self.dashing = False
        self.iframes_left = 0.0
        self.dash_cd_left = 0.0
        self.trail: list[tuple[Vector2, float]] = []  # images rémanentes

    @property
    def invincible(self) -> bool:
        """À consulter par le système de dégâts (phase 2+)."""
        return self.iframes_left > 0

    def take_damage(self, amount: float) -> bool:
        if self.invincible:
            return False
        self.hp = max(0, self.hp - amount)
        return True

    def draw(self, surface: pygame.Surface) -> None:
        for p, life in self.trail:
            s = pygame.Surface((self.radius * 2,) * 2, pygame.SRCALPHA)
            pygame.draw.circle(s, (*S.CYAN, int(120 * life)), (self.radius,) * 2, self.radius)
            surface.blit(s, p - Vector2(self.radius, self.radius))
        color = S.CYAN if self.invincible else self.color
        pygame.draw.circle(surface, color, self.pos, self.radius)
        pygame.draw.circle(surface, S.WHITE, self.pos, self.radius, 2)
        # indicateur de direction
        pygame.draw.line(surface, S.WHITE, self.pos, self.pos + self.facing * (self.radius + 8), 3)


class PlayerController:
    def __init__(self, player: Player, bounds: pygame.Rect):
        self.player = player
        self.bounds = bounds
        self._dash_time = 0.0
        self._dash_dir = Vector2(1, 0)

    def update(self, intent: Intent, dt: float) -> None:
        p = self.player

        # Timers
        p.iframes_left = max(0.0, p.iframes_left - dt)
        p.dash_cd_left = max(0.0, p.dash_cd_left - dt)
        p.trail = [(pos, life - dt * 5) for pos, life in p.trail if life - dt * 5 > 0]

        move = Vector2(intent.move)
        if move.length_squared() > 0:
            move = move.normalize()
            if not p.dashing:
                p.facing = Vector2(move)

        # Démarrage du dash
        if intent.dash and not p.dashing and p.dash_cd_left <= 0:
            self._dash_dir = Vector2(move) if move.length_squared() > 0 else Vector2(p.facing)
            self._dash_time = S.DASH_DURATION
            p.dashing = True
            p.iframes_left = S.DASH_IFRAMES
            p.dash_cd_left = S.DASH_COOLDOWN

        # Déplacement
        if p.dashing:
            p.pos += self._dash_dir * S.DASH_SPEED * dt
            p.trail.append((Vector2(p.pos), 1.0))
            self._dash_time -= dt
            if self._dash_time <= 0:
                p.dashing = False
        else:
            p.pos += move * S.PLAYER_SPEED * dt

        self._clamp(p)

    def _clamp(self, p: Player) -> None:
        b, r = self.bounds, p.radius
        p.pos.x = min(max(p.pos.x, b.left + r), b.right - r)
        p.pos.y = min(max(p.pos.y, b.top + r), b.bottom - r)
