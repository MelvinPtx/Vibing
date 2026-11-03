"""Tests headless : obstacles, navigation, boss. python -m tests.test_bosses"""
import random

import pygame
from pygame import Vector2

from src import settings as S
from src.combat import CombatSystem
from src.combat import moves as M
from src.entities import (Ectoplasma, Intent, Onix, Player, PlayerController, Racaillou, Rattata,
                          Zubat)
from src.game import Game
from src.geometry import circle_hits_rect, push_out, resolve
from src.levels import RoomManager, RoomState
from src.levels.obstacles import DOOR_ZONE, LAYOUTS, NavGrid, _keepouts, generate_layout
from src.starters import DEFAULT_STARTER

DT = 1 / 60
ROOM = pygame.Rect(60, 60, 904, 600)


def ready(boss):
    boss.spawn_left = 0
    return boss


def run(boss, player, secs, others=None):
    for _ in range(int(secs / DT)):
        boss.update(DT, player, others if others is not None else [boss], ROOM)


# --- collisions ---------------------------------------------------------------------
def test_push_out_and_circle_hits_rect():
    rect = pygame.Rect(100, 100, 50, 50)
    p = Vector2(95, 125)                                   # empiète de 15 px à gauche
    assert circle_hits_rect(p, 20, rect) and push_out(p, 20, rect)
    assert abs(p.x - 80) < 1e-9 and not circle_hits_rect(p, 20 - 0.01, rect)
    inside = Vector2(112, 125)                             # centre dans le rocher : sort par le bord le plus proche
    resolve(inside, 20, [rect])
    assert not circle_hits_rect(inside, 19.9, rect)
    assert not push_out(Vector2(0, 0), 10, rect)


def test_player_and_dash_blocked_by_rock():
    p = Player((100, 100))
    c = PlayerController(p, pygame.Rect(0, 0, 2000, 2000))
    c.obstacles = [pygame.Rect(150, 80, 60, 40)]
    for _ in range(60):
        c.update(Intent(move=Vector2(1, 0)), DT)
    assert p.pos.x <= 150 - p.radius + 0.01
    p.pos = Vector2(100, 100)
    for _ in range(30):
        c.update(Intent(move=Vector2(1, 0), dash=True), DT)
    assert p.pos.x <= 150 - p.radius + 0.01                # le dash ne traverse pas non plus


def test_projectiles_stop_on_rocks_but_zones_and_melee_do_not():
    owner = Player((0, 0))
    rock = [pygame.Rect(100, -20, 40, 40)]
    target = Rattata((300, 0)); target.spawn_left = 0
    cs = CombatSystem()
    cs.spawn(M.BALLE_OMBRE.build(owner, Vector2(1, 0)))
    for _ in range(60):
        cs.update(DT, [target], None, rock)
    assert not cs.attacks and target.hp == target.max_hp   # arrêté avant la cible
    cs.spawn(M.TRANCH_HERBE.build_at(owner, Vector2(120, 0)))   # zone posée sur le rocher
    cs.update(DT, [], None, rock)
    assert cs.attacks                                      # pas supprimée
    cs.spawn_hostile(M.ENEMY_BALLE_OMBRE.build(Rattata((0, 0)), Vector2(1, 0)))
    for _ in range(40):
        cs.update(DT, [], Player((500, 0)), rock)
    assert not cs.hostile                                  # le tir ennemi aussi s'écrase sur le rocher


# --- dispositions & navigation ---------------------------------------------------------
def test_layouts_are_valid_playable_and_keep_doors_and_start_clear():
    door, start = _keepouts(ROOM)
    for kind in LAYOUTS[1:]:
        made = 0
        for seed in range(40):
            rects = generate_layout(kind, ROOM, random.Random(seed))
            if not rects:
                continue
            made += 1
            for r in rects:
                assert ROOM.contains(r) and not r.colliderect(door) and not r.colliderect(start)
            assert NavGrid(ROOM, rects).all_free_reachable((ROOM.centerx, ROOM.bottom - 60))
        assert made >= 38, f"{kind}: trop d'échecs de génération ({made}/40)"
    assert door.h == DOOR_ZONE


