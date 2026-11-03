"""Tests headless : niveaux, expérience, évolutions, capacités réelles. python -m tests.test_progression"""
import random
from pathlib import Path

import pygame
from pygame import Vector2

from src import progression as PR
from src.combat import CombatSystem, PType
from src.combat import moves as M
from src.data.pokedex import EVOLUTIONS, LEARNSET, MOVES, POKEMON
from src.entities import Entity, Intent, Player, PlayerController, Rattata
from src.game import Game
from src.levels import RoomManager
from src.starters import ALL_FORMS, FUECOCO, QUAXLY, SPRIGATITO, STARTERS, lineage
from src.ui.evolution import INTRO, MORPH, EvolutionScreen
from src.ui.sprites import SpriteRenderer

DT = 1 / 60
ARENA = pygame.Rect(0, 0, 2000, 2000)
ROOM = pygame.Rect(60, 60, 904, 600)


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


# --- courbes d'expérience ----------------------------------------------------------------
def test_experience_curves_match_the_games():
    at100 = {"fast": 800_000, "medium fast": 1_000_000, "medium slow": 1_059_860, "slow": 1_250_000,
             "erratic": 600_000, "fluctuating": 1_640_000}                 # totaux connus au niveau 100
    for rate, total in at100.items():
        assert PR.exp_for_level(rate, 100) == total, rate
    assert PR.exp_for_level("medium slow", 10) == 560
    for rate in at100:
        assert PR.level_from_exp(rate, PR.exp_for_level(rate, 37)) == 37
        assert PR.level_from_exp(rate, PR.exp_for_level(rate, 37) - 1) == 36


def test_xp_reward_and_scaling_formulas():
    assert PR.xp_reward(51, 5) == 36                   # Rattata niv. 5 : 51 x 5 / 7
    assert PR.enemy_level(1) == 5 and PR.enemy_level(5, boss=True) == 19
    assert PR.stat_mult(PR.START_LEVEL) == 1 and abs(PR.stat_mult(20) - 1.25) < 1e-9
    assert abs(PR.hp_mult(20) - 1.35) < 1e-9 and PR.enemy_hp_mult(1) == 1 and abs(PR.enemy_hp_mult(11) - 2.0) < 1e-9


# --- données et lignées --------------------------------------------------------------------
def test_evolution_lines_are_16_then_36_with_real_types():
    assert EVOLUTIONS == {906: (907, 16), 907: (908, 36), 909: (910, 16), 910: (911, 36), 912: (913, 16), 913: (914, 36)}
    expected = {"Sprigatito": ["Sprigatito", "Floragato", "Meowscarada"], "Fuecoco": ["Fuecoco", "Crocalor", "Skeledirge"],
                "Quaxly": ["Quaxly", "Quaxwell", "Quaquaval"]}
    for first in STARTERS:
        line = lineage(first)
        assert [f.name for f in line] == expected[first.name] and [f.stage for f in line] == [1, 2, 3]
        assert [f.evolve_level for f in line] == [16, 36, 0] and line[2].evolves_to is None
    assert [t.value for t in lineage(SPRIGATITO)[2].types] == ["Plante", "Ténèbres"]
    assert [t.value for t in lineage(FUECOCO)[2].types] == ["Feu", "Spectre"]
    assert [t.value for t in lineage(QUAXLY)[2].types] == ["Eau", "Combat"]


def test_stats_follow_real_base_stats_ratios_and_sprigatito_is_rebalanced():
    assert SPRIGATITO.atk == 1.10 and SPRIGATITO.spa == 1.00
    floragato, meow = lineage(SPRIGATITO)[1:]
    assert abs(meow.atk - 1.10 * 110 / 61) < 2e-3 and abs(floragato.max_hp - 100 * 61 / 40) < 0.1
    for first in STARTERS:
        a, b, c = lineage(first)
        assert a.max_hp < b.max_hp < c.max_hp and a.atk < b.atk < c.atk and a.speed_mult < c.speed_mult


