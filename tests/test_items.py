"""Tests headless : python -m tests.test_items"""
import random

from src.starters import DEFAULT_STARTER
import pygame
from pygame import Vector2

from src.combat import CombatSystem, PType
from src.entities import Entity, Intent, Player, PlayerController, Rattata, TrainingDummy
from src.items import apply_reward, roll_choices
from src.items.modifier import BaieOran, BaieSitrus, BandeauChoix, Charbon, LanceFlammes, Restes
from src.levels import RewardKind

DT = 1 / 60
ARENA = pygame.Rect(0, 0, 2000, 2000)


def setup():
    p = Player((500, 500))
    return p, PlayerController(p, ARENA)


def test_charbon_basic_becomes_fire_and_burns():
    p, c = setup()
    apply_reward(p, Charbon())
    t = Entity((540, 500), 20, (0, 0, 0), [PType.NORMAL], max_hp=1000)
    cs = CombatSystem()
    for a in c.update(Intent(attack="basic", aim=Vector2(900, 500)), DT):
        assert a.element is PType.FEU
        cs.spawn(a)
    cs.update(DT, [t])
    assert t.burn_left > 0 and t.hp == 1000 - 20          # Feu vs Normal : x1
    for _ in range(200):
        t.tick_status(DT)
    assert abs(t.hp - (980 - 18)) < 7, t.hp               # ~6 dps x 3 s


def test_charbon_only_basic_and_fire_types_immune_to_burn():
    p, c = setup()
    apply_reward(p, Charbon())
    special = c.update(Intent(attack="special"), DT)[0]
    assert special.element is PType.PLANTE
    fire = Entity((540, 500), 20, (0, 0, 0), [PType.FEU], max_hp=1000)
    c2 = CombatSystem()
    p2, ctl = setup()
    apply_reward(p2, Charbon())
    c2.spawn(ctl.update(Intent(attack="basic", aim=Vector2(900, 500)), DT)[0])
    c2.update(DT, [fire])
    assert fire.burn_left == 0


def test_burn_kills_enemy_and_stacking_rules():
    e = Rattata((0, 0)); e.spawn_left = 0
    e.apply_burn(3, 30)
    for _ in range(200):
        e.update(DT)
    assert not e.alive


def test_modifiers_and_instants():
    p, c = setup()
    apply_reward(p, BandeauChoix()); apply_reward(p, LanceFlammes())
    a = c.update(Intent(attack="special"), DT)[0]
    assert a.element is PType.FEU and abs(a.power - 35 * 1.3) < 1e-9
    p.hp = 50; apply_reward(p, Restes())
    for _ in range(60):
        c.update(Intent(), DT)
    assert 51 < p.hp < 52
    p.hp = 10; apply_reward(p, BaieOran()); assert p.hp == 40
    apply_reward(p, BaieSitrus()); assert p.max_hp == 120
    assert all(m.instant is False for m in p.modifiers)    # baies non stockées


def test_roll_choices_distinct_and_excludes_owned():
    p, _ = setup()
    rng = random.Random(3)
    for kind in RewardKind:
        ch = roll_choices(kind, p, rng)
        assert len(ch) == 3 and len({type(x) for x in ch}) == 3 and all(x.kind is kind for x in ch)
    apply_reward(p, Charbon())
    for s in range(20):
        assert all(not isinstance(x, Charbon) for x in roll_choices(RewardKind.OBJET, p, random.Random(s)))


def test_full_flow_door_menu_pick():
    from src.game import Game
    g = Game(starter=DEFAULT_STARTER)
    for _ in range(60):
        g.update(Intent(), DT)
    for e in g.room.enemies:
        e.take_damage(1e9)
    g.update(Intent(), DT)
    door = g.room.doors[0]
    g.player.pos = Vector2(door.rect.center)
    g.update(Intent(), DT)
    assert g.menu is not None and 1 <= len(g.menu.choices) <= 3
    assert all(m.kind is door.reward for m in g.menu.choices)
    before = Vector2(g.player.pos)
    g.update(Intent(move=Vector2(1, 0)), 0.5)               # menu ouvert : jeu en pause
    assert g.player.pos == before
    ev = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)
    chosen = g.menu.handle_event(ev)
    g.pick_reward(chosen)
    assert g.menu is None
    assert (chosen in g.player.modifiers) or chosen.instant


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("OK ", n)
