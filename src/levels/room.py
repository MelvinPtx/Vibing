"""Logique de salle (sans rendu) : vagues, verrouillage des sorties, portes de récompense."""
import random
from dataclasses import dataclass
from enum import Enum

import pygame
from pygame import Vector2

from .. import settings as S
from ..entities.enemy import Rattata


class RewardKind(Enum):
    CAPSULE = "Capsule Technique"
    OBJET = "Objet Stratégique"
    SOIN = "Baie (soin)"


class RoomState(Enum):
    COMBAT = "combat"
    CLEARED = "cleared"


@dataclass
class Door:
    rect: pygame.Rect
    reward: RewardKind
    open: bool = False


class RoomManager:
    def __init__(self, arena: pygame.Rect, player, rng: random.Random | None = None):
        self.arena = arena
        self.player = player
        self.rng = rng or random.Random()
        self.room_number = 0
        self.enemies: list = []
        self.doors: list[Door] = []
        self.state = RoomState.COMBAT
        self.start_room()

    # --- génération ---
    def start_room(self) -> None:
        self.room_number += 1
        self.state = RoomState.COMBAT
        self.doors = []
        self.player.pos = Vector2(self.arena.centerx, self.arena.bottom - 60)
        count = min(2 + self.room_number, 10)
        self.enemies = [Rattata(self._spawn_point()) for _ in range(count)]

    def _spawn_point(self) -> Vector2:
        for _ in range(50):
            p = Vector2(self.rng.uniform(self.arena.left + 40, self.arena.right - 40),
                        self.rng.uniform(self.arena.top + 60, self.arena.bottom - 40))
            if p.distance_to(self.player.pos) >= S.MIN_SPAWN_DIST:
                return p
        return Vector2(self.arena.centerx, self.arena.top + 60)

    def _open_doors(self) -> None:
        a = self.arena
        rewards = self.rng.sample(list(RewardKind), 2)  # 2 récompenses différentes
        xs = (a.centerx - 160, a.centerx + 160)
        self.doors = [Door(pygame.Rect(x - S.DOOR_W // 2, a.top - S.DOOR_H // 2,
                                       S.DOOR_W, S.DOOR_H), r, open=True)
                      for x, r in zip(xs, rewards)]
        self.state = RoomState.CLEARED

    # --- état ---
    @property
    def targets(self) -> list:
        """Ennemis ciblables par le CombatSystem."""
        return [e for e in self.enemies if e.vulnerable]

    @property
    def exits_locked(self) -> bool:
        return self.state is RoomState.COMBAT

    def update(self, dt: float) -> RewardKind | None:
        """Renvoie la récompense choisie si le joueur franchit une porte ouverte."""
        if self.state is RoomState.COMBAT:
            for e in self.enemies:
                e.update(dt, self.player, self.enemies, self.arena)
                if e.can_touch(self.player) and self.player.take_damage(e.contact_damage):
                    e.register_hit()
            self.enemies = [e for e in self.enemies if e.alive]
            if not self.enemies:
                self._open_doors()
            return None
        for d in self.doors:
            if d.open and d.rect.colliderect(self.player.rect):
                reward = d.reward
                self.start_room()
                return reward
        return None
