import pygame
from pygame import Vector2

from . import settings as S
from .combat import CombatSystem
from .entities import Intent, Player, PlayerController, TrainingDummy
from .items import apply_reward, roll_choices
from .levels import RoomManager
from .species import DUMMY_ROSTER
from .starters import DEFAULT_STARTER
from .ui import HUD
from .ui import theme as T
from .ui.effects import Effects
from .ui.floating_text import FloatingTexts
from .ui.pause_menu import PauseMenu
from .ui.reward_menu import RewardMenu
from .ui.room_view import RoomView
from .ui.starter_select import StarterSelect
from .ui.sprites import SpriteRenderer

MOVE_KEYS = {
    "left": (pygame.K_q, pygame.K_a, pygame.K_LEFT),
    "right": (pygame.K_d, pygame.K_RIGHT),
    "up": (pygame.K_z, pygame.K_w, pygame.K_UP),
    "down": (pygame.K_s, pygame.K_DOWN),
}
DASH_KEYS = (pygame.K_SPACE, pygame.K_LSHIFT, pygame.K_RSHIFT)
ATTACK_KEYS = {pygame.K_e: "special", pygame.K_r: "cast", pygame.K_j: "basic"}


class Game:
    def __init__(self, training: bool = False, starter=None, room: int = 1):
        """`starter` : démarre directement avec ce Pokémon ; sinon l'écran de choix s'affiche."""
        pygame.init()
        self.screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H))
        pygame.display.set_caption(S.TITLE)
        self.clock = pygame.time.Clock()
        self.arena = pygame.Rect(S.ARENA_MARGIN, S.ARENA_MARGIN,
                                 S.SCREEN_W - 2 * S.ARENA_MARGIN, S.SCREEN_H - 2 * S.ARENA_MARGIN)
        self.training = training
        self.first_room = room             # numéro de la première salle (--room N pour tester un boss)
        self.banner = None                 # [texte, sous-titre, secondes restantes]
        self.hud = HUD()
        self.view = RoomView()
        self.sprites = SpriteRenderer()
        self.texts = FloatingTexts()
        self.effects = Effects()
        self.running = True
        self.select = None if starter else StarterSelect()
        self.reset(starter or DEFAULT_STARTER)

    def reset(self, starter=DEFAULT_STARTER) -> None:
        """(Re)lance une partie avec ce starter."""
        self.player = Player(self.arena.center, starter)
        self.controller = PlayerController(self.player, self.arena)
        self.combat = CombatSystem()
        self.menu = None
        self.pause = None
        self.texts.items.clear()
        self.effects = Effects()
        if self.training:
            self.room = None
            n = len(DUMMY_ROSTER)
            self.dummies = [TrainingDummy((self.arena.left + (i + 1) * self.arena.width / (n + 1),
                                           self.arena.top + 130), types, dex, name)
                            for i, (name, dex, types) in enumerate(DUMMY_ROSTER)]
        else:
            self.dummies = []
            self.room = RoomManager(self.arena, self.player, start_number=self.first_room)
            self._announce_boss()

    def _announce_boss(self) -> None:
        boss = self.room.boss if self.room else None
        if boss is not None:
            self.banner = [f"{boss.name} sauvage !", "Boss — Phase 1", 2.4]

    @property
    def game_over(self) -> bool:
        return self.player.hp <= 0

    # --- Entrées -> Intent (seul endroit qui connaît le clavier) ---
    def read_intent(self, dash_event: bool, attack=None) -> Intent:
        keys = pygame.key.get_pressed()
        down = lambda name: any(keys[k] for k in MOVE_KEYS[name])
        move = Vector2(down("right") - down("left"), down("down") - down("up"))
        return Intent(move=move, dash=dash_event, attack=attack,
                      aim=Vector2(pygame.mouse.get_pos()))

    def handle_event(self, e) -> str | None:
        """Traite un événement pygame. Renvoie "dash" / "basic" / "special" / "cast" ou None."""
        if e.type == pygame.QUIT:
            self.running = False
        elif self.select:                                 # choix du starter : capte tout
            if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                self.running = False
                return None
            chosen = self.select.handle_event(e)
            if chosen:
                self.select = None
                self.reset(chosen)
        elif self.menu:                                   # menu de récompense : capte tout
            chosen = self.menu.handle_event(e)
            if chosen:
                self.pick_reward(chosen)
        elif self.pause:                                  # menu pause : capte tout
            res = self.pause.handle_event(e)
            if res == "resume":
                self.pause = None
            elif res == "quit":
                self.running = False
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
            if self.game_over:
                self.running = False
            else:
                self.pause = PauseMenu()
        elif e.type == pygame.KEYDOWN and e.key == pygame.K_RETURN and self.game_over:
            self.select = StarterSelect()                 # nouvelle partie : on rechoisit son starter
        elif e.type == pygame.KEYDOWN and e.key in DASH_KEYS:
            return "dash"
        elif e.type == pygame.KEYDOWN and e.key in ATTACK_KEYS:
            return ATTACK_KEYS[e.key]
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
            return "dash"
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            return "basic"
        return None

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(S.FPS) / 1000.0
            dash_event, attack = False, None
            for e in pygame.event.get():
                action = self.handle_event(e)
                if action == "dash":
                    dash_event = True
                elif action:
                    attack = action
            self.update(self.read_intent(dash_event, attack), min(dt, 0.05))
            self.draw()
        pygame.quit()

    def pick_reward(self, mod) -> None:
        apply_reward(self.player, mod)
        self.texts.add(self.player.pos - Vector2(0, 40), mod.name, S.YELLOW)
        self.menu = None

    def update(self, intent: Intent, dt: float) -> None:
        if self.select or self.game_over or self.menu or self.pause:
            return
        self.controller.obstacles = self.room.obstacles if self.room else []
        for atk in self.controller.update(intent, dt):
            self.combat.spawn(atk)
        if self.room:
            reward = self.room.update(dt)
            if reward:
                self.combat.clear()
                self.menu = RewardMenu(roll_choices(reward, self.player))
                self._announce_boss()
                return
            targets = self.room.targets
            for atk in self.room.drain_attacks():           # tirs et explosions ennemis
                self.combat.spawn_hostile(atk)
        else:
            for d in self.dummies:
                d.update(dt)
            targets = self.dummies
        self.combat.update(dt, targets, self.player, self.room.obstacles if self.room else ())
        boss = self.room.boss if self.room else None
        if boss is not None:
            for ev in boss.events:                          # « Phase 2 ! »
                self.texts.add(boss.pos - Vector2(0, boss.radius + 70), ev, T.YELLOW)
            boss.events.clear()
        if self.room and self.room.consume_boss_clear():    # boss vaincu : soin de moitié
            self.player.hp = min(self.player.max_hp, self.player.hp + self.player.max_hp / 2)
            self.texts.add(self.player.pos - Vector2(0, 60), "Boss vaincu ! PV restaurés", T.YELLOW)
        if self.banner:
            self.banner[2] -= dt
            if self.banner[2] <= 0:
                self.banner = None
        for target, res, atk in self.combat.events:
            color = S.RED if res.multiplier > 1 else (S.GREY if res.multiplier < 1 else S.WHITE)
            self.texts.add(target.pos - Vector2(0, 50), f"{res.amount:.0f}", color)
            if res.label:
                self.texts.add(target.pos - Vector2(0, 70), res.label, color)
        for target, res, atk in self.combat.hurt_events:    # le joueur est touché
            self.texts.add(target.pos - Vector2(0, 56), f"-{res.amount:.0f}" if res.amount else "0", T.RED)
            if res.label:
                self.texts.add(target.pos - Vector2(0, 78), res.label, T.YELLOW)
        for e in (self.room.enemies if self.room else self.dummies):   # mort : éclats + onde de choc
            if e.death_fresh:
                e.death_fresh = False
                color = T.TYPE_COLORS[e.types[0].name] if e.types else T.WHITE
                self.effects.burst(e.pos, color, 46 if getattr(e, "is_boss", False) else 14)
        self.effects.update(dt)
        self.texts.update(dt)
        self.sprites.update(dt)

    def draw(self) -> None:
        if self.select:
            self.select.draw(self.screen, self.sprites)
            pygame.display.flip()
            return
        self.screen.fill(S.BG)
        if self.room:
            self.view.draw(self.screen, self.room)
        else:
            pygame.draw.rect(self.screen, S.FLOOR, self.arena)
            pygame.draw.rect(self.screen, S.WALL, self.arena, 6)
        if self.room:
            self.view.draw_telegraphs(self.screen, self.room.telegraphs)
        entities = self.room.enemies if self.room else self.dummies
        for e in sorted([*entities, self.player], key=lambda e: e.pos.y):   # profondeur : le plus bas devant
            if self.sprites.draw(self.screen, e):
                e.draw_status(self.screen)
            else:
                e.draw(self.screen)             # pas de sprite : cercle de secours
        for a in self.combat.attacks:
            pygame.draw.circle(self.screen, (255, 255, 255), a.pos, a.radius, 2)
        for a in self.combat.hostile:                       # attaques ennemies : couleur du type
            col = T.TYPE_COLORS[a.element.name]
            pygame.draw.circle(self.screen, col, a.pos, a.radius, 0 if a.radius < 40 else 5)
            pygame.draw.circle(self.screen, (255, 255, 255), a.pos, a.radius, 2)
        self.effects.draw(self.screen)
        self.hud.draw_world(self.screen, entities, show_types=self.training)
        self.texts.draw(self.screen)
        room_number = self.room.room_number if self.room else 0
        if self.menu:
            self.menu.draw(self.screen)
        elif self.pause:
            self.pause.draw(self.screen, self.player, room_number, self.sprites)
        elif self.game_over:
            self.view.draw_game_over(self.screen, self.player, room_number)
        else:
            self.hud.draw(self.screen, self.player, self.clock.get_fps(), room_number,
                          self.room.alive_count if self.room else 0, self.sprites,
                          self.room.boss if self.room else None)
        if self.banner and not (self.menu or self.pause or self.game_over):
            self.view.draw_banner(self.screen, self.banner[0], self.banner[1],
                                  int(255 * min(1.0, self.banner[2] / 0.5)))
        pygame.display.flip()