def test_each_form_learns_exactly_its_real_learnset_with_database_numbers():
    for form in ALL_FORMS:
        real = LEARNSET[form.dex]
        assert set(real) <= set(M.MOVE_PLAN), f"{form.name} : capacité réelle sans plan {set(real) - set(M.MOVE_PLAN)}"
        assert form.learnset == real, form.name                         # toute la liste, aux niveaux réels
        for move_id, level in real.items():
            spec, db = M.spec_for(move_id), MOVES[move_id]
            assert spec.move_id == move_id and spec.name == db["name"] and spec.power == round(db["power"] * M.POWER_SCALE, 1)
            assert spec.element is M._TYPES[db["type"]] and spec.category.name == db["category"].upper()
            assert db["desc"], f"description manquante : {move_id}"
    assert set(LEARNSET[906]) == {"scratch", "leafage", "bite", "magical-leaf", "quick-attack", "seed-bomb", "u-turn",
                                  "slash", "energy-ball", "play-rough"}
    assert LEARNSET[908]["flower-trick"] == 0 and LEARNSET[911]["torch-song"] == 0 and LEARNSET[914]["aqua-step"] == 0


def test_signature_and_shared_moves_are_where_the_games_put_them():
    assert "bite" in LEARNSET[906] and "bite" in LEARNSET[909]              # la Morsure est bien partagée
    assert "flower-trick" not in LEARNSET[907] and "hex" in LEARNSET[911] and "hex" not in LEARNSET[910]
    assert "water-gun" in LEARNSET[912] and "surf" not in LEARNSET[912]     # Quaxly n'apprend pas Surf


def test_known_moves_grow_with_level_and_are_relearned_on_evolution():
    p = Player((0, 0), SPRIGATITO)                                          # niveau 10
    assert p.known == ["leafage", "scratch", "bite"]
    res = p.gain_xp(PR.exp_for_level(p.growth, 15) - p.xp)
    assert [m.name for _, m in res.new_moves] == ["Feuille Magik", "Vive-Attaque"] and "seed-bomb" not in p.known
    p.gain_xp(PR.exp_for_level(p.growth, 16) - p.xp)
    p.evolve()                                                             # Floragato : mêmes capacités, pas de Canon Graine avant le niveau 20
    assert p.known == ["leafage", "scratch", "bite", "magical-leaf", "quick-attack"]
    p.gain_xp(PR.exp_for_level(p.growth, 20) - p.xp)
    assert p.known[-1] == "seed-bomb" and p.moveset["cast"].name == "Canon Graine"


def test_equip_choice_persists_and_every_form_has_all_three_slots():
    p = Player((0, 0), SPRIGATITO)
    assert (p.moveset["basic"].name, p.moveset["special"].name, p.moveset["cast"].name) == ("Griffe", "Morsure", "Feuillage")
    p.gain_xp(PR.exp_for_level(p.growth, 15) - p.xp)
    assert p.moveset["cast"].name == "Feuille Magik" and p.moveset["basic"].name == "Vive-Attaque"   # dernière apprise
    assert p.equip("cast", "leafage") and p.moveset["cast"].name == "Feuillage"
    assert not p.equip("cast", "scratch") and not p.equip("cast", "seed-bomb")                       # mauvais emplacement / inconnue
    p.gain_xp(PR.exp_for_level(p.growth, 15) - p.xp + 1)
    assert p.moveset["cast"].name == "Feuillage"                                                     # le choix manuel reste
    for form in ALL_FORMS:
        level = {1: 10, 2: 16, 3: 36}[form.stage]
        q = Player((0, 0), form, level=level)
        assert set(q.moveset) == {"basic", "special", "cast"}, (form.name, q.moveset)
        assert all(q.known_for(slot) for slot in q.moveset)


def test_next_unlock_points_at_the_real_next_move():
    lv, spec = SPRIGATITO.next_unlock(10)
    assert (lv, spec.name) == (13, "Feuille Magik")
    assert lineage(QUAXLY)[1].next_unlock(36)[1].name == "Acrobatie" and lineage(QUAXLY)[2].next_unlock(64) is None


# --- joueur : niveau, évolution, bonus --------------------------------------------------------
def test_level_scaling_and_level_up_heal():
    p = Player((0, 0), SPRIGATITO)
    assert p.level == 10 and p.max_hp == 100 and abs(p.stat("atk") - 1.10) < 1e-9
    p.hp = 50
    p.gain_xp(PR.exp_for_level(p.growth, 20) - p.xp)
    assert p.level == 20 and abs(p.max_hp - 135) < 1e-9 and abs(p.stat("atk") - 1.10 * 1.25) < 1e-9
    assert p.hp > 50 + 0.15 * 100                                    # PV gagnés + petit soin
    assert p.xp_into_level == 0 and p.xp_span == PR.exp_for_level(p.growth, 21) - PR.exp_for_level(p.growth, 20)


