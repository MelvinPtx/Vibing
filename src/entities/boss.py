"""Boss : gros Pokémon à 3 phases (changement aux seuils de PV), attaques télégraphiées,
invocations d'ennemis. Chaque attaque `atk_xxx` annonce ses zones de danger (`Telegraph`, dessinées
au sol par l'interface) puis crée ses attaques hostiles après un délai : le joueur a le temps de
réagir (s'écarter, se mettre à couvert derrière un rocher, ou dasher dans l'attaque).
"""
import random
from dataclasses import dataclass, field

import pygame
from pygame import Vector2

from .. import settings as S
from ..combat import moves as M
from ..combat.types import PType
from ..species import GENGAR_DEX, ONIX_DEX
from .enemy import Enemy, Fantominus, Racaillou
from .entity import Stats


@dataclass
class Telegraph:
    """Zone de danger annoncée au sol. kind : "circle" (rayon `radius`) ou "line" (rectangle de
    demi-largeur `radius` et de longueur `length` dans la direction `direction`)."""
    kind: str
    pos: Vector2
    radius: float
    time_left: float
    total: float
    direction: Vector2 = field(default_factory=Vector2)
    length: float = 0.0

    @property
    def progress(self) -> float:
        return 1 - self.time_left / self.total


class Boss(Enemy):
    is_boss = True
    sprite_scale = 3
    INTRO = 1.6                        # s d'apparition (intouchable)
    contact_damage = 20.0
    contact_cooldown = 1.0
    PHASE_AT = (0.6, 0.3)              # fractions de PV : début des phases 2 et 3
    ATTACK_GAP = (1.4, 1.0, 0.7)       # pause entre deux attaques, par phase
    ATTACKS: dict = {}                 # phase -> noms d'attaques possibles (méthodes atk_<nom>)

    def __init__(self, pos, radius, color, types, max_hp, stats, level: int = 0, rng=None):
        super().__init__(pos, radius, color, types, max_hp * (1 + 0.6 * level), stats)
        self.level = level
        self.rng = rng or random.Random()
        self.spawn_left = self.INTRO
        self.phase = 1
        self.telegraphs: list = []
        self.spawn_requests: list = []         # classes d'ennemis à invoquer (lu par la salle)
        self.events: list = []                 # messages pour l'interface ("Phase 2 !")
        self.hidden = False                    # téléportation : invisible et intouchable
        self.cd, self.busy, self._last = 1.2, 0.0, None
        self._timers: list = []
        self._bounds = None

    # --- état ---
    @property
    def vulnerable(self) -> bool:
        return self.alive and not self.spawning and not self.hidden

    def draw(self, surface) -> None:
        if not self.hidden:
            super().draw(surface)

    def stun(self, seconds: float) -> None:      # les boss ne sont ni apeurés ni paralysés
        pass

    def slow(self, seconds: float) -> None:
        pass

    # --- outils pour écrire les attaques ---
    def after(self, delay: float, fn) -> None:
        self._timers.append([delay, fn])

    def warn(self, kind: str, pos, radius: float, t: float, direction=None, length: float = 0.0):
        tel = Telegraph(kind, Vector2(pos), radius, t, t, Vector2(direction or (0, 0)), length)
        self.telegraphs.append(tel)
        return tel

    def aim(self, player) -> Vector2:
        d = player.pos - self.pos
        return d.normalize() if d.length_squared() else Vector2(0, 1)

    def clamp_inside(self, p: Vector2, margin: float = 60) -> Vector2:
        if self._bounds is not None:
            b = self._bounds
            p.x = min(max(p.x, b.left + margin), b.right - margin)
            p.y = min(max(p.y, b.top + margin), b.bottom - margin)
        return p

    # --- cycle de vie ---
    def update(self, dt: float, player=None, others=(), bounds=None) -> None:
        self._bounds = bounds
        super().update(dt, player, others, bounds)

    def _tick(self, dt: float) -> None:
        for t in self._timers:
            t[0] -= dt
        due = [t for t in self._timers if t[0] <= 0]
        self._timers = [t for t in self._timers if t[0] > 0]
        for _, fn in due:
            fn()
        for tel in self.telegraphs:
            tel.time_left -= dt
        self.telegraphs = [t for t in self.telegraphs if t.time_left > 0]

    def _check_phase(self) -> None:
        if self.phase < 3 and self.hp / self.max_hp <= self.PHASE_AT[self.phase - 1]:
            self.phase += 1
            self.events.append(f"Phase {self.phase} !")
            self.on_phase(self.phase)
            self.busy, self.cd = max(self.busy, 0.8), 0.6

    def on_phase(self, phase: int) -> None:
        pass

    def pick_attack(self) -> str:
        pool = [a for a in self.ATTACKS[self.phase] if a != self._last] or self.ATTACKS[self.phase]
        self._last = self.rng.choice(pool)
        return self._last

    def think(self, dt, player, others) -> Vector2:
        self._tick(dt)
        self._check_phase()
        self.busy = max(0.0, self.busy - dt)
        if self.busy <= 0:
            self.cd -= dt
            if self.cd <= 0:
                self.cd = self.ATTACK_GAP[self.phase - 1]
                getattr(self, "atk_" + self.pick_attack())(player)
        return self.movement(dt, player, others)

    def movement(self, dt, player, others) -> Vector2:
        return self.seek(self.chase_point(player)) * 0.5 + self.separation(others)


