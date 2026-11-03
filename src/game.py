import pygame
from pygame import Vector2

from . import settings as S
from .combat import CombatSystem
from .entities import Intent, Player, PlayerController, TrainingDummy
from .combat.types import PType
from .ui.floating_text import FloatingTexts
from .ui import DebugHUD

MOVE_KEYS = {
    "left": (pygame.K_q, pygame.K_a, pygame.K_LEFT),
    "right": (pygame.K_d, pygame.K_RIGHT),
    "up": (pygame.K_z, pygame.K_w, pygame.K_UP),
    "down": (pygame.K_s, pygame.K_DOWN),
}
DASH_KEYS = (pygame.K_SPACE, pygame.K_LSHIFT, pygame.K_RSHIFT)
ATTACK_KEYS = {pygame.K_e: "special", pygame.K_r: "cast", pygame.K_j: "basic"}
DUMMY_TYPES = [(PType.NORMAL,), (PType.FEU,), (PType.EAU,), (PType.PLANTE,),
               (PType.SPECTRE,), (PType.INSECTE, PType.PLANTE)]


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((S.SCREEN_W, S.SCREEN_H))
        pygame.display.set_caption(S.TITLE)
        self.clock = pygame.time.Clock()
        self.arena = pygame.Rect(S.ARENA_MARGIN, S.ARENA_MARGIN,
                                 S.SCREEN_W - 2 * S.ARENA_MARGIN, S.SCREEN_H - 2 * S.ARENA_MARGIN)
        self.player = Player(self.arena.center)
        self.controller = PlayerController(self.player, self.arena)
        self.hud = DebugHUD()
        self.combat = CombatSystem()
        self.texts = FloatingTexts()
        n = len(DUMMY_TYPES)
        self.dummies = [TrainingDummy((self.arena.left + (i + 1) * self.arena.width / (n + 1),
                                       self.arena.top + 110), t) for i, t in enumerate(DUMMY_TYPES)]
        self.running = True

    # --- Entrées -> Intent (seul endroit qui connaît le clavier) ---
    def read_intent(self, dash_event: bool, attack=None) -> Intent:
        keys = pygame.key.get_pressed()
        down = lambda name: any(keys[k] for k in MOVE_KEYS[name])
        move = Vector2(down("right") - down("left"), down("down") - down("up"))
        return Intent(move=move, dash=dash_event, attack=attack,
                      aim=Vector2(pygame.mouse.get_pos()))

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(S.FPS) / 1000.0
            dash_event, attack = False, None
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    self.running = False
                elif e.type == pygame.KEYDOWN and e.key in DASH_KEYS:
                    dash_event = True
                elif e.type == pygame.KEYDOWN and e.key in ATTACK_KEYS:
                    attack = ATTACK_KEYS[e.key]
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                    dash_event = True
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
                    attack = "basic"
            self.update(self.read_intent(dash_event, attack), min(dt, 0.05))
            self.draw()
        pygame.quit()

    def update(self, intent: Intent, dt: float) -> None:
        for atk in self.controller.update(intent, dt):
            self.combat.spawn(atk)
        for d in self.dummies:
            d.update(dt)
        self.combat.update(dt, self.dummies)
        for target, res, atk in self.combat.events:
            color = S.RED if res.multiplier > 1 else (S.GREY if res.multiplier < 1 else S.WHITE)
            self.texts.add(target.pos - Vector2(0, 50), f"{res.amount:.0f}", color)
            if res.label:
                self.texts.add(target.pos - Vector2(0, 70), res.label, color)
        self.texts.update(dt)

    def draw(self) -> None:
        self.screen.fill(S.BG)
        pygame.draw.rect(self.screen, S.FLOOR, self.arena)
        pygame.draw.rect(self.screen, S.WALL, self.arena, 6)
        for d in self.dummies:
            d.draw(self.screen)
        for a in self.combat.attacks:
            pygame.draw.circle(self.screen, (255, 255, 255), a.pos, a.radius, 2)
        self.player.draw(self.screen)
        self.texts.draw(self.screen)
        self.hud.draw(self.screen, self.player, self.clock.get_fps())
        pygame.display.flip()
