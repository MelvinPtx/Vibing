"""Tests headless des animations d'attaque : python -m tests.test_fx"""
import random

import pygame
from pygame import Vector2

from src.combat import moves as M
from src.combat.attack import Category
from src.combat.moves import MoveSpec
from src.combat.types import PType
from src.entities import Intent, Player
from src.game import Game
from src.starters import DEFAULT_STARTER, FUECOCO, QUAXLY
from src.ui.attack_fx import DUR, STYLES, AttackFX

DT = 1 / 60


class Owner:
    def __init__(self, pos):
        self.pos = Vector2(pos)


def spec(kind, element=PType.FEU):
    return MoveSpec("t", element, Category.SPECIAL, 10, kind, 0, "Attack", 30, 0.12 if kind != "projectile" else 2.0,
                    speed=260 if kind == "projectile" else 0.0)


def test_every_type_has_a_style_with_a_known_shape():
    assert set(STYLES) == set(PType)
    for main, dark, light, name in STYLES.values():
        assert len(main) == len(dark) == len(light) == 3 and name


def test_attack_kind_comes_from_the_move_spec():
    o = Owner((0, 0))
    assert M.VIVE_ATTAQUE.build(o, Vector2(1, 0)).kind == "melee"
    assert M.TRANCH_HERBE.build(o, Vector2(1, 0)).kind == "burst"
    assert M.BALLE_OMBRE.build(o, Vector2(1, 0)).kind == "projectile"
    assert M.SEISME.build_at(o, (5, 5)).kind == "zone"
    assert {s.moves[slot].kind for s in (DEFAULT_STARTER, FUECOCO, QUAXLY) for slot in s.moves} == {"melee", "burst", "projectile"}


def test_melee_animation_outlives_the_short_hitbox():
    fx, o = AttackFX(), Owner((100, 100))
    atk = spec("melee").build(o, Vector2(1, 0))
    fx.spawn(atk)
    atk.update(1.0)                                    # la hitbox (0,12 s) est déjà finie
    assert not atk.active
    for _ in range(int(0.2 / DT)):
        fx.update(DT)
    assert len(fx.anims) == 1                          # ...mais la coupe est encore à l'écran
    for _ in range(int(0.2 / DT)):
        fx.update(DT)
    assert fx.anims == []                              # elle disparaît au bout de DUR["melee"]
    assert DUR["melee"] > 0.12 * 2


def test_projectile_has_trail_then_turns_into_impact():
    fx, o = AttackFX(), Owner((0, 0))
    atk = spec("projectile").build(o, Vector2(1, 0))
    fx.spawn(atk)
    for _ in range(20):
        atk.update(DT)
        fx.update(DT)
    anim = fx.anims[0]
    assert anim.kind == "projectile" and len(anim.trail) >= 5
    last = Vector2(anim.fixed)
    atk.kill()                                         # touché ou bloqué
    fx.update(DT)
    assert [a.kind for a in fx.anims] == ["impact"] and fx.anims[0].pos().distance_to(last) < 1e-6
    for _ in range(int(0.4 / DT)):
        fx.update(DT)
    assert fx.anims == []


def test_zone_stays_where_it_was_dropped_and_burst_follows_owner():
    fx, o = AttackFX(), Owner((100, 100))
    fx.spawn(M.SEISME.build_at(o, Vector2(300, 300)))
    fx.spawn(M.TRANCH_HERBE.build(o, Vector2(1, 0)))
    o.pos = Vector2(200, 100)
    zone, burst = fx.anims
    assert zone.pos() == Vector2(300, 300) and burst.pos() == Vector2(200, 100)
    assert zone.dur > burst.dur                        # la grande zone dure plus longtemps


def test_hostile_flag_and_explosion_uses_fire_style():
    fx, o = AttackFX(), Owner((0, 0))
    fx.spawn(M.ENEMY_BALLE_OMBRE.build(o, Vector2(1, 0)), hostile=True)
    fx.spawn(M.EXPLOSION.build(o, Vector2(0, 1)), hostile=True)
    assert all(a.hostile for a in fx.anims) and fx.anims[1].element is PType.FEU


def test_every_type_and_kind_actually_draws_something():
    pygame.init()
    screen = pygame.display.set_mode((400, 300))
    for element in PType:
        for kind in ("melee", "burst", "projectile"):
            fx, o = AttackFX(), Owner((150, 150))
            atk = spec(kind, element).build(o, Vector2(1, 0))
            fx.spawn(atk)
            for _ in range(8):
                atk.update(DT) if kind == "projectile" else None
                fx.update(DT)
            screen.fill((38, 42, 58))
            fx.draw(screen)
            changed = sum(screen.get_at((x, y))[:3] != (38, 42, 58) for x in range(0, 400, 4) for y in range(0, 300, 4))
            assert changed > 5, (element, kind)
        fx = AttackFX()
        fx.hit((200, 150), element, strong=True)
        fx.update(0.05)
        screen.fill((38, 42, 58)); fx.draw(screen)
        assert any(screen.get_at((x, 150))[:3] != (38, 42, 58) for x in range(150, 250))


def test_game_spawns_player_and_enemy_animations_and_clears_on_room_change():
    random.seed(2)
    g = Game(starter=QUAXLY)
    for _ in range(60):
        g.update(Intent(), DT)
    g.update(Intent(attack="cast", aim=Vector2(600, 300)), DT)
    assert any(a.kind == "projectile" and not a.hostile for a in g.fx.anims)
    g.draw()
    g2 = Game(starter=DEFAULT_STARTER, room=10)           # Ectoplasma : ses tirs sont des animations hostiles
    for _ in range(110):
        g2.update(Intent(), DT)
    g2.room.boss.cd = g2.room.boss.busy = 0
    g2.room.boss.atk_ring(g2.player)
    most = 0
    for _ in range(60):
        g2.update(Intent(), DT)
        g2.draw()
        most = max(most, sum(a.hostile and a.kind == "projectile" for a in g2.fx.anims))
    assert most >= 6
    g2.room.boss.take_damage(1e9)
    g2.update(Intent(), DT)
    g2.player.pos = Vector2(g2.room.doors[0].rect.center)
    g2.update(Intent(), DT)                                # porte franchie : menu de récompense
    assert g2.menu is not None and g2.fx.anims == []


def test_hits_make_impact_flashes_in_game():
    g = Game(training=True, starter=FUECOCO)
    d = g.dummies[0]
    g.player.pos = d.pos + Vector2(0, 90)
    g.update(Intent(attack="special"), DT)
    for _ in range(6):
        g.update(Intent(), DT)
    assert any(a.kind == "impact" for a in g.fx.anims)
    g.draw()


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((10, 10))
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("OK ", n)