def test_evolution_changes_form_types_moves_and_heals_half():
    p = Player((0, 0), FUECOCO)
    p.modifiers.append("objet")
    res = p.gain_xp(PR.exp_for_level(p.growth, 16) - p.xp)
    assert p.level == 16 and res.evolve_to.name == "Crocalor" and p.name == "Fuecoco"      # pas encore adoptée
    p.hp = 10
    p.evolve()
    assert (p.name, p.species, p.form.stage) == ("Crocalor", 910, 2) and p.modifiers == ["objet"]
    assert p.hp >= 10 + 0.5 * p.max_hp - 1e-6 and p.max_hp > 125
    assert p.moveset["cast"].name == "Flammèche" and "incinerate" in p.known        # apprise par Fuecoco au niveau 15
    assert p.moveset["special"].name == "Calcination" and "snarl" not in p.known    # Aboiement : niveau 24
    assert p.gain_xp(0).evolve_to is None                          # la forme 3 attend le niveau 36
    p.gain_xp(PR.exp_for_level(p.growth, 36) - p.xp)
    assert p.gain_xp(0).evolve_to.name == "Skeledirge"
    p.evolve()
    assert [t.value for t in p.types] == ["Feu", "Spectre"] and "torch-song" in p.known       # apprise à l'évolution


def test_buffs_stack_to_three_and_expire():
    skel = lineage(FUECOCO)[2]
    p = Player((500, 500), skel, level=36)
    assert p.equip("cast", "torch-song")
    c = PlayerController(p, ARENA)
    base = p.stat("spa")
    for _ in range(4):
        p.atk_cd["cast"] = 0
        c.update(Intent(attack="cast"), DT)
    assert p.buffs["spa"][0] == 3 and abs(p.stat("spa") - base * 1.36) < 1e-9     # 3 x 12 %
    for _ in range(int(8.2 / DT)):
        c.update(Intent(), DT)
    assert not p.buffs and abs(p.stat("spa") - base) < 1e-9
    q = Player((500, 500), lineage(QUAXLY)[2], level=36)
    assert q.equip("special", "aqua-step")
    v0 = q.move_speed
    PlayerController(q, ARENA).update(Intent(attack="special"), DT)
    assert abs(q.move_speed - v0 * 1.10) < 1e-9                                    # Danse Aquatique : +10 % de vitesse


# --- nouvelles propriétés de capacités -----------------------------------------------------------
def make_target(pos):
    t = Rattata(pos)
    t.spawn_left = 0
    t.max_hp = t.hp = 1000
    return t


def test_homing_projectile_curves_to_a_target_off_axis_but_plain_one_misses():
    owner = Entity((0, 0), 10, (0, 0, 0))
    for move, expect_hit in (("magical-leaf", True), ("leafage", False)):
        t = make_target((300, 130))
        cs = CombatSystem()
        cs.spawn(M.from_db(move, "bolt").build(owner, Vector2(1, 0)))
        for _ in range(120):
            cs.update(DT, [t])
        assert (t.hp < t.max_hp) is expect_hit, move


def test_pierce_hits_every_enemy_in_line_plain_projectile_only_the_first():
    owner = Entity((0, 0), 10, (0, 0, 0))
    for pierce, hit_both in ((True, True), (False, False)):
        a, b = make_target((200, 0)), make_target((340, 0))
        cs = CombatSystem()
        cs.spawn(M.from_db("aqua-cutter", "bolt", pierce=pierce).build(owner, Vector2(1, 0)))
        for _ in range(60):
            cs.update(DT, [a, b])
        assert a.hp < a.max_hp and (b.hp < b.max_hp) is hit_both
    wall = pygame.Rect(100, -30, 30, 60)                              # un projectile perforant s'arrête quand même sur un rocher
    cs = CombatSystem()
    cs.spawn(M.from_db("aqua-cutter", "bolt", pierce=True).build(owner, Vector2(1, 0)))
    t = make_target((300, 0))
    for _ in range(60):
        cs.update(DT, [t], None, [wall])
    assert t.hp == t.max_hp


