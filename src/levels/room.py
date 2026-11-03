"""Logique de salle (sans rendu) : vagues, verrouillage des sorties, portes de récompense."""
import random
from dataclasses import dataclass
from enum import Enum

import pygame
from pygame import Vector2

from .. import settings as S
from ..entities.boss import BOSS_ROTATION
from ..entities.enemy import Fantominus, Racaillou, Rattata, Voltorbe, Zubat
from .obstacles import NavGrid, generate_layout, pick_layout


# (classe, première salle où elle apparaît, poids de tirage) : la difficulté monte avec les salles
ENEMY_TABLE = [(Rattata, 1, 5), (Zubat, 2, 3), (Racaillou, 3, 2), (Fantominus, 4, 2), (Voltorbe, 6, 2)]
BOSS_EVERY = 5      # une salle de boss toutes les 5 salles ; les boss alternent et se renforcent


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
    def __init__(self, arena: pygame.Rect, player, rng: random.Random | None = None, start_number: int = 1):
        self.arena = arena
        self.player = player
        self.rng = rng or random.Random()
        self.room_number = start_number - 1
        self.obstacles: list = []
        self.layout = "open"
        self.nav = None
        self._nav_t = 0.0
        self._boss_cleared = False
        self.enemies: list = []          # vivants + ceux dont l'animation de mort est en cours
        self.out_attacks: list = []     # attaques hostiles à confier au CombatSystem (drain_attacks)
        self.doors: list[Door] = []
        self.state = RoomState.COMBAT
        self.start_room()

    # --- génération ---
    def start_room(self) -> None:
        self.room_number += 1
        self.state = RoomState.COMBAT
        self.doors = []
        self.player.pos = Vector2(self.arena.centerx, self.arena.bottom - 60)
        boss_room = self.room_number % BOSS_EVERY == 0
        self.layout = pick_layout(self.rng, self.room_number, boss_room)
        self.obstacles = generate_layout(self.layout, self.arena, self.rng)
        if not self.obstacles:
            self.layout = "open"
        self.nav = NavGrid(self.arena, self.obstacles) if self.obstacles else None
        self._nav_t = 0.0
        self.out_attacks = []
        if boss_room:                                      # salle de boss : le boss seul, au fond
            idx = self.room_number // BOSS_EVERY - 1
            boss = BOSS_ROTATION[idx % len(BOSS_ROTATION)](
                Vector2(self.arena.centerx, self.arena.top + 190), level=idx // len(BOSS_ROTATION), rng=self.rng)
            self.enemies = [self._adopt(boss)]
            return
        count = min(2 + self.room_number, 10)
        pool = [(cls, w) for cls, first, w in ENEMY_TABLE if first <= self.room_number]
        classes, weights = zip(*pool)
        self.enemies = [self._adopt(cls(self._spawn_point()))
                        for cls in self.rng.choices(classes, weights=weights, k=count)]

    def _adopt(self, enemy):
        """Donne à l'ennemi les obstacles et la navigation de la salle."""
        enemy.obstacles, enemy.nav = self.obstacles, self.nav
        return enemy

    def _spawn_point(self) -> Vector2:
        for _ in range(50):
            p = Vector2(self.rng.uniform(self.arena.left + 40, self.arena.right - 40),
                        self.rng.uniform(self.arena.top + 60, self.arena.bottom - 40))
            if (p.distance_to(self.player.pos) >= S.MIN_SPAWN_DIST
                    and not any(o.inflate(70, 70).collidepoint(p) for o in self.obstacles)):
                return p
        return Vector2(self.arena.centerx, self.arena.top + 60)

    def _minion_point(self, boss) -> Vector2:
        p = boss.pos + Vector2(self.rng.uniform(-110, 110), self.rng.uniform(70, 140))
        p.x = min(max(p.x, self.arena.left + 40), self.arena.right - 40)
        p.y = min(max(p.y, self.arena.top + 40), self.arena.bottom - 40)
        return p

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
    def boss(self):
        """Le boss de la salle (vivant ou en train de mourir), sinon None."""
        return next((e for e in self.enemies if getattr(e, "is_boss", False)), None)

    @property
    def telegraphs(self) -> list:
        b = self.boss
        return b.telegraphs if b is not None and b.alive else []

    def consume_boss_clear(self) -> bool:
        """True une seule fois quand un boss vient d'être vaincu (l'interface soigne le joueur)."""
        done, self._boss_cleared = self._boss_cleared, False
        return done

    @property
    def alive_count(self) -> int:
        return sum(e.alive for e in self.enemies)

    def drain_attacks(self) -> list:
        """Attaques hostiles créées depuis le dernier appel (tirs, explosions)."""
        out, self.out_attacks = self.out_attacks, []
        return out

    @property
    def exits_locked(self) -> bool:
        return self.state is RoomState.COMBAT

    def update(self, dt: float) -> RewardKind | None:
        """Renvoie la récompense choisie si le joueur franchit une porte ouverte."""
        if self.state is RoomState.COMBAT:
            if self.nav is not None:                        # chemin vers le joueur, recalculé 5x/s
                self._nav_t -= dt
                if self._nav_t <= 0:
                    self._nav_t = 0.2
                    self.nav.update_target(self.player.pos)
            for e in list(self.enemies):
                e.update(dt, self.player, self.enemies, self.arena)
                self.out_attacks.extend(e.out_attacks)
                e.out_attacks.clear()
                for cls in getattr(e, "spawn_requests", []):    # invocations d'un boss
                    self.enemies.append(self._adopt(cls(self._minion_point(e))))
                if getattr(e, "spawn_requests", None):
                    e.spawn_requests.clear()
                if e.can_touch(self.player) and self.player.take_damage(e.contact_damage):
                    e.register_hit()
        else:                                    # salle vidée : les morts finissent leur animation
            for e in self.enemies:
                e.update(dt)
        self.enemies = [e for e in self.enemies if e.alive or e.dying]
        if self.state is RoomState.COMBAT:
            if not self.alive_count:
                self._boss_cleared = any(getattr(e, "is_boss", False) for e in self.enemies)
                self._open_doors()
            return None
        for d in self.doors:
            if d.open and d.rect.colliderect(self.player.rect):
                reward = d.reward
                self.start_room()
                return reward
        return None
