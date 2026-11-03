"""Tests headless des sprites : python -m tests.test_sprites"""
import tempfile
from pathlib import Path

import pygame
from pygame import Vector2

from src.entities import Intent
from src.game import Game
from src.species import ALL_DEX, NAMES
from src.ui.sprites import ASSET_DIR, SpriteRenderer, direction_index, load_sprite_set

ANIMDATA = """<AnimData><Anims>
<Anim><Name>Idle</Name><Index>0</Index><FrameWidth>4</FrameWidth><FrameHeight>4</FrameHeight>
<Durations><Duration>3</Duration><Duration>3</Duration></Durations></Anim>
<Anim><Name>Attack</Name><Index>1</Index><FrameWidth>4</FrameWidth><FrameHeight>4</FrameHeight>
<Durations><Duration>6</Duration><Duration>6</Duration><Duration>6</Duration></Durations></Anim>
<Anim><Name>Strike</Name><Index>2</Index><CopyOf>Attack</CopyOf></Anim>
</Anims></AnimData>"""


def fake_species(root: Path, dex=1):
    d = root / f"{dex:04d}"
    d.mkdir(parents=True)
    (d / "AnimData.xml").write_text(ANIMDATA)
    for name, cols in (("Idle", 2), ("Attack", 3)):
        sheet = pygame.Surface((cols * 4, 8 * 4), pygame.SRCALPHA)
        for row in range(8):                      # une couleur par direction, pour tester le découpage
            sheet.fill((row * 30, 10 * cols, 0, 255), (0, row * 4, cols * 4, 4))
        pygame.image.save(sheet, str(d / f"{name}-Anim.png"))


def test_direction_index():
    v = Vector2
    assert [direction_index(x) for x in (v(0, 1), v(1, 1), v(1, 0), v(1, -1),
                                         v(0, -1), v(-1, -1), v(-1, 0), v(-1, 1))] == list(range(8))
    assert direction_index(v()) == 0


def test_parse_slice_copyof_and_timing():
    with tempfile.TemporaryDirectory() as tmp:
        fake_species(Path(tmp))
        s = load_sprite_set(1, Path(tmp))
        assert set(s.anims) == {"Idle", "Attack", "Strike"}          # Strike = copie d'Attack
        idle = s.anims["Idle"]
        assert len(idle.frames) == 8 and len(idle.frames[0]) == 2
        assert idle.frames[5][0].get_at((0, 0))[0] == 150              # ligne 5 -> direction NO
        assert abs(idle.total - 6 / 60) < 1e-9
        assert idle.index_at(0.0, True) == 0 and idle.index_at(0.049, True) == 0   # 3 ticks = 0,05 s
        assert idle.index_at(0.051, True) == 1 and idle.index_at(0.11, True) == 0   # puis boucle
        att = s.anims["Attack"]
        assert att.index_at(99, False) == 2                            # une fois : reste sur la dernière image
        assert s.anim("Swing") is att                                  # repli Swing -> Attack
        assert s.anim("Hurt") is idle                                  # repli Hurt -> Idle


def test_missing_species_falls_back_to_circles():
    assert load_sprite_set(9999) is None
    r = SpriteRenderer(root=Path(tempfile.gettempdir()) / "no-sprites-here")
    g = Game()
    g.sprites = r
    for _ in range(5):
        g.update(Intent(), 1 / 60)
    g.draw()                                                           # cercles de secours, sans erreur
    assert r.draw(g.screen, g.player) is False


def test_renderer_restarts_one_shot_on_new_action():
    with tempfile.TemporaryDirectory() as tmp:
        fake_species(Path(tmp), 133)
        r = SpriteRenderer(root=Path(tmp), scale=1)
        g = Game(); g.sprites = r
        p = g.player
        p.act_anim, p.act_left = "Attack", 1.0
        p.act_nonce += 1
        r.draw(g.screen, p); r.update(0.5)
        t_before = r._state[p][1]
        p.act_nonce += 1                                                # 2e attaque : l'animation repart
        r.draw(g.screen, p)
        assert r._state[p][1] == 0 < t_before


def test_all_game_species_have_assets_and_credits():
    credits = (ASSET_DIR / "CREDITS.md").read_text(encoding="utf-8")
    r = SpriteRenderer()
    for dex in ALL_DEX:
        s = r.get(dex)
        assert s is not None, f"sprites manquants pour #{dex} {NAMES[dex]} (python -m tools.fetch_sprites)"
        assert "Idle" in s.anims and "Walk" in s.anims and "Attack" in s.anims
        assert f"#{dex:04d}" in credits, f"crédits manquants pour #{dex}"
    assert "CC BY-NC" in credits


def test_game_renders_with_sprites_in_every_state():
    g = Game()
    for _ in range(60):
        g.update(Intent(move=Vector2(1, 0)), 1 / 60)
    g.draw()
    g.update(Intent(dash=True, move=Vector2(0, -1)), 1 / 60); g.draw()    # dash : teinte + images rémanentes
    for slot in ("basic", "special", "cast"):
        g.player.atk_cd[slot] = 0
        g.update(Intent(attack=slot, aim=Vector2(600, 300)), 1 / 60); g.draw()
    g.player.take_damage(10); g.draw()                                    # Hurt + clignotement
    t = Game(training=True)
    for _ in range(10):
        t.update(Intent(attack="basic", aim=Vector2(200, 190)), 1 / 60)
    t.draw()


if __name__ == "__main__":
    pygame.init()
    pygame.display.set_mode((10, 10))
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f(); print("OK ", n)
