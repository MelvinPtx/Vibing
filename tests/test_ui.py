"""Tests headless des menus : python -m tests.test_ui"""
import random

import pygame
from pygame import Vector2

from src.entities import Intent
from src.game import Game
from src.items import apply_reward, roll_choices
from src.items.modifier import Charbon, Restes
from src.levels import RewardKind
from src.ui.pause_menu import PauseMenu, move_infos
from src.ui.reward_menu import RewardMenu

DT = 1 / 60


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


def test_reward_menu_navigation():
    g = Game()
    m = RewardMenu(roll_choices(RewardKind.OBJET, g.player, random.Random(1)))
    n = len(m.choices)
    assert n == 3 and m.index == 0
    m.handle_event(key(pygame.K_DOWN)); assert m.index == 1
    m.handle_event(key(pygame.K_UP)); m.handle_event(key(pygame.K_UP)); assert m.index == n - 1
    assert m.handle_event(key(pygame.K_RETURN)) is m.choices[n - 1]
    assert m.handle_event(key(pygame.K_2)) is m.choices[1]
    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=m.rects[0].center)
    assert m.handle_event(click) is m.choices[0]


def test_pause_flow_in_game():
    g = Game()
    assert g.handle_event(key(pygame.K_ESCAPE)) is None and g.pause is not None
    pos = Vector2(g.player.pos)
    g.update(Intent(move=Vector2(1, 0)), 0.5)
    assert g.player.pos == pos, "le jeu doit être en pause"
    g.handle_event(key(pygame.K_DOWN)); g.handle_event(key(pygame.K_RETURN))
    assert g.pause.screen == "status"
    g.handle_event(key(pygame.K_ESCAPE))                    # Échap : retour au menu principal
    assert g.pause is not None and g.pause.screen == "main"
    g.handle_event(key(pygame.K_ESCAPE))                    # Échap : reprendre
    assert g.pause is None and g.running
    g.handle_event(key(pygame.K_ESCAPE)); g.handle_event(key(pygame.K_DOWN))
    g.handle_event(key(pygame.K_DOWN)); g.handle_event(key(pygame.K_RETURN))  # Quitter
    assert g.running is False


def test_game_over_keys():
    g = Game()
    g.player.hp = 0
    g.handle_event(key(pygame.K_RETURN))
    assert g.player.hp == g.player.max_hp
    g.player.hp = 0
    g.handle_event(key(pygame.K_ESCAPE))
    assert g.running is False


def test_status_shows_modified_moves():
    g = Game()
    apply_reward(g.player, Charbon())
    names = {n: e.value for n, e, *_ in move_infos(g.player)}
    assert names["Vive-Attaque"] == "Feu" and names["Tranch'Herbe"] == "Plante"


def test_every_screen_renders():
    g = Game()
    apply_reward(g.player, Charbon()); apply_reward(g.player, Restes())
    for _ in range(70):
        g.update(Intent(), DT)
    g.draw()                                                  # HUD
    g.menu = RewardMenu(roll_choices(RewardKind.CAPSULE, g.player, random.Random(2)))
    g.draw(); g.menu = None
    g.pause = PauseMenu(); g.draw()
    g.pause.screen = "status"; g.draw(); g.pause = None
    g.player.hp = 0; g.draw()                                 # K.O.
    t = Game(training=True); t.draw()                         # mode entraînement


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("OK ", n)
