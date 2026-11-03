"""Tests headless : starters, ennemis, mort, icônes de type. python -m tests.test_content"""
import random

import pygame
from pygame import Vector2

from src import settings as S
from src.combat import CombatSystem, PType
from src.combat import moves as M
from src.combat.damage import compute_damage
from src.entities import (Entity, Fantominus, Intent, Player, PlayerController, Racaillou,
                          Rattata, TrainingDummy, Voltorbe, Zubat)
from src.game import Game
from src.levels import RoomManager, RoomState
from src.starters import DEFAULT_STARTER, FUECOCO, QUAXLY, SPRIGATITO, STARTERS
from src.ui import theme as T
from src.ui.effects import Effects
from src.ui.sprites import SpriteRenderer
from src.ui.starter_select import StarterSelect

DT = 1 / 60
ARENA = pygame.Rect(0, 0, 2000, 2000)
ROOM = pygame.Rect(60, 60, 904, 600)


def ready(enemy):
    enemy.spawn_left = 0
    return enemy


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


# --- starters -----------------------------------------------------------------
def test_starters_types_stats_and_moves():
    assert [s.types for s in STARTERS] == [(PType.PLANTE,), (PType.FEU,), (PType.EAU,)]
    p = Player((500, 500), FUECOCO)
    assert (p.name, p.species, p.max_hp, p.hp) == ("Fuecoco", 909, 125, 125) and p.stats.spa == 1.1
    atk = PlayerController(p, ARENA).update(Intent(attack="special"), DT)[0]
    assert atk.element is PType.FEU and atk.name == "Lance-Flammes"
    q, c = Player((500, 500), QUAXLY), None
    c = PlayerController(q, ARENA)
    for _ in range(60):
        c.update(Intent(move=Vector2(1, 0)), DT)
    assert abs(q.pos.x - (500 + S.PLAYER_SPEED * 1.08)) < 1


def test_every_starter_has_three_distinct_slots():
    for s in STARTERS:
        assert set(s.moves) == {"basic", "special", "cast"}
        assert s.moves["basic"].kind == "melee" and s.moves["special"].kind == "burst"
        assert s.moves["cast"].kind == "projectile"
    assert len({s.moves["special"].element for s in STARTERS}) == 3


def test_stab_boosts_own_type_moves_only():
    me = Player((0, 0), FUECOCO)
    target = Entity((50, 0), 20, (0, 0, 0), [PType.NORMAL], max_hp=1000)
    stab = compute_damage(M.LANCE_FLAMMES.build(me, Vector2(1, 0)), target).amount
    flat = compute_damage(M.MORSURE.build(me, Vector2(1, 0)), target).amount
    assert abs(stab - 38 * 1.1 * 1.5) < 1e-9 and abs(flat - 24) < 1e-9


def test_starter_select_navigation_and_choice():
    s = StarterSelect()
    s.handle_event(key(pygame.K_DOWN)); assert s.index == 1
    assert s.handle_event(key(pygame.K_RETURN)) is FUECOCO
    assert s.handle_event(key(pygame.K_3)) is QUAXLY
    click = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=s.rects[0].center)
    assert s.handle_event(click) is SPRIGATITO


def test_game_starts_on_select_screen_and_blocks_updates():
    g = Game()
    assert g.select is not None
    pos = Vector2(g.player.pos)
    g.update(Intent(move=Vector2(1, 0)), 0.5)
    assert g.player.pos == pos
    g.draw()
    g.handle_event(key(pygame.K_2))
    assert g.select is None and g.player.name == "Fuecoco"


# --- ennemis ----------------------------------------------------------------------
def test_zubat_zigzags():
    z, p = ready(Zubat((100, 400))), Player((900, 400))
    path, last = 0.0, Vector2(z.pos)
    for _ in range(90):
        z.update(DT, p, [z], ROOM)
        path += z.pos.distance_to(last); last = Vector2(z.pos)
    assert path / z.pos.distance_to(Vector2(100, 400)) > 1.08, "trajectoire trop droite"


def test_racaillou_winds_up_then_charges():
    r, p = ready(Racaillou((300, 400))), Player((500, 400))
    r.state, r.state_t = "walk", 0.0
    top = 0.0
    for i in range(80):
        r.update(DT, p, [r], ROOM)
        top = max(top, r.vel.length())
        if i == 25:
            assert r.state == "windup" and r.vel.length() < 30       # à l'arrêt pendant la préparation
    assert top > 300, top                                            # puis charge rapide


def test_fantominus_backs_off_and_shoots():
    g, p = ready(Fantominus((500, 400))), Player((600, 400))
    g.shoot_t = 0.0
    for _ in range(45):
        g.update(DT, p, [g], ROOM)
    assert g.pos.distance_to(p.pos) > 100                           # recule
    shots = g.out_attacks
    assert shots and shots[0].element is PType.SPECTRE and shots[0].velocity.x > 0