def test_burn_chance_crit_and_priority_cooldown():
    owner = Entity((0, 0), 10, (0, 0, 0))
    atk = M.from_db("ember", "bolt", burn=1.0).build(owner, Vector2(1, 0))
    normal, fire = Entity((5, 0), 10, (0, 0, 0), [PType.NORMAL]), Entity((5, 0), 10, (0, 0, 0), [PType.FEU])
    res = type("R", (), {"multiplier": 1.0})
    atk.on_hit[0](atk, normal, res); atk.on_hit[0](atk, fire, res)
    assert normal.burn_left > 0 and fire.burn_left == 0               # les types Feu sont immunisés
    crit = M.from_db("flower-trick", "bolt", crit=1.5)
    assert abs(crit.build(owner, Vector2(1, 0)).power - 70 * 0.45 * 1.5) < 1e-9 and crit.homing > 0
    assert M.from_db("quick-attack", "melee").cooldown < M.from_db("scratch", "melee").cooldown * 0.7
    assert M.from_db("fire-blast", "bolt").cooldown > M.from_db("flamethrower", "bolt").cooldown      # PP 5 : plus lent


# --- salles, expérience et évolution dans le jeu ---------------------------------------------------------
def test_enemies_get_level_and_room_scaling():
    p = Player((500, 600))
    m = RoomManager(ROOM, p, random.Random(2), start_number=11)       # (la 10 est un boss ; la 11 est normale)
    e = m.enemies[0]
    assert e.lv == PR.enemy_level(11) == 25
    base = {Rattata: 60}.get(type(e))
    if base:
        assert abs(e.max_hp - 60 * PR.enemy_hp_mult(11)) < 1e-9 and abs(e.contact_damage - 10 * PR.enemy_power_mult(11)) < 1e-9
    assert all(e.max_hp >= type(e)(Vector2()).max_hp * 1.99 for e in m.enemies)


def test_killing_enemies_gives_xp_and_triggers_evolution_flow():
    g = Game(starter=SPRIGATITO)
    for _ in range(70):
        g.update(Intent(), DT)
    p = g.player
    x0 = p.xp
    g.room.enemies[0].take_damage(1e9)
    g.update(Intent(), DT)
    assert abs(p.xp - x0 - PR.xp_reward(POKEMON[g.room.enemies[0].species]["base_exp"], 5)) < 1e-9
    p.xp = PR.exp_for_level(p.growth, 16) - 3                          # juste avant le niveau 16
    victim = next(e for e in g.room.enemies if e.alive)
    victim.take_damage(1e9)
    g.update(Intent(), DT)
    assert p.level == 16 and g.evolution is not None and p.name == "Sprigatito"
    pos = Vector2(p.pos)
    g.update(Intent(move=Vector2(1, 0)), 0.5)
    assert p.pos == pos, "le jeu est en pause pendant l'évolution"
    g.draw()
    assert g.handle_event(key(pygame.K_RETURN)) is None and g.evolution is not None      # pas avant la révélation
    g.evolution.t = INTRO + MORPH + 0.1
    g.draw()
    g.handle_event(key(pygame.K_RETURN))
    assert g.evolution is None and p.name == "Floragato" and p.species == 907
    g.update(Intent(move=Vector2(1, 0)), 0.1)
    assert p.pos != pos


def test_evolution_screen_events_and_drawing_with_and_without_sprites():
    pygame.init()
    screen = pygame.display.set_mode((1024, 720))
    s = EvolutionScreen(SPRIGATITO, lineage(SPRIGATITO)[1])
    assert not s.revealed and s.handle_event(key(pygame.K_RETURN)) is False
    for sprites in (SpriteRenderer(), SpriteRenderer(root=Path("/nonexistent"))):
        for t in (0.0, INTRO + 0.1, INTRO + MORPH * 0.5, INTRO + MORPH * 0.99, INTRO + MORPH + 0.2, INTRO + MORPH + 3):
            s.t = t
            screen.fill((30, 30, 50))
            s.draw(screen, sprites)
    s.t = INTRO + MORPH + 0.01
    assert s.revealed and s.handle_event(key(pygame.K_RETURN)) is True
    assert s.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(5, 5))) is True


def test_every_form_has_sprites_and_screens_render_for_each_form():
    r = SpriteRenderer()
    for form in ALL_FORMS:
        s = r.get(form.dex)
        assert s is not None and {"Idle", "Walk", "Attack"} <= set(s.anims), form.name
    g = Game(starter=SPRIGATITO)
    for form in ALL_FORMS:
        g.reset(form)
        g.player.gain_xp(0)
        g.draw()
        from src.ui.pause_menu import PauseMenu
        g.pause = PauseMenu(); g.pause.screen = "status"; g.draw(); g.pause = None
    g2 = Game()
    for i in range(3):
        g2.select.index = i
        g2.draw()


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((10, 10))
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("OK ", n)
