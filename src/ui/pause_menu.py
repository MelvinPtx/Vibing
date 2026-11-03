"""Menu pause : « MAIN MENU » (équipe à gauche, commandes à droite) + écran de statut
(bandeau orange, étiquettes jaunes, pastilles de type, capacités)."""
import pygame
from pygame import Vector2

from .. import settings as S
from . import theme as T

ITEMS = [("Reprendre", "resume"), ("Statut", "status"), ("Quitter", "quit")]
MENU = pygame.Rect(S.SCREEN_W - 340, 112, 300, 268)
ROW_H = 54
MOVE_SLOTS = (("basic", "Clic G"), ("special", "E"), ("cast", "R"))


def move_infos(player):
    """Capacités telles qu'elles seront lancées (modificateurs inclus)."""
    out = []
    for slot, key in MOVE_SLOTS:
        a = player.moveset[slot].build(player, Vector2(1, 0))
        a.slot = slot
        for m in player.modifiers:
            m.on_attack(a, player)
        out.append((a.name, a.element, a.power, a.category.value, key))
    return out


def _icon(surface, kind: str, c, color) -> None:
    if kind == "resume":
        pygame.draw.polygon(surface, color, [(c[0] - 8, c[1] - 11), (c[0] + 11, c[1]), (c[0] - 8, c[1] + 11)])
    elif kind == "status":
        pygame.draw.circle(surface, color, c, 13, 3)
        T.text(surface, "i", 18, color, center=c)
    else:
        pygame.draw.line(surface, color, (c[0] - 9, c[1] - 9), (c[0] + 9, c[1] + 9), 4)
        pygame.draw.line(surface, color, (c[0] - 9, c[1] + 9), (c[0] + 9, c[1] - 9), 4)