def test_nav_finds_way_around_a_cup_and_ground_enemy_follows_it():
    cup = [pygame.Rect(400, 300, 200, 30), pygame.Rect(400, 200, 30, 130), pygame.Rect(570, 200, 30, 130)]
    nav = NavGrid(ROOM, cup)
    player = Player((500, 560))

    def trapped_chase(with_nav):
        e = Rattata((500, 250)); e.spawn_left = 0
        e.obstacles, e.nav = cup, (nav if with_nav else None)
        for i in range(480):
            if i % 12 == 0:
                nav.update_target(player.pos)
            e.update(DT, player, [e], ROOM)
        return e.pos.distance_to(player.pos)
    assert trapped_chase(True) < 60                        # contourne le gobelet et rejoint le joueur
    assert trapped_chase(False) > 150                      # sans navigation il reste coincé


def test_flying_enemy_ignores_rocks():
    wall = [pygame.Rect(60, 300, 904, 40)]
    z = Zubat((500, 200)); z.spawn_left = 0
    z.obstacles = wall
    p = Player((500, 560))
    crossed = False
    for _ in range(180):
        z.update(DT, p, [z], ROOM)
        crossed |= z.pos.y > 345
    assert crossed


def test_rooms_spawn_enemies_outside_rocks_and_keep_player_start_free():
    p = Player((500, 600))
    for seed in range(15):
        m = RoomManager(ROOM, p, random.Random(seed), start_number=2)
        for _ in range(4):
            m.start_room()
            if m.room_number % 5 == 0:
                continue
            assert all(not circle_hits_rect(e.pos, e.radius, o) for e in m.enemies for o in m.obstacles)
            assert all(not circle_hits_rect(p.pos, p.radius, o) for o in m.obstacles)
            assert all(e.obstacles is m.obstacles for e in m.enemies)


# --- boss ---------------------------------------------------------------------------
def test_boss_rooms_every_five_rooms_alternate_and_scale():
    p = Player((500, 600))
    for number, cls, level in ((5, Onix, 0), (10, Ectoplasma, 0), (15, Onix, 1), (20, Ectoplasma, 1)):
        m = RoomManager(ROOM, p, random.Random(3), start_number=number)
        assert m.enemies == [m.boss] and isinstance(m.boss, cls) and m.layout in ("pillars", "open")
        assert m.boss.level == level
        base = 1000 if cls is Onix else 760
        assert abs(m.boss.max_hp - base * (1 + 0.6 * level)) < 1e-9
    assert RoomManager(ROOM, p, random.Random(3), start_number=6).boss is None


def test_boss_intro_is_untouchable():
    b = Onix((500, 200))
    assert b.spawning and not b.vulnerable and b.take_damage(50) is False
    run(b, Player((500, 560)), 1.7)
    assert b.vulnerable and b.take_damage(50) is True


def test_quake_is_telegraphed_then_hits_only_in_range_and_dash_dodges():
    b, p = ready(Onix((500, 200), rng=random.Random(1))), Player((500, 560))
    b.atk_quake(p)
    assert len(b.telegraphs) == 1 and b.telegraphs[0].radius == M.SEISME.radius
    run(b, p, 0.9)
    assert not any(a.name == "Séisme" for a in b.out_attacks), "le coup part avant la fin de l'annonce"
    run(b, p, 0.2)
    quake = [a for a in b.out_attacks if a.name == "Séisme"]
    assert len(quake) == 1
    near, far, dodging = Player((500, 350)), Player((500, 600)), Player((500, 350))
    dodging.iframes_left = 1.0
    for who in (near, far, dodging):
        cs = CombatSystem()
        cs.spawn_hostile(M.SEISME.build_at(b, quake[0].pos))
        cs.update(DT, [], who)
    assert near.hp < near.max_hp and far.hp == far.max_hp and dodging.hp == dodging.max_hp


def test_charge_winds_up_then_dashes_then_rests():
    b, p = ready(Onix((500, 150), rng=random.Random(1))), Player((500, 560))
    b.atk_charge(p)
    assert b.state == "windup" and b.telegraphs[0].kind == "line"
    run(b, p, 0.5)
    assert b.vel.length() < 20                             # immobile pendant la préparation
    top = 0.0
    for _ in range(60):
        b.update(DT, p, [b], ROOM)
        top = max(top, b.vel.length())
    assert b.state == "charge" and top > 380
    run(b, p, 1.0)
    assert b.state == "idle"


