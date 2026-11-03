"""HUD en jeu : cadre du Pokémon (nom, « Lv. », jauge de PV chiffrée) façon écran de combat,
coins dorés, indications de touches, étiquettes de PV au-dessus des ennemis."""
import pygame

from .. import settings as S
from . import theme as T


class HUD:
    # --- éléments dans le monde (barres au-dessus des ennemis) ---------------------
    def draw_world(self, surface, entities, show_types: bool = False) -> None:
        for e in entities:
            if not e.alive or getattr(e, "spawning", False):
                continue
            bar = pygame.Rect(0, 0, 64, 12)
            bar.midbottom = (e.pos.x, e.pos.y - e.radius - 26)   # au-dessus du sprite
            T.hp_bar(surface, bar, e.hp / e.max_hp)
            T.text(surface, e.name, 14, T.WHITE, shadow=True, midbottom=(bar.centerx, bar.top - 2))
            if show_types and e.types:
                T.type_pills(surface, e.types, int(e.pos.x), int(e.pos.y + e.radius + 14), 18)

    # --- HUD ---------------------------------------------------------------------
    def draw(self, surface, player, fps: float, room_number: int = 0, enemies_left: int = 0,
             sprites=None) -> None:
        T.corner_brackets(surface)
        T.text(surface, f"{fps:.0f} FPS", 12, T.GREY, False, topleft=(80, 16))
        self._player_panel(surface, player, room_number, sprites)
        if room_number:
            self._room_panel(surface, player, room_number, enemies_left)
        m = player.moveset                       # les capacités dépendent du starter
        T.prompt_bar(surface, [("Clic G", m["basic"].name), ("E", m["special"].name),
                               ("R", m["cast"].name), ("Espace", "Dash"), ("Échap", "Menu")],
                     S.SCREEN_W - 28, S.SCREEN_H - 24, size=14, gap=12)

    def _player_panel(self, surface, p, room_number, sprites=None) -> None:
        r = pygame.Rect(24, S.SCREEN_H - 158, 292, 140)
        T.alpha_rect(surface, r, T.NAVY, 185, 14)
        T.lv_pill(surface, f"Salle {room_number}" if room_number else "Entraînement",
                  topleft=(r.x + 16, r.y + 12))
        nm = T.text(surface, p.name, 24, T.WHITE, shadow=True, topleft=(r.x + 16, r.y + 38))
        ix = nm.right + 14
        for t in p.types:                       # icônes de type du Pokémon
            T.draw_type_icon(surface, t, (ix + 12, nm.centery + 1), 24)
            ix += 28
        if sprites:   # icône du Pokémon, comme dans la liste d'équipe
            sprites.draw_icon(surface, p.species, (r.right - 52, r.y + 40), "Idle", 0, 3)
        T.hp_bar(surface, (r.x + 14, r.y + 70, r.w - 28, 26), p.hp / p.max_hp,
                 f"{p.hp:.0f}/{p.max_hp:.0f}")
        ready = 1 - p.dash_cd_left / S.DASH_COOLDOWN
        T.text(surface, "DASH", 12, T.LABEL, topleft=(r.x + 16, r.y + 104))
        T.thin_bar(surface, (r.x + 70, r.y + 107, r.w - 86, 8), ready, T.LIME if ready >= 1 else T.AMBER)
        T.text(surface, "I-FRAMES", 12, T.LABEL, topleft=(r.x + 16, r.y + 120))
        T.thin_bar(surface, (r.x + 94, r.y + 123, r.w - 110, 8),
                   p.iframes_left / S.DASH_IFRAMES, T.CYAN)

    def _room_panel(self, surface, p, room_number, enemies_left) -> None:
        r = pygame.Rect(S.SCREEN_W - 300, 20, 276, 46)
        T.alpha_rect(surface, r, T.NAVY, 185, 14)
        T.lv_pill(surface, f"Salle {room_number}", topleft=(r.x + 12, r.y + 10))
        status = (f"{enemies_left} ennemi{'s' if enemies_left > 1 else ''}"
                  if enemies_left else "Choisis une porte !")
        T.text(surface, status, 17, T.WHITE if enemies_left else T.YELLOW, midright=(r.right - 14, r.centery))
        for i, mod in enumerate(p.modifiers):   # objets possédés : lignes façon menu
            rr = pygame.Rect(r.x, r.bottom + 8 + i * 42, r.w, 36)
            T.alpha_rect(surface, rr, T.NAVY, 170, 9)
            sq = pygame.Rect(rr.x + 6, rr.y + 5, 26, 26)
            pygame.draw.rect(surface, T.KIND_COLORS[mod.kind.name], sq, border_radius=7)
            T.text(surface, mod.name, 16, T.WHITE, midleft=(sq.right + 10, rr.centery))
