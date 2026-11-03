"""Test headless du dash : python -m tests.test_dash"""
import pygame
from pygame import Vector2

from src import settings as S
from src.entities import Player, PlayerController
from src.entities.player import Intent

DT = 1 / 60
arena = pygame.Rect(0, 0, 2000, 2000)


def make():
    p = Player((500, 500))
    return p, PlayerController(p, arena)


def test_walk():
    p, c = make()
    for _ in range(60):
        c.update(Intent(move=Vector2(1, 0)), DT)
    assert abs(p.pos.x - (500 + S.PLAYER_SPEED)) < 1, p.pos


def test_diagonal_not_faster():
    p, c = make()
    for _ in range(60):
        c.update(Intent(move=Vector2(1, 1)), DT)
    assert abs((p.pos - Vector2(500, 500)).length() - S.PLAYER_SPEED) < 1


def test_dash_iframes_and_cooldown():
    p, c = make()
    c.update(Intent(move=Vector2(0, -1), dash=True), DT)
    assert p.dashing and p.invincible and p.dash_cd_left > 0
    assert p.take_damage(10) is False and p.hp == p.max_hp
    # Dash retriggered during cooldown must be ignored
    y = p.pos.y
    t = 0.0
    while t < S.DASH_IFRAMES + DT:
        c.update(Intent(), DT); t += DT
    assert not p.invincible and not p.dashing
    assert y - p.pos.y > 100  # distance parcourue vers le haut
    c.update(Intent(dash=True), DT)
    assert not p.dashing, "dash pendant cooldown"
    assert p.take_damage(10) is True
    # après cooldown
    for _ in range(int(S.DASH_COOLDOWN / DT) + 2):
        c.update(Intent(), DT)
    c.update(Intent(dash=True), DT)
    assert p.dashing


def test_dash_distance_and_default_direction():
    p, c = make()
    x0 = p.pos.x
    c.update(Intent(dash=True), DT)  # pas d'input : direction = facing (droite)
    for _ in range(30):
        c.update(Intent(), DT)
    expected = S.DASH_SPEED * S.DASH_DURATION
    assert abs((p.pos.x - x0) - expected) < S.DASH_SPEED * DT, (p.pos.x - x0, expected)


def test_bounds():
    p = Player((50, 50))
    c = PlayerController(p, pygame.Rect(0, 0, 100, 100))
    for _ in range(30):
        c.update(Intent(move=Vector2(-1, -1), dash=True), DT)
    assert p.pos.x >= p.radius and p.pos.y >= p.radius


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn(); print("OK ", name)
