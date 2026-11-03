import pygame

from .. import settings as S
from . import theme as T


class DebugHUD:
    """HUD : dash (cooldown / i-frames), PV, salle, objets, aide des touches."""

    def draw(self, surface, player, fps: float, show_help: bool = True) -> None:
        # --- panneau Dash (haut gauche) ---
        box = T.panel(surface, (14, 12, 250, 70), T.PANEL, radius=18)
        ready = 1 - player.dash_cd_left / S.DASH_COOLDOWN
        T.text(surface, "DASH", 13, T.INK_SOFT, True, topleft=(box.x + 16, box.y + 10))
        label = "PRÊT" if ready >= 1 else f"{player.dash_cd_left:.1f}s"
        T.text(surface, label, 13, T.VIOLET if ready >= 1 else T.INK_SOFT, True,
               topright=(box.right - 16, box.y + 10))
        T.thin_bar(surface, (box.x + 16, box.y + 28, box.w - 32, 10), ready,
                   T.VIOLET if ready >= 1 else T.GOLD)
        T.text(surface, "I-FRAMES", 13, T.INK_SOFT, True, topleft=(box.x + 16, box.y + 44))
        T.thin_bar(surface, (box.x + 92, box.y + 49, box.w - 108, 8),
                   player.iframes_left / S.DASH_IFRAMES, T.SCARLET)

        if not show_help:
            return
        # --- aide des touches (bas gauche) ---
        lines = ["ZQSD / WASD / flèches : bouger", "Espace / Maj / clic droit : dash",
                 "Clic gauche : Vive-Attaque", "E : Tranch'Herbe   R : Ball'Ombre",
                 f"Échap : quitter   ·   {fps:.0f} FPS"]
        h = 18 * len(lines) + 16
        help_box = pygame.Rect(14, S.SCREEN_H - h - 10, 290, h)
        T.panel(surface, help_box, T.INK, radius=16, shadow=False, alpha=170)
        for i, t in enumerate(lines):
            T.text(surface, t, 13, T.PANEL, topleft=(help_box.x + 14, help_box.y + 9 + i * 18))

    def draw_run(self, surface, player, room_number: int, enemies_left: int) -> None:
        # --- panneau PV (haut droite), façon cadre de PV Pokémon ---
        box = T.panel(surface, (S.SCREEN_W - 314, 12, 300, 76), T.PANEL, radius=18)
        T.pill(surface, "PV", 13, T.SCARLET, T.PANEL, pad=(10, 2), topleft=(box.x + 16, box.y + 12))
        T.text(surface, f"{player.hp:.0f} / {player.max_hp:.0f}", 16, T.INK, True,
               topright=(box.right - 16, box.y + 10))
        T.hp_bar(surface, (box.x + 16, box.y + 36, box.w - 32, 14), player.hp / player.max_hp)
        status = (f"{enemies_left} ennemi{'s' if enemies_left > 1 else ''}"
                  if enemies_left else "Choisis une porte !")
        T.text(surface, f"Salle {room_number}", 14, T.INK_SOFT, True, topleft=(box.x + 16, box.y + 54))
        T.text(surface, status, 14, T.VIOLET if not enemies_left else T.INK, True,
               topright=(box.right - 16, box.y + 54))

        # --- objets possédés : pastilles sous le panneau ---
        for i, mod in enumerate(player.modifiers):
            T.pill(surface, mod.name, 13, T.KIND_COLORS[mod.kind.name], T.PANEL, pad=(12, 4),
                   topright=(box.right, box.bottom + 10 + i * 30))
