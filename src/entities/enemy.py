"""Ennemis. Le déplacement est un steering behavior (Reynolds) : une force de pilotage
(`think()`, propre à chaque espèce) limitée par une accélération maximale, plus une séparation
entre voisins. Chaque espèce redéfinit `think()` :

- Rattata   : poursuite simple.
- Zubat     : vole en zigzag, rapide et fragile.
- Racaillou : lent et très résistant, charge le joueur après une courte préparation.
- Fantominus: garde ses distances et tire des Ball'Ombre (attaque hostile typée).
- Voltorbe  : fonce puis explose (zone) après une mèche, sauf s'il est tué avant.
"""
import math
import random

import pygame
from pygame import Vector2

from .. import settings as S
from ..combat import moves as M
from ..combat.types import PType
from ..species import GASTLY_DEX, GEODUDE_DEX, RATTATA_DEX, VOLTORB_DEX, ZUBAT_DEX
from .entity import Entity, Stats


class Enemy(Entity):
    speed = 140.0
    accel = 900.0            # px/s² : force de pilotage maximale
    turn_rate = 8.0          # réactivité : vitesse atteinte en ~1/turn_rate s
    contact_damage = 10.0
    contact_cooldown = 0.8   # s entre deux touches
    separation_radius = 46.0

    def __init__(self, pos, radius, color, types, max_hp, stats: Stats | None = None):
        super().__init__(pos, radius, color, types, max_hp)
        if stats:
            self.stats = stats
        self.vel = Vector2()
        self.spawn_left = S.SPAWN_DELAY
        self.contact_cd = 0.0
        self.flash = 0.0
        self.act_anim, self.act_left = "Attack", 0.0   # animation d'action en cours (tir, charge...)
        self.sprite_nonce = 0
        self.out_attacks: list = []                    # attaques hostiles créées, récupérées par la salle

    # --- état / rendu de sprites ---
    @property
    def spawning(self) -> bool:
        return self.spawn_left > 0

    @property
    def vulnerable(self) -> bool:
        return self.alive and not self.spawning

    @property
    def sprite_visible(self) -> bool:
        return self.vulnerable or self.dying

    @property
    def sprite_anim(self) -> tuple:
        if self.flash > 0:
            return ("Hurt", 1.0)
        if self.act_left > 0:
            return (self.act_anim, 1.5)
        if self.contact_cd > self.contact_cooldown - 0.35:
            return ("Attack", 1.6)
        v = self.vel.length()
        return ("Walk", max(0.8, 1.3 * v / self.speed)) if v > 10 else ("Idle", 1.0)

    @property
    def sprite_tint(self):
        return None

    def act(self, anim: str, duration: float) -> None:
        """Joue une animation d'action (relancée à chaque appel)."""
        self.act_anim, self.act_left = anim, duration
        self.sprite_nonce += 1

    def register_hit(self) -> None:
        """Appelé quand le contact a touché le joueur : délai avant la prochaine touche + animation."""
        self.contact_cd = self.contact_cooldown
        self.sprite_nonce += 1

    def fire(self, spec: M.MoveSpec, direction: Vector2) -> None:
        self.out_attacks.append(spec.build(self, direction))

    def take_damage(self, amount: float) -> bool:
        if self.spawning:
            return False
        hit = super().take_damage(amount)
        if hit:
            self.flash = 0.1
        return hit

    # --- steering ---
    @property
    def speed_cap(self) -> float:
        return self.speed

    def seek(self, target: Vector2) -> Vector2:
        to = target - self.pos
        if to.length_squared() == 0:
            return Vector2()
        return (to.normalize() * self.speed - self.vel) * self.turn_rate

    def separation(self, others) -> Vector2:
        push = Vector2()
        for o in others:
            if o is self or not o.alive:
                continue
            away = self.pos - o.pos
            d = away.length()
            if 0 < d < self.separation_radius:
                push += away / d * (1 - d / self.separation_radius)
        return push * self.speed

    def think(self, dt: float, player, others) -> Vector2:
        """Force de pilotage de cette frame (à redéfinir par espèce)."""
        return self.seek(player.pos) + self.separation(others)

    def update(self, dt: float, player=None, others=(), bounds: pygame.Rect | None = None) -> None:
        self.flash = max(0.0, self.flash - dt)
        self.contact_cd = max(0.0, self.contact_cd - dt)
        self.act_left = max(0.0, self.act_left - dt)
        if not self.alive:
            self.tick_death(dt)
            return
        self.tick_status(dt)
        if self.spawning:
            self.spawn_left -= dt
            return
        if player is None:
            return
        force = self.think(dt, player, others)
        if not self.alive:          # mort pendant think() (ex. explosion)
            return
        if force.length() > self.accel:
            force.scale_to_length(self.accel)
        self.vel += force * dt
        if self.vel.length() > self.speed_cap:
            self.vel.scale_to_length(self.speed_cap)
        self.pos += self.vel * dt
        if self.vel.length_squared() > 1:
            self.facing = self.vel.normalize()
        if bounds is not None:
            r = self.radius
            self.pos.x = min(max(self.pos.x, bounds.left + r), bounds.right - r)
            self.pos.y = min(max(self.pos.y, bounds.top + r), bounds.bottom - r)

    def can_touch(self, player) -> bool:
        return (self.vulnerable and self.contact_cd <= 0
                and self.pos.distance_to(player.pos) <= self.radius + player.radius)

    def draw(self, surface) -> None:   # cercle de secours (sans sprite)
        if self.spawning:  # cercle qui se remplit = apparition
            k = 1 - self.spawn_left / S.SPAWN_DELAY
            pygame.draw.circle(surface, self.color, self.pos, max(2, self.radius * k), 2)
            return
        if self.dying:     # rétrécit en mourant
            r = max(1, self.radius * (1 - self.death_t / S.DEATH_DURATION))
            pygame.draw.circle(surface, self.color, self.pos, r)
            return
        if not self.alive:
            return
        pygame.draw.circle(surface, S.WHITE if self.flash > 0 else self.color, self.pos, self.radius)
        pygame.draw.circle(surface, (20, 20, 20), self.pos, self.radius, 2)
        self.draw_status(surface)   # barre de PV et nom : dessinés par le HUD


