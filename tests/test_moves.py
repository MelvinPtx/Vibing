"""Tests headless : effets réels des capacités (descriptions officielles). python -m tests.test_moves"""
import random

import pygame
from pygame import Vector2

from src.combat import CombatSystem
from src.combat import moves as M
from src.combat.types import PType
from src.combat.damage import compute_damage
from src.data.pokedex import MOVES
from src.entities import Boss, Entity, Intent, Onix, Player, PlayerController, Rattata
from src.starters import FUECOCO, QUAXLY, SPRIGATITO, lineage

DT = 1 / 60
ARENA = pygame.Rect(0, 0, 2000, 2000)


def target(pos, hp=1000):
    t = Rattata(pos)
    t.spawn_left = 0
    t.max_hp = t.hp = hp
    return t


def hit_once(spec, owner, tgt, frames=20, direction=Vector2(1, 0)):
    cs = CombatSystem()
    cs.spawn(spec.build(owner, direction))
    for _ in range(frames):
        cs.update(DT, [tgt])
    return cs


def test_description_driven_effects_are_declared_in_the_plan():
    plan = M.MOVE_PLAN
    assert plan["quick-attack"][2]["lunge"] > 0 and plan["aqua-jet"][2]["lunge"] > 0     # « fonce si rapidement »
    assert M.spec_for("quick-attack").cooldown < M.spec_for("scratch").cooldown          # « frappe en priorité »
    assert plan["double-hit"][2]["hits"] == 2 and plan["u-turn"][2]["retreat"] > 0
    assert plan["bite"][2]["stun"] and plan["air-slash"][2]["stun"] and plan["lick"][2]["stun"]   # apeurer / paralyser
    assert plan["low-sweep"][2]["slow"] and plan["acrobatics"][2]["solo"] == 2.0
    assert plan["hex"][2]["status_bonus"] == 2.0 and plan["wave-crash"][2]["recoil"] > 0
    assert plan["torch-song"][2]["buffs"][0][1] > 0 and plan["overheat"][2]["buffs"][0][1] < 0      # augmente / baisse l'Atq. Spé.
    assert plan["leaf-storm"][2]["buffs"][0][1] < 0 and len(plan["close-combat"][2]["buffs"]) == 2  # Défense et Déf. Spé.
    assert M.spec_for("magical-leaf").homing > 0 and M.spec_for("flower-trick").homing > 0         # « n'échoue jamais »
    assert M.spec_for("flower-trick").crit == 1.5                                                  # « toujours un coup critique »
    assert M.spec_for("aqua-cutter").pierce and M.spec_for("aqua-cutter").crit_rate > 0            # taux de critiques élevé
    for m in ("ember", "flamethrower", "fire-blast"):
        assert M.spec_for(m).burn == 0.10                                                          # « peut aussi le brûler »


def test_double_hit_hits_twice_and_other_melee_once():
    o = Entity((0, 0), 10, (0, 0, 0))
    once, twice = target((50, 0)), target((50, 0))
    hit_once(M.spec_for("pound"), o, once)
    hit_once(M.spec_for("double-hit"), o, twice)
    assert abs((once.max_hp - once.hp) - M.spec_for("pound").power) < 1e-9                  # un coup
    assert abs((twice.max_hp - twice.hp) - 2 * M.spec_for("double-hit").power) < 1e-9       # « deux fois d'affilée »


def test_lunge_moves_the_user_forward_and_retreat_moves_it_back_after_a_hit():
    p = Player((500, 500), SPRIGATITO, level=15)
    p.equip("basic", "quick-attack")
    ctl = PlayerController(p, ARENA)
    ctl.update(Intent(attack="basic", aim=Vector2(900, 500)), DT)
    for _ in range(10):
        ctl.update(Intent(), DT)
    assert 45 < p.pos.x - 500 < 65                                  # ~55 px en avant
    q = Player((500, 500), lineage(SPRIGATITO)[1], level=24)
    q.equip("special", "u-turn")
    t = target((580, 500))
    cs = CombatSystem()
    for atk in PlayerController(q, ARENA).update(Intent(attack="special", aim=Vector2(900, 500)), DT):
        cs.spawn(atk)
    cs.update(DT, [t])
    assert t.hp < t.max_hp and q.pos.x < 500 - 80                   # a frappé puis est revenu en arrière


