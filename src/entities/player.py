"""Joueur : `Player` = données/rendu, `PlayerController` = logique de déplacement.

Le contrôleur ne lit PAS le clavier lui-même : il reçoit un `Intent`
(direction + dash demandé). Ainsi on peut le piloter depuis le clavier,
une manette, une IA ou un test automatisé.
"""
from dataclasses import dataclass, field

import pygame
from pygame import Vector2

from .. import settings as S
from ..geometry import resolve
from ..data.pokedex import POKEMON
from ..progression import START_LEVEL, exp_for_level, hp_mult, stat_mult
from ..combat.moves import slot_of, spec_for
from ..starters import DEFAULT_STARTER, Starter, auto_equip
from .entity import Entity, Stats


@dataclass
class Intent:
    move: Vector2 = field(default_factory=Vector2)
    dash: bool = False
    attack: str | None = None   # "basic" | "special" | "cast"
    aim: Vector2 | None = None  # point visé (souris) ; None = direction regardée


@dataclass
class LevelUp:
    """Résultat de `Player.gain_xp` : niveaux gagnés, capacités débloquées, évolution due."""
    levels: list = field(default_factory=list)
    new_moves: list = field(default_factory=list)       # (emplacement, MoveSpec)
    evolve_to: "Starter | None" = None