class Onix(Boss):
    """Roche/Sol, énorme et très résistant (Déf x2,2). Jets de pierres, Séisme (grande zone à
    fuir ou à traverser en dash), Charge en ligne droite ; en phase 2+ des éboulements et ses
    Racaillou."""
    name = "Onix"
    species = ONIX_DEX
    speed = 70.0
    sprite_scale = 3
    contact_damage = 22.0
    CHARGE_SPEED = 560.0
    ATTACKS = {1: ["rocks", "quake", "charge"], 2: ["rocks", "rockfall", "charge", "quake"],
               3: ["rockfall", "charge", "rocks", "quake"]}

    def __init__(self, pos, level: int = 0, rng=None):
        super().__init__(pos, 46, (150, 140, 110), (PType.ROCHE, PType.SOL), 1000,
                         Stats(atk=1.3, defense=2.2, spdef=1.2), level, rng)
        self.state = "idle"        # idle | windup | charge
        self._dir = Vector2(0, 1)

    @property
    def speed_cap(self) -> float:
        return self.CHARGE_SPEED if self.state == "charge" else self.speed

    def on_phase(self, phase: int) -> None:
        self.spawn_requests += [Racaillou, Racaillou] if phase == 2 else [Racaillou]

    def movement(self, dt, player, others) -> Vector2:
        if self.state == "windup":
            return -self.vel * self.turn_rate
        if self.state == "charge":
            return (self._dir * self.CHARGE_SPEED - self.vel) * self.turn_rate
        return super().movement(dt, player, others)

    def atk_rocks(self, player) -> None:
        n = 3 if self.phase == 1 else 5
        self.act("Shoot", 0.7)
        self.busy = 1.0

        def fire():
            base = self.aim(player)
            for i in range(n):
                self.fire(M.JET_PIERRES, base.rotate((i - (n - 1) / 2) * 18))
        self.after(0.6, fire)

    def atk_quake(self, player) -> None:
        pos = Vector2(self.pos)
        self.act("Swing", 1.1)
        self.busy = 1.6
        self.warn("circle", pos, M.SEISME.radius, 1.0)
        self.after(1.0, lambda: self.out_attacks.append(M.SEISME.build_at(self, pos)))

    def atk_charge(self, player) -> None:
        self._dir = self.aim(player)
        self.state = "windup"
        self.busy = 2.5
        self.warn("line", self.pos, self.radius, 0.9, self._dir, 720)

        def go():
            self.state = "charge"
            self.act("Attack", 0.8)
        self.after(0.9, go)
        self.after(1.7, lambda: setattr(self, "state", "idle"))

    def atk_rockfall(self, player) -> None:
        self.act("Swing", 1.0)
        self.busy = 1.5
        spots = [Vector2(player.pos)] + [
            self.clamp_inside(player.pos + Vector2(self.rng.uniform(-230, 230), self.rng.uniform(-230, 230)))
            for _ in range(4)]
        for p in spots:
            self.warn("circle", p, M.EBOULEMENT.radius, 1.1)
        self.after(1.1, lambda: [self.out_attacks.append(M.EBOULEMENT.build_at(self, p)) for p in spots])