def test_stun_and_slow_halt_or_slow_the_enemy_but_not_bosses():
    o = Entity((0, 0), 10, (0, 0, 0))
    t = target((50, 0))
    hit_once(M.from_db("bite", "wide", stun=(1.0, 0.9)), o, t)
    assert t.stun_left > 0
    t.update(DT, Player((600, 0)), [t], pygame.Rect(0, -500, 2000, 1000))
    assert t.vel.length() < 1                                       # apeuré : ne bouge pas
    s = target((50, 0))
    hit_once(M.spec_for("low-sweep"), o, s)
    assert s.slow_left > 0 and s.speed_cap == s.speed * 0.5
    boss = Onix((50, 0))
    boss.spawn_left = 0
    hit_once(M.from_db("bite", "wide", stun=(1.0, 0.9)), o, boss)
    assert boss.stun_left == 0                                       # les boss résistent


def test_hex_hurts_more_a_burning_target_and_acrobatics_more_without_items():
    o = Entity((0, 0), 10, (0, 0, 0))
    plain, burning = target((50, 0)), target((50, 0))
    plain.types = burning.types = (PType.EAU,)                       # neutre face au type Spectre
    burning.apply_burn(3, 1)
    a = compute_damage(M.spec_for("hex").build(o, Vector2(1, 0)), plain).amount
    b = compute_damage(M.spec_for("hex").build(o, Vector2(1, 0)), burning).amount
    assert abs(b / a - 2.0) < 1e-9
    p = Player((0, 0), lineage(QUAXLY)[1], level=38)
    base = M.spec_for("acrobatics").power
    assert abs(M.spec_for("acrobatics").build(p, Vector2(1, 0)).power - base * 2) < 1e-9
    p.modifiers.append("objet")
    assert abs(M.spec_for("acrobatics").build(p, Vector2(1, 0)).power - base) < 1e-9


def test_recoil_hurts_the_user_but_never_kills_and_crit_rate_boosts_power():
    p = Player((0, 0), lineage(QUAXLY)[2], level=64)
    p.equip("special", "wave-crash")
    t = target((60, 0))
    cs = CombatSystem()
    for atk in PlayerController(p, ARENA).update(Intent(attack="special", aim=Vector2(900, 0)), DT):
        cs.spawn(atk)
    hp0 = p.hp
    for _ in range(15):
        cs.update(DT, [t])
    assert t.hp < t.max_hp and p.hp < hp0 and p.hp >= 1
    p.hp = 1.0
    cs.spawn(M.spec_for("wave-crash").build(p, Vector2(1, 0)))
    t2 = target((60, 0))
    cs.update(DT, [t2])
    assert p.hp >= 1.0
    o = Entity((0, 0), 10, (0, 0, 0))
    crit = M.from_db("slash", "wide", crit_rate=1.0).build(o, Vector2(1, 0))
    assert abs(crit.power - M.from_db("slash", "wide").power * 1.5) < 1e-9 and crit.crit_hit


def test_self_debuffs_lower_the_users_stat_and_recover():
    p = Player((500, 500), lineage(FUECOCO)[2], level=64)
    assert p.equip("cast", "overheat")
    base = p.stat("spa")
    ctl = PlayerController(p, ARENA)
    ctl.update(Intent(attack="cast"), DT)
    assert abs(p.stat("spa") - base * 0.8) < 1e-9                    # « baisse beaucoup l'Attaque Spéciale »
    for _ in range(int(8.2 / DT)):
        ctl.update(Intent(), DT)
    assert abs(p.stat("spa") - base) < 1e-9


def test_every_learnable_move_builds_and_has_a_description():
    owner = Player((0, 0))
    for move_id in M.MOVE_PLAN:
        spec = M.spec_for(move_id)
        atk = spec.build(owner, Vector2(1, 0))
        assert atk.move_id == move_id and atk.kind in ("melee", "burst", "projectile") and atk.power > 0
        assert len(MOVES[move_id]["desc"]) > 15


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((10, 10))
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("OK ", n)
