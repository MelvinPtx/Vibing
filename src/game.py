import pygame
from pygame import Vector2

from . import settings as S
from .entities import Player, PlayerController
from .entities.player import Intent
from .ui import DebugHUD

MOVE_KEYS = {
    "left": (pygame.K_q, pygame.K_a, pygame.K_LEFT),
    "right": (pygame.K_d, pygame.K_RIGHT),
    "up": (pygame.K_z, pygame.K_w, pygame.K_UP),
    "down": (pygame.K_s, pygame.K_DOWN),
}
DASH_KEYS = (pygame.K_SPACE, pygame.K_LSHIFT, pygame.K_RSHIFT)


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
        self.running = True

    # --- Entrées -> Intent (seul endroit qui connaît le clavier) ---
    def read_intent(self, dash_event: bool) -> Intent:
        keys = pygame.key.get_pressed()
        down = lambda name: any(keys[k] for k in MOVE_KEYS[name])
        move = Vector2(down("right") - down("left"), down("down") - down("up"))
        return Intent(move=move, dash=dash_event)

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(S.FPS) / 1000.0
            dash_event = False
            for e in pygame.event.get():
                if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
                    self.running = False
                elif e.type == pygame.KEYDOWN and e.key in DASH_KEYS:
                    dash_event = True
                elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 3:
                    dash_event = True
            self.update(self.read_intent(dash_event), min(dt, 0.05))
            self.draw()
        pygame.quit()

    def update(self, intent: Intent, dt: float) -> None:
        self.controller.update(intent, dt)

    def draw(self) -> None:
        self.screen.fill(S.BG)
        pygame.draw.rect(self.screen, S.FLOOR, self.arena)
        pygame.draw.rect(self.screen, S.WALL, self.arena, 6)
        self.player.draw(self.screen)
        self.hud.draw(self.screen, self.player, self.clock.get_fps())
        pygame.display.flip()