class Rattata(Enemy):
    name = "Rattata"
    species = RATTATA_DEX
    speed = 150.0

    def __init__(self, pos):
        super().__init__(pos, 18, (160, 110, 190), (PType.NORMAL,), max_hp=60)


class Zubat(Enemy):
    """Rapide et fragile : zigzague autour de sa trajectoire."""
    name = "Zubat"
    species = ZUBAT_DEX
    speed = 235.0
    contact_damage = 8.0
    contact_cooldown = 0.7

    def __init__(self, pos):
        super().__init__(pos, 16, (110, 120, 200), (PType.POISON, PType.VOL), max_hp=36)
        self._t = 0.0
        self._phase = random.uniform(0, math.tau)

    def think(self, dt, player, others) -> Vector2:
        self._t += dt
        to = player.pos - self.pos
        if to.length_squared() < 1:
            return self.separation(others)
        dirn = to.normalize()
        perp = Vector2(-dirn.y, dirn.x)
        # vitesse désirée = avance + balancier latéral (zigzag d'environ 35 px d'amplitude)
        want = dirn * self.speed * 0.85 + perp * math.sin(self._t * 5 + self._phase) * self.speed * 0.9
        return (want - self.vel) * self.turn_rate + self.separation(others)


class Racaillou(Enemy):
    """Lent, très résistant (Déf x2) : prépare puis fonce en ligne droite."""
    name = "Racaillou"
    species = GEODUDE_DEX
    speed = 75.0
    contact_damage = 16.0
    contact_cooldown = 1.0
    WINDUP, CHARGE, REST, CHARGE_SPEED = 0.6, 0.5, 0.8, 430.0

    def __init__(self, pos):
        super().__init__(pos, 24, (150, 140, 110), (PType.ROCHE, PType.SOL), max_hp=170,
                         stats=Stats(atk=1.2, defense=2.0, spdef=0.9))
        self.state, self.state_t = "walk", random.uniform(1.2, 2.2)
        self._dir = Vector2(0, 1)

    @property
    def speed_cap(self) -> float:
        return self.CHARGE_SPEED if self.state == "charge" else self.speed

    @property
    def sprite_tint(self):
        return (70, 20, 0) if self.state == "windup" and int(self.state_t * 14) % 2 == 0 else None

    def think(self, dt, player, others) -> Vector2:
        self.state_t -= dt
        to = player.pos - self.pos
        brake = -self.vel * self.turn_rate
        if self.state == "walk":
            if self.state_t <= 0 and to.length() < 340:
                self.state, self.state_t = "windup", self.WINDUP
            return self.seek(player.pos) + self.separation(others)
        if self.state == "windup":                        # s'arrête et vise
            if self.state_t <= 0:
                self._dir = to.normalize() if to.length_squared() else Vector2(0, 1)
                self.state, self.state_t = "charge", self.CHARGE
                self.act("Attack", self.CHARGE)
            return brake
        if self.state == "charge":
            if self.state_t <= 0:
                self.state, self.state_t = "rest", self.REST
            return (self._dir * self.CHARGE_SPEED - self.vel) * self.turn_rate
        if self.state_t <= 0:                             # rest -> walk
            self.state, self.state_t = "walk", random.uniform(1.5, 2.5)
        return brake