class Ectoplasma(Boss):
    """Spectre/Poison, volant : volées de Ball'Ombre, anneau de projectiles, téléportation avec
    coup de poing en zone, bombes toxiques ; en phase 2+ il invoque des Fantominus. Normal ne
    lui fait rien (immunité) : choisir ses capacités en conséquence."""
    name = "Ectoplasma"
    species = GENGAR_DEX
    speed = 95.0
    flies = True
    sprite_scale = 4
    contact_damage = 14.0
    NEAR, FAR = 220.0, 340.0
    ATTACKS = {1: ["volley", "ring", "blink"], 2: ["volley", "ring", "blink", "bombs"],
               3: ["ring", "blink", "bombs", "volley"]}

    def __init__(self, pos, level: int = 0, rng=None):
        super().__init__(pos, 34, (110, 70, 150), (PType.SPECTRE, PType.POISON), 760,
                         Stats(atk=1.2, spa=1.3, defense=1.0, spdef=1.2), level, rng)
        self._side = self.rng.choice((-1, 1))

    def on_phase(self, phase: int) -> None:
        self.spawn_requests += [Fantominus, Fantominus] if phase == 2 else [Fantominus]

    def movement(self, dt, player, others) -> Vector2:
        if self.hidden:
            self.vel *= 0
            return Vector2()
        to = player.pos - self.pos
        d = to.length()
        dirn = to.normalize() if d else Vector2(0, 1)
        if d < self.NEAR:
            want = -dirn * self.speed
        elif d > self.FAR:
            want = dirn * self.speed
        else:
            want = Vector2(-dirn.y, dirn.x) * self._side * self.speed * 0.6
        if self.busy > 0:
            want *= 0.3
        return (want - self.vel) * self.turn_rate

    def atk_volley(self, player) -> None:
        n = 3 if self.phase == 1 else 5
        self.act("Shoot", 0.6)
        self.busy = 1.0

        def fire():
            base = self.aim(player)
            for i in range(n):
                self.fire(M.BOSS_BALLE_OMBRE, base.rotate((i - (n - 1) / 2) * 16))
        self.after(0.5, fire)

    def atk_ring(self, player) -> None:
        n = 10 if self.phase == 1 else 14
        self.act("Charge", 0.8)
        self.busy = 1.2
        self.warn("circle", self.pos, 64, 0.8)
        offset = self.rng.uniform(0, 360)

        def fire():
            for i in range(n):
                self.fire(M.BOSS_BALLE_OMBRE, Vector2(1, 0).rotate(offset + 360 / n * i))
        self.after(0.8, fire)

    def atk_blink(self, player) -> None:
        angle = self.rng.uniform(0, 360)
        dest = self.clamp_inside(player.pos + Vector2(150, 0).rotate(angle))
        self.hidden = True
        self.busy = 1.5
        self.warn("circle", dest, M.POING_OMBRE.radius, 0.9)

        def appear():
            self.pos = Vector2(dest)
            self.vel = Vector2()
            self.hidden = False
            self.act("Attack", 0.4)
        self.after(0.7, appear)
        self.after(0.9, lambda: self.out_attacks.append(M.POING_OMBRE.build_at(self, dest)))

    def atk_bombs(self, player) -> None:
        self.act("Swing", 0.8)
        self.busy = 1.3
        spots = [self.clamp_inside(player.pos + Vector2(self.rng.uniform(-170, 170), self.rng.uniform(-170, 170)))
                 for _ in range(4)]
        for p in spots:
            self.warn("circle", p, M.BOMBE_BEURK.radius, 1.0)
        self.after(1.0, lambda: [self.out_attacks.append(M.BOMBE_BEURK.build_at(self, p)) for p in spots])


BOSS_ROTATION = [Onix, Ectoplasma]