class PauseMenu:
    """handle_event() renvoie "resume", "quit" ou None."""

    def __init__(self):
        self.index = 0
        self.screen = "main"
        self.rects = [pygame.Rect(MENU.x + 14, MENU.y + 62 + i * (ROW_H + 6), MENU.w - 28, ROW_H)
                      for i in range(len(ITEMS))]

    def handle_event(self, e):
        n = len(ITEMS)
        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                if self.screen == "status":
                    self.screen = "main"
                    return None
                return "resume"
            if self.screen == "status":
                return None
            if e.key in (pygame.K_UP, pygame.K_z, pygame.K_w):
                self.index = (self.index - 1) % n
            elif e.key in (pygame.K_DOWN, pygame.K_s):
                self.index = (self.index + 1) % n
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return self._activate(self.index)
        elif self.screen == "main" and e.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.rects):
                if r.collidepoint(e.pos):
                    self.index = i
        elif self.screen == "main" and e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.rects):
                if r.collidepoint(e.pos):
                    return self._activate(i)
        return None

    def _activate(self, i):
        action = ITEMS[i][1]
        if action == "status":
            self.screen = "status"
            return None
        return action

    # --- rendu ---------------------------------------------------------------
    def draw(self, surface, player, room_number: int = 0, sprites=None) -> None:
        surface.blit(T.blurred_backdrop(surface), (0, 0))
        if self.screen == "status":
            self._draw_status(surface, player, room_number, sprites)
        else:
            self._draw_main(surface, player, room_number, sprites)

    def _draw_main(self, surface, player, room_number, sprites=None) -> None:
        # Équipe (ligne jaune sélectionnée, comme le Pokémon de tête)
        r = pygame.Rect(34, 104, 360, 92)
        pygame.draw.rect(surface, T.YELLOW, r, border_radius=10)
        T.cursor(surface, 6, r.centery, 34)
        T.text(surface, player.name, 24, T.YELLOW_TXT, topleft=(r.x + 16, r.y + 8))
        T.hp_bar(surface, (r.x + 16, r.y + 44, 190, 30), player.hp / player.max_hp,
                 f"{player.hp:.0f}/{player.max_hp:.0f}")
        T.lv_pill(surface, f"Salle {room_number}" if room_number else "Entraînement",
                  topright=(r.right - 14, r.y + 10))
        c = (r.right - 62, r.centery + 12)
        if not (sprites and sprites.draw_icon(surface, player.species, (c[0], c[1] - 4), "Idle", 0, 3)):
            pygame.draw.circle(surface, T.YELLOW_TXT, c, 25)
            pygame.draw.circle(surface, player.color, c, 21)
            pygame.draw.line(surface, T.YELLOW_TXT, c, (c[0] + 25, c[1]), 3)

        # MAIN MENU
        T.alpha_rect(surface, MENU, T.NAVY, 190, 14)
        T.text(surface, "MENU", 22, T.WHITE, topleft=(MENU.x + 18, MENU.y + 16))
        T.divider(surface, MENU.x + 14, MENU.right - 14, MENU.y + 52, (150, 156, 180))
        for i, ((label, kind), rr) in enumerate(zip(ITEMS, self.rects)):
            fg = T.list_row(surface, rr, i == self.index)
            _icon(surface, kind, (rr.x + 30, rr.centery), fg)
            T.text(surface, label, 24, fg, midleft=(rr.x + 62, rr.centery))

        T.prompt_bar(surface, [("↑↓", "Choisir"), ("Entrée", "Valider"), ("Échap", "Reprendre")],
                     S.SCREEN_W - 20, S.SCREEN_H - 20)

    def _draw_status(self, surface, player, room_number, sprites=None) -> None:
        T.header(surface, "RÉSUMÉ DU POKÉMON", T.ORANGE, T.ORANGE_PAT, "i")
        # sous-barre « Résumé »
        T.alpha_rect(surface, (0, 62, S.SCREEN_W, 40), T.NAVY_DARK, 210, 0)
        pygame.draw.rect(surface, T.YELLOW, (22, 70, 5, 24), border_radius=2)
        T.text(surface, "Résumé", 20, T.WHITE, midleft=(40, 82))

        # portrait
        pr = pygame.Rect(40, 126, 300, 420)
        T.alpha_rect(surface, pr, T.NAVY, 190, 12)
        pygame.draw.rect(surface, (255, 255, 255), pr, 2, border_radius=12)
        c = (pr.centerx, pr.y + 170)
        if not (sprites and sprites.draw_icon(surface, player.species, c, "Idle", 0, 6)):
            pygame.draw.circle(surface, (255, 255, 255), c, 92)
            pygame.draw.circle(surface, player.color, c, 84)
            pygame.draw.line(surface, (255, 255, 255), c, (c[0] + 84, c[1]), 6)
        T.alpha_rect(surface, (pr.x, pr.bottom - 64, pr.w, 64), T.NAVY_DARK, 235, 12)
        T.text(surface, player.name, 24, T.WHITE, midleft=(pr.x + 18, pr.bottom - 32))
        T.lv_pill(surface, f"Niv. {player.level}", midright=(pr.right - 16, pr.bottom - 32))

        # fiche
        x, vx, y = 376, 556, 126
        T.text(surface, "Nom", 20, T.LABEL, topleft=(x, y))
        T.text(surface, player.name, 20, T.WHITE, topleft=(vx, y))
        T.text(surface, "Type", 20, T.LABEL, topleft=(x, y + 46))
        px = vx
        for t in player.types:
            px = T.type_pill(surface, t, 28, topleft=(px, y + 42)).right + 8
        T.text(surface, "PV", 20, T.LABEL, topleft=(x, y + 94))
        T.hp_bar(surface, (vx, y + 90, 300, 30), player.hp / player.max_hp,
                 f"{player.hp:.0f}/{player.max_hp:.0f}")

        T.text(surface, "Niveau", 20, T.LABEL, topleft=(x, y + 140))
        T.text(surface, f"{player.level}", 20, T.WHITE, topleft=(vx, y + 140))
        T.thin_bar(surface, (vx + 56, y + 148, 240, 10), player.xp_into_level / max(1, player.xp_span), T.CYAN)
        T.text(surface, f"{player.xp_into_level}/{player.xp_span} EXP", 13, T.GREY, False, topleft=(vx + 306, y + 143))

        T.text(surface, "Capacités", 20, T.LABEL, topleft=(x, y + 186))
        for i, (name, ptype, power, cat, key) in enumerate(move_infos(player)):
            rr = pygame.Rect(vx, y + 178 + i * 54, 424, 48)
            T.alpha_rect(surface, rr, T.NAVY_ROW, 200, 9)
            T.draw_type_icon(surface, ptype, (rr.x + 24, rr.centery), 34)
            T.text(surface, name, 19, T.WHITE, topleft=(rr.x + 52, rr.y + 5))
            T.text(surface, f"[{key}]  {cat} · puissance {power:.0f}", 13, T.GREY, False,
                   topleft=(rr.x + 52, rr.y + 28))
            T.type_pill(surface, ptype, 24, midright=(rr.right - 12, rr.centery))

        form = player.form
        T.text(surface, "Objets", 20, T.LABEL, topleft=(x, y + 346))
        if player.modifiers:
            px, py = vx, y + 342
            for m in player.modifiers:
                rect = T.pill(surface, m.name, 16, T.KIND_COLORS[m.kind.name], T.WHITE,
                              pad=(14, 6), topleft=(px, py))
                px = rect.right + 8
        else:
            T.text(surface, "Aucun", 20, T.GREY, False, topleft=(vx, y + 346))
        T.text(surface, "Évolution", 20, T.LABEL, topleft=(x, y + 392))
        if form.evolves_to:
            T.text(surface, f"{form.evolves_to.name} au niveau {form.evolve_level}", 20, T.WHITE, topleft=(vx, y + 392))
        else:
            T.text(surface, "Forme finale", 20, T.GREY, False, topleft=(vx, y + 392))
        nxt = form.next_unlock(player.level)
        T.text(surface, "Prochaine", 20, T.LABEL, topleft=(x, y + 432))
        T.text(surface, f"{nxt[1].name} au niveau {nxt[0]}" if nxt else "—", 20, T.WHITE if nxt else T.GREY,
               topleft=(vx, y + 432))

        T.footer(surface, [("Échap", "Retour")], T.ORANGE, T.ORANGE_PAT)
