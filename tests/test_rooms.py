"""Tests headless : python -m tests.test_rooms"""
import random

import pygame
from pygame import Vector2

from src import settings as S
from src.entities import Player, Rattata
from src.levels import RoomManager, RoomState

DT = 1 / 60
ARENA = pygame.Rect(60, 60, 904, 600)


def make(seed=1):
    p = Player((500, 600))
    return p, RoomManager(ARENA, p, random.Random(seed))


def run(room, secs):
    for _ in range(int(secs / DT)):
        room.update(DT)


def test_steering_chases_and_separates():
    p = Player((800, 400))
    a, b = Rattata((100, 400)), Rattata((100, 405))
    a.spawn_left = b.spawn_left = 0
    d0 = a.pos.distance_to(p.pos)
    for _ in range(60):
        for e in (a, b):
            e.update(DT, p, [a, b], ARENA)
    assert a.pos.distance_to(p.pos) < d0 - 100          # se rapproche
    assert a.pos.distance_to(b.pos) > 20                # ne se superposent pas


def test_spawn_delay_harmless_and_untargetable():
    p, room = make()
    assert room.targets == [] and all(e.spawning for e in room.enemies)
    assert room.enemies[0].take_damage(50) is False
    run(room, S.SPAWN_DELAY + 0.05)
    assert len(room.targets) == len(room.enemies)


def test_exits_locked_then_two_distinct_doors():
    p, room = make()
    assert room.exits_locked and room.doors == []
    run(room, S.SPAWN_DELAY + 0.05)
    for e in room.enemies[:-1]:
        e.take_damage(1e6)
    room.update(DT)
    assert room.exits_locked and not room.doors          # un ennemi vivant : toujours fermé
    room.enemies[-1].take_damage(1e6)
    room.update(DT)
    assert room.state is RoomState.CLEARED and not room.exits_locked
    assert len(room.doors) == 2 and room.doors[0].reward != room.doors[1].reward


def test_door_leads_to_next_room_with_reward():
    p, room = make()
    run(room, S.SPAWN_DELAY + 0.05)
    for e in room.enemies:
        e.take_damage(1e6)
    room.update(DT)
    door = room.doors[1]
    p.pos = Vector2(door.rect.center)
    assert room.update(DT) == door.reward
    assert room.room_number == 2 and room.exits_locked and len(room.enemies) == 4


def test_contact_damage_respects_iframes():
    p, room = make()
    run(room, S.SPAWN_DELAY + 0.05)
    e = room.enemies[0]
    e.pos = Vector2(p.pos)
    p.iframes_left = 1.0                                  # dash en cours
    room.update(DT)
    assert p.hp == p.max_hp
    p.iframes_left = 0
    room.update(DT)
    assert p.hp == p.max_hp - e.contact_damage


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("OK ", n)