class Fantominus(Enemy):
    """Tireur : reste à bonne distance (fuit si on s'approche) et lance des Ball'Ombre."""
    name = "Fantominus"
    species = GASTLY_DEX
    speed = 100.0
    contact_damage = 6.0
    NEAR, FAR, WINDUP = 210.0, 340.0, 0.45

    def __init__(self, pos):
        super().__init__(pos, 20, (100, 80, 150), (PType.SPECTRE, PType.POISON), max_hp=48)
        self.shoot_t = random.uniform(1.0, 2.0)
        self.windup = 0.0
        self._side = random.choice((-1, 1))

    def think(self, dt, player, others) -> Vector2:
        to = player.pos - self.pos
        d = to.length()
        dirn = to.normalize() if d else Vector2(0, 1)
        if self.windup > 0:                               # tire : ne bouge presque plus
            self.windup -= dt
            if self.windup <= 0:
                self.fire(M.ENEMY_BALLE_OMBRE, (player.pos - self.pos).normalize())
            return -self.vel * self.turn_rate * 0.5
        self.shoot_t -= dt
        if self.shoot_t <= 0 and d < 480:
            self.shoot_t = M.ENEMY_BALLE_OMBRE.cooldown
            self.windup = self.WINDUP
            self.act("Shoot", self.WINDUP + 0.2)
        if d < self.NEAR:
            want = -dirn * self.speed                     # recule
        elif d > self.FAR:
            want = dirn * self.speed                      # se rapproche
        else:
            want = Vector2(-dirn.y, dirn.x) * self.side_speed()   # tourne autour du joueur
        return (want - self.vel) * self.turn_rate + self.separation(others)

    def side_speed(self) -> float:
        return self._side * self.speed * 0.7


class Voltorbe(Enemy):
    """Fonce sur le joueur ; une fois proche, la mèche s'allume puis il explose (zone)."""
    name = "Voltorbe"
    species = VOLTORB_DEX
    speed = 135.0
    contact_damage = 0.0
    TRIGGER, FUSE = 120.0, 0.8

    def __init__(self, pos):
        super().__init__(pos, 18, (220, 70, 70), (PType.ELECTRIK,), max_hp=40)
        self.fuse = None
        self._t = 0.0

    @property
    def sprite_tint(self):      # clignote en rouge pendant la mèche
        return (130, 0, 0) if self.fuse is not None and int(self._t * 14) % 2 == 0 else None

    def think(self, dt, player, others) -> Vector2:
        self._t += dt
        d = self.pos.distance_to(player.pos)
        if self.fuse is None and d < self.TRIGGER:
            self.fuse = self.FUSE
        if self.fuse is not None:
            self.fuse -= dt
            if self.fuse <= 0:
                self.fire(M.EXPLOSION, Vector2(0, 1))     # zone centrée sur lui
                Entity.take_damage(self, self.max_hp)     # il se sacrifie
                return Vector2()
            return self.seek(player.pos) * 0.25 + self.separation(others)
        return self.seek(player.pos) + self.separation(others)
