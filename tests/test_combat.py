"""Tests headless : python -m tests.test_combat"""
import pygame
from pygame import Vector2

from src.combat import CombatSystem, PType, effectiveness, TYPE_CHART
from src.combat.moves import balle_ombre, tranch_herbe, vive_attaque
from src.combat.damage import compute_damage
from src.entities import Entity, Intent, Player, PlayerController

P = PType


def test_chart_complete():
    assert len(TYPE_CHART) == 18 and all(len(r) == 18 for r in TYPE_CHART.values())


def test_multipliers():
    assert effectiveness(P.FEU, [P.PLANTE]) == 2
    assert effectiveness(P.FEU, [P.EAU]) == 0.5
    assert effectiveness(P.NORMAL, [P.SPECTRE]) == 0
    assert effectiveness(P.SPECTRE, [P.NORMAL]) == 0
    assert effectiveness(P.FEU, [P.INSECTE, P.PLANTE]) == 4
    assert effectiveness(P.ELECTRIK, [P.SOL, P.EAU]) == 0
    assert effectiveness(P.NORMAL, [P.NORMAL]) == 1


def dummy(types, pos=(100, 0)):
    return Entity(pos, 20, (0, 0, 0), types, max_hp=1000)


def test_damage_by_type():
    me = Entity((0, 0), 10, (0, 0, 0))
    d = Vector2(1, 0)
    cases = [(tranch_herbe, [P.EAU], 70), (tranch_herbe, [P.FEU], 17.5),
             (balle_ombre, [P.NORMAL], 0), (vive_attaque, [P.SPECTRE], 0),
             (vive_attaque, [P.NORMAL], 20), (tranch_herbe, [P.EAU, P.SOL], 140)]
    for mv, types, expected in cases:
        assert compute_damage(mv(me, d), dummy(types)).amount == expected, (mv.__name__, types)


def test_system_hits_once_and_projectile_dies():
    me = Player((0, 0))
    t = dummy([P.PSY], (150, 0))
    cs = CombatSystem()
    cs.spawn(balle_ombre(me, Vector2(1, 0)))
    for _ in range(60):
        cs.update(1 / 60, [t])
    assert t.hp == 1000 - 25 * 2 and not cs.attacks  # Spectre > Psy, un seul impact


def test_player_spawns_attack_with_cooldown():
    p = Player((300, 300))
    c = PlayerController(p, pygame.Rect(0, 0, 1000, 1000))
    out = c.update(Intent(attack="basic", aim=Vector2(500, 300)), 1 / 60)
    assert len(out) == 1 and p.facing.x > 0.99
    assert c.update(Intent(attack="basic"), 1 / 60) == []  # cooldown
    for _ in range(30):
        c.update(Intent(), 1 / 60)
    assert len(c.update(Intent(attack="basic"), 1 / 60)) == 1


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("OK ", n)