class Player(Entity):
    """Le Pokémon contrôlé. Types, stats, PV, vitesse et capacités viennent de sa forme (`Starter`) et de
    son niveau ; il gagne de l'expérience, monte de niveau et évolue (voir src/progression.py)."""

    BUFF_TIME, BUFF_MAX = 8.0, 3

    def __init__(self, pos, starter: Starter = DEFAULT_STARTER, level: int = START_LEVEL):
        super().__init__(pos, S.PLAYER_RADIUS, S.YELLOW, types=starter.types, max_hp=starter.max_hp)
        self.form = starter
        self.level = level
        self.growth = POKEMON[starter.dex]["growth"]
        self.xp = exp_for_level(self.growth, level)
        self.buffs: dict = {}                         # stat -> [cumuls, temps restant, bonus par cumul]
        self.moving = False
        self.act_anim, self.act_left, self.act_nonce = "Attack", 0.0, 0   # animation d'attaque en cours
        self.modifiers: list = []   # Modifier actifs (src/items)
        self.facing = Vector2(1, 0)
        # État du dash (écrit par le contrôleur, lu par le rendu / le combat)
        self.dashing = False
        self.iframes_left = 0.0
        self.hurt_left = 0.0   # invincibilité après avoir été touché
        self.dash_cd_left = 0.0
        self.trail: list[tuple[Vector2, float]] = []  # images rémanentes
        self.moveset: dict = {}
        self.atk_cd: dict = {}
        self.known: list = starter.known_at(level)        # identifiants des capacités apprises, dans l'ordre
        self.manual: dict = {}                            # emplacement -> capacité choisie à la main
        self.lunge_left, self.lunge_vec = 0.0, Vector2()
        self._adopt_form(starter)
        self.hp = self.max_hp

    # --- forme, niveau, évolution ---
    @property
    def starter(self) -> Starter:          # forme actuelle (nom historique)
        return self.form

    def _adopt_form(self, form: Starter) -> None:
        self.form = form
        self.name, self.species, self.types = form.name, form.dex, form.types
        for m in form.known_at(self.level):               # comme le Rappel Capacité d'Écarlate/Violet
            if m not in self.known:
                self.known.append(m)
        self.recalc()
        self.refresh_moves()

    def recalc(self) -> None:
        """Recalcule stats et PV max depuis la forme et le niveau ; les PV gagnés sont ajoutés."""
        f, sm = self.form, stat_mult(self.level)
        self.stats = Stats(f.atk * sm, f.spa * sm, f.defense * sm, f.spdef * sm)
        old = self.max_hp
        self.max_hp = f.max_hp * hp_mult(self.level)
        self.hp = min(self.max_hp, self.hp + max(0.0, self.max_hp - old))
        self.speed_mult = f.speed_mult

    def refresh_moves(self) -> list:
        """Recalcule les capacités équipées (choix manuel ou dernière apprise) ; renvoie celles qui changent."""
        equipped = auto_equip(self.known, self.manual)
        new = {slot: spec_for(m) for slot, m in equipped.items()}
        changed = [(slot, spec) for slot, spec in new.items() if self.moveset.get(slot) is not spec]
        self.moveset = new
        for slot in new:
            self.atk_cd.setdefault(slot, 0.0)
        return changed

    def known_for(self, slot: str) -> list:
        """Capacités apprises utilisables sur cet emplacement."""
        return [m for m in self.known if slot_of(m) == slot]

    def equip(self, slot: str, move_id: str) -> bool:
        """Équipe une capacité apprise sur son emplacement (choix du menu « Capacités »)."""
        if move_id not in self.known or slot_of(move_id) != slot:
            return False
        self.manual[slot] = move_id
        self.refresh_moves()
        return True

    @property
    def xp_into_level(self) -> int:
        return int(self.xp - exp_for_level(self.growth, self.level))

    @property
    def xp_span(self) -> int:
        return exp_for_level(self.growth, self.level + 1) - exp_for_level(self.growth, self.level)

    def gain_xp(self, amount: float) -> LevelUp:
        res = LevelUp()
        self.xp += amount
        before = self.level
        while self.level < 100 and self.xp >= exp_for_level(self.growth, self.level + 1):
            self.level += 1
            res.levels.append(self.level)
        if res.levels:
            self.recalc()
            for m, lv in sorted(self.form.learnset.items(), key=lambda kv: (kv[1], kv[0])):
                if before < lv <= self.level and m not in self.known:     # apprend les capacités de ces niveaux
                    self.known.append(m)
                    res.new_moves.append((slot_of(m), spec_for(m)))
            self.refresh_moves()
            self.hp = min(self.max_hp, self.hp + 0.15 * self.max_hp)     # petit soin à chaque montée
        f = self.form
        if f.evolves_to and self.level >= f.evolve_level:
            res.evolve_to = f.evolves_to
        return res

    def evolve(self) -> list:
        """Adopte la forme suivante (types, stats, capacités, sprite) et soigne de moitié."""
        old_known = set(self.known)
        self._adopt_form(self.form.evolves_to)
        self.hp = min(self.max_hp, self.hp + 0.5 * self.max_hp)
        return [(slot_of(m), spec_for(m)) for m in self.known if m not in old_known]     # apprises à l'évolution

    # --- bonus temporaires (Chant Flamboyant, Danse Aquatique...) ---
    def add_buff(self, stat: str, amount: float) -> None:
        b = self.buffs.setdefault(stat, [0, 0.0, amount])
        b[0], b[1] = min(self.BUFF_MAX, b[0] + 1), self.BUFF_TIME

    def tick_buffs(self, dt: float) -> None:
        for stat in list(self.buffs):
            self.buffs[stat][1] -= dt
            if self.buffs[stat][1] <= 0:
                del self.buffs[stat]

    def _buff_mult(self, stat: str) -> float:
        b = self.buffs.get(stat)
        return 1 + b[0] * b[2] if b else 1.0

    def stat(self, name: str) -> float:
        return getattr(self.stats, name) * self._buff_mult(name)

    @property
    def move_speed(self) -> float:
        return self.speed_mult * self._buff_mult("speed")

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
        self.obstacles: list = []        # rochers de la salle courante (fournis par le jeu)
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
        p.tick_buffs(dt)
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
        if p.lunge_left > 0:                                    # élan d'une attaque qui fonce
            p.pos += p.lunge_vec * dt
            p.lunge_left -= dt
        if p.dashing:
            p.pos += self._dash_dir * S.DASH_SPEED * dt
            p.trail.append((Vector2(p.pos), 1.0))
            self._dash_time -= dt
            if self._dash_time <= 0:
                p.dashing = False
        else:
            p.pos += move * S.PLAYER_SPEED * p.move_speed * dt

        if self.obstacles:
            resolve(p.pos, p.radius, self.obstacles)
        self._clamp(p)

        spawned = []
        if intent.attack in p.moveset and p.atk_cd[intent.attack] <= 0 and not p.dashing:
            if intent.aim is not None and (intent.aim - p.pos).length_squared() > 1:
                p.facing = (intent.aim - p.pos).normalize()
            spec = p.moveset[intent.attack]
            atk = spec.build(p, Vector2(p.facing))
            atk.slot = intent.attack
            p.act_anim, p.act_left = spec.anim, 0.35
            for stat, amount in spec.buffs:
                p.add_buff(stat, amount)
            if spec.lunge:                                   # Vive-Attaque, Aqua-Jet, Aquatacle : il fonce en avant
                p.lunge_left, p.lunge_vec = 0.12, Vector2(p.facing) * spec.lunge / 0.12
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