def test_rockfall_marks_five_spots_then_drops_rocks():
    b, p = ready(Onix((500, 200), rng=random.Random(2))), Player((500, 500))
    b.atk_rockfall(p)
    assert len(b.telegraphs) == 5
    run(b, p, 1.0)
    assert not b.out_attacks
    run(b, p, 0.2)
    assert len([a for a in b.out_attacks if a.name == "Éboulement"]) == 5


def test_phases_trigger_at_thresholds_and_summon_minions():
    p = Player((500, 560))
    m = RoomManager(ROOM, p, random.Random(4), start_number=5)
    boss = m.boss
    for _ in range(int(1.7 / DT)):
        m.update(DT)
    boss.hp = boss.max_hp * 0.59
    m.update(DT)
    assert boss.phase == 2 and boss.events == ["Phase 2 !"]
    assert sum(isinstance(e, Racaillou) for e in m.enemies) == 2
    assert all(e.obstacles is m.obstacles for e in m.enemies)
    boss.hp = boss.max_hp * 0.29
    m.update(DT)
    assert boss.phase == 3 and sum(isinstance(e, Racaillou) for e in m.enemies) == 3


def test_ectoplasma_blink_hides_then_reappears_with_punch():
    b, p = ready(Ectoplasma((500, 200), rng=random.Random(5))), Player((500, 450))
    b.atk_blink(p)
    dest = Vector2(b.telegraphs[0].pos)                    # la destination est annoncée au sol
    run(b, p, 0.3)
    assert b.hidden and not b.vulnerable and b.sprite_visible is False
    run(b, p, 0.5)                                         # t = 0,8 s : réapparu à la destination
    assert not b.hidden and b.vulnerable and b.pos.distance_to(dest) < 15
    assert not [a for a in b.out_attacks if a.name == "Poing Ombre"]       # le coup arrive à 0,9 s
    run(b, p, 0.2)
    punch = [a for a in b.out_attacks if a.name == "Poing Ombre"]
    assert len(punch) == 1 and punch[0].pos.distance_to(dest) < 1e-9


def test_ectoplasma_ring_fires_ring_of_projectiles():
    b, p = ready(Ectoplasma((500, 200), rng=random.Random(5))), Player((500, 450))
    b.atk_ring(p)
    run(b, p, 0.9)
    shots = [a for a in b.out_attacks if a.name == "Ball'Ombre"]
    assert len(shots) == 10 and len({round(a.velocity.angle_to(Vector2(1, 0))) for a in shots}) == 10


def test_boss_death_cancels_pending_attacks_and_clears_room_once():
    p = Player((500, 560))
    m = RoomManager(ROOM, p, random.Random(6), start_number=5)
    boss = m.boss
    for _ in range(int(1.7 / DT)):
        m.update(DT)
    boss.atk_quake(p)
    boss.take_damage(1e9)
    for _ in range(90):
        m.update(DT)
    assert not [a for a in m.drain_attacks() if a.name == "Séisme"]    # l'attaque annoncée est annulée
    assert m.state is RoomState.CLEARED and len(m.doors) == 2
    assert m.consume_boss_clear() is True and m.consume_boss_clear() is False
    assert m.telegraphs == []


def test_game_boss_flow_banner_heal_and_render():
    g = Game(starter=DEFAULT_STARTER, room=5)
    assert g.banner and "Onix" in g.banner[0]
    for _ in range(110):
        g.update(Intent(), DT)
    g.room.boss.cd, g.room.boss.busy = 0, 0
    g.room.boss.atk_quake(g.player); g.room.boss.atk_charge(g.player)
    for _ in range(30):
        g.update(Intent(), DT)
    g.draw()                                               # zones de danger + barre de boss
    g.player.hp = 10
    g.room.boss.take_damage(1e9)
    g.update(Intent(), DT)
    assert g.player.hp >= 10 + g.player.max_hp / 2 - 1e-6
    for _ in range(int(S.DEATH_DURATION / DT) + 5):
        g.update(Intent(), DT)
    g.draw()
    e = Game(starter=DEFAULT_STARTER, room=10)
    for _ in range(110):
        e.update(Intent(), DT)
    e.room.boss.atk_blink(e.player)
    for _ in range(25):
        e.update(Intent(), DT)
        e.draw()                                           # boss caché : rien ne plante


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((10, 10))
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("OK ", n)