def test_voltorbe_explodes_after_fuse():
    v, p = ready(Voltorbe((500, 400))), Player((550, 400))
    for _ in range(70):
        v.update(DT, p, [v], ROOM)
    assert not v.alive and v.death_t is not None
    assert any(a.name == "Explosion" for a in v.out_attacks)


def test_voltorbe_killed_before_fuse_does_not_explode():
    v, p = ready(Voltorbe((500, 400))), Player((550, 400))
    for _ in range(10):
        v.update(DT, p, [v], ROOM)
    assert v.fuse is not None
    v.take_damage(1e9)
    for _ in range(80):
        v.update(DT, p, [v], ROOM)
    assert not v.out_attacks


def test_hostile_projectile_typed_damage_and_dash_dodge():
    owner = ready(Fantominus((0, 0)))
    p = Player((100, 0))                                             # Plante
    cs = CombatSystem()
    cs.spawn_hostile(M.ENEMY_BALLE_OMBRE.build(owner, Vector2(1, 0)))
    hits = []
    for _ in range(40):
        cs.update(DT, [], p)
        hits += cs.hurt_events
    assert len(hits) == 1 and abs(p.hp - (p.max_hp - 14 * 1.5)) < 1e-9   # Spectre STAB, x1 sur Plante
    assert not cs.hostile                                            # projectile consommé

    p2 = Player((100, 0)); p2.iframes_left = 5.0                     # en plein dash
    cs.spawn_hostile(M.ENEMY_BALLE_OMBRE.build(owner, Vector2(1, 0)))
    for _ in range(40):
        cs.update(DT, [], p2)
    assert p2.hp == p2.max_hp and cs.hostile                         # traversé, pas consommé
    assert all(id(p2) not in a.hit for a in cs.hostile)


def test_room_composition_follows_room_number():
    m = RoomManager(ROOM, Player((500, 600)), random.Random(7))
    assert {type(e) for e in m.enemies} == {Rattata}
    seen = set()
    for _ in range(40):
        m.room_number = 5            # -> salle 6 (la 5 est une salle de boss)
        m.start_room()
        seen |= {type(e) for e in m.enemies}
    assert seen == {Rattata, Zubat, Racaillou, Fantominus, Voltorbe}
    for _ in range(20):
        m.room_number = 1
        m.start_room()
        assert {type(e) for e in m.enemies} <= {Rattata, Zubat}


# --- mort -------------------------------------------------------------------------
def test_dead_enemies_linger_then_vanish_and_doors_open_at_once():
    p = Player((500, 600))
    m = RoomManager(ROOM, p, random.Random(1))
    for _ in range(int((S.SPAWN_DELAY + 0.1) / DT)):
        m.update(DT)
    for e in m.enemies:
        e.take_damage(1e9)
    m.update(DT)
    assert m.state is RoomState.CLEARED and len(m.doors) == 2        # portes tout de suite
    assert m.enemies and all(e.dying for e in m.enemies)             # corps encore là
    assert m.alive_count == 0
    for _ in range(int((S.DEATH_DURATION + 0.2) / DT)):
        m.update(DT)
    assert m.enemies == []


def test_dying_sprites_render_with_and_without_faint():
    g = Game(starter=DEFAULT_STARTER)
    r = SpriteRenderer()
    with_faint = TrainingDummy((300, 300), (PType.PLANTE,), 906, "Sprigatito")
    assert "Faint" in r.get(906).anims
    without = ready(Zubat((400, 300)))
    assert "Faint" not in r.get(41).anims
    for ent in (with_faint, without):
        ent.take_damage(1e9)
        for t in (0.0, 0.05, 0.3, 0.6, S.DEATH_DURATION - 0.01):
            ent.death_t = t
            assert ent.dying and r.draw(g.screen, ent) is True
        ent.death_t = S.DEATH_DURATION + 0.01
        assert not ent.dying


def test_death_fx_and_dummy_respawn():
    g = Game(training=True, starter=DEFAULT_STARTER)
    d = g.dummies[0]
    d.take_damage(1e9)
    g.update(Intent(), DT)
    assert g.effects.active and not d.death_fresh and d.dying
    for _ in range(int(2.0 / DT)):
        g.update(Intent(), DT)
    assert d.alive and d.death_t is None and not g.effects.active


def test_effects_expire():
    fx = Effects()
    fx.burst(Vector2(100, 100), (255, 0, 0))
    assert fx.active
    for _ in range(80):
        fx.update(DT)
    assert not fx.active


# --- icônes de type --------------------------------------------------------------------
def test_type_icons_exist_for_all_18_types():
    pygame.init()
    pygame.display.set_mode((10, 10))
    assert len(list(PType)) == 18
    for t in PType:
        path = T.ICON_DIR / f"{t.name.lower()}.png"
        assert path.exists(), path
        img = pygame.image.load(str(path))
        assert img.get_size() == (128, 128)
        assert img.get_at((0, 0))[3] == 0 and img.get_at((64, 64))[3] == 255   # rond, transparent aux coins
        small = T.type_icon(t, 24)
        assert small is not None and small.get_size() == (24, 24)


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((10, 10))
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("OK ", n)
