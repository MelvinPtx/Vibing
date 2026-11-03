"""Joueur : `Player` = données/rendu, `PlayerController` = logique de déplacement.

Le contrôleur ne lit PAS le clavier lui-même : il reçoit un `Intent`
(direction + dash demandé). Ainsi on peut le piloter depuis le clavier,
une manette, une IA ou un test automatisé.
"""
from dataclasses import dataclass, field

import pygame
from pygame import Vector2

from .. import settings as S
from ..starters import DEFAULT_STARTER, Starter
from .entity import Entity, Stats


@dataclass
class Intent:
    move: Vector2 = field(default_factory=Vector2)
    dash: bool = False
    attack: str | None = None   # "basic" | "special" | "cast"
    aim: Vector2 | None = None  # point visé (souris) ; None = direction regardée


class Player(Entity):
    """Le Pokémon contrôlé : ses types, stats, PV, vitesse et capacités viennent du `Starter`."""

    def __init__(self, pos, starter: Starter = DEFAULT_STARTER):
        super().__init__(pos, S.PLAYER_RADIUS, S.YELLOW, types=starter.types, max_hp=starter.max_hp)
        self.starter = starter
        self.name = starter.name
        self.species = starter.dex
        self.stats = Stats(starter.atk, starter.spa, starter.defense, starter.spdef)
        self.speed_mult = starter.speed_mult
        self.moveset = dict(starter.moves)            # emplacement -> MoveSpec
        self.moving = False
        self.act_anim, self.act_left, self.act_nonce = "Attack", 0.0, 0   # animation d'attaque en cours
        self.atk_cd = {slot: 0.0 for slot in self.moveset}
        self.modifiers: list = []   # Modifier actifs (src/items)
        self.facing = Vector2(1, 0)
        # État du dash (écrit par le contrôleur, lu par le rendu / le combat)
        self.dashing = False
        self.iframes_left = 0.0
        self.hurt_left = 0.0   # invincibilité après avoir été touché
        self.dash_cd_left = 0.0
        self.trail: list[tuple[Vector2, float]] = []  # images rémanentes

    @property
    def dying(self) -> bool:          # le K.O. du joueur est géré par l'écran de fin
        return False

    @property
    def invincible(self) -> bool:
        """À consulter par le système de dégâts (phase 2+)."""
        return self.iframes_left > 0 or self.hurt_left > 0

    # --- rendu de sprites ---
    @property
    def sprite_visible(self) -> bool:
        return True

    @property
    def sprite_nonce(self) -> int:
        return self.act_nonce

    @property
    def sprite_anim(self) -> tuple:
        if self.hurt_left > S.HIT_IFRAMES - 0.3:
            return ("Hurt", 1.0)
        if self.act_left > 0:
            return (self.act_anim, 1.5)
        if self.dashing:
            return ("Walk", 2.2)
        return ("Walk", 1.0) if self.moving else ("Idle", 1.0)

    @property
    def sprite_blink(self) -> bool:     # clignote pendant l'invincibilité post-coup
        return self.hurt_left > 0 and int(self.hurt_left * 18) % 2 == 0

    @property
    def sprite_tint(self):              # teinte cyan pendant les i-frames du dash
        return (0, 70, 90) if self.iframes_left > 0 else None

    def take_damage(self, amount: float) -> bool:
        if self.invincible:
            return False
        hit = super().take_damage(amount)
        if hit:
            self.hurt_left = S.HIT_IFRAMES
        return hit

    def draw(self, surface: pygame.Surface) -> None:
        for p, life in self.trail:
            s = pygame.Surface((self.radius * 2,) * 2, pygame.SRCALPHA)
            pygame.draw.circle(s, (*S.CYAN, int(120 * life)), (self.radius,) * 2, self.radius)
            surface.blit(s, p - Vector2(self.radius, self.radius))
        color = S.RED if self.hurt_left > 0 else (S.CYAN if self.invincible else self.color)
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

    def update(self, intent: Intent, dt: float) -> list:
        """Avance d'une frame. Renvoie la liste des Attack créées (à confier au CombatSystem)."""
        p = self.player
        for k in p.atk_cd:
            p.atk_cd[k] = max(0.0, p.atk_cd[k] - dt)

        # Timers
        p.iframes_left = max(0.0, p.iframes_left - dt)
        p.dash_cd_left = max(0.0, p.dash_cd_left - dt)
        p.hurt_left = max(0.0, p.hurt_left - dt)
        p.act_left = max(0.0, p.act_left - dt)
        for mod in p.modifiers:
            mod.on_update(p, dt)
        p.trail = [(pos, life - dt * 5) for pos, life in p.trail if life - dt * 5 > 0]

        move = Vector2(intent.move)
        if move.length_squared() > 0:
            move = move.normalize()
            if not p.dashing:
                p.facing = Vector2(move)
        p.moving = move.length_squared() > 0

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
            p.pos += move * S.PLAYER_SPEED * p.speed_mult * dt

        self._clamp(p)

        spawned = []
        if intent.attack in p.moveset and p.atk_cd[intent.attack] <= 0 and not p.dashing:
            if intent.aim is not None and (intent.aim - p.pos).length_squared() > 1:
                p.facing = (intent.aim - p.pos).normalize()
            spec = p.moveset[intent.attack]
            atk = spec.build(p, Vector2(p.facing))
            atk.slot = intent.attack
            p.act_anim, p.act_left = spec.anim, 0.35
            p.act_nonce += 1
            for mod in p.modifiers:
                mod.on_attack(atk, p)
            spawned.append(atk)
            p.atk_cd[intent.attack] = spec.cooldown
        return spawned

    def _clamp(self, p: Player) -> None:
        b, r = self.bounds, p.radius
        p.pos.x = min(max(p.pos.x, b.left + r), b.right - r)
        p.pos.y = min(max(p.pos.y, b.top + r), b.bottom - r)
