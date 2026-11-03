import pygame

from .. import settings as S


class DebugHUD:
    """Affiche cooldown du dash, i-frames et FPS (utile pour tester le Dash)."""

    def __init__(self):
        self.font = pygame.font.SysFont("monospace", 16)

    def _bar(self, surface, x, y, w, h, ratio, color, label):
        pygame.draw.rect(surface, (50, 50, 60), (x, y, w, h))
        pygame.draw.rect(surface, color, (x, y, int(w * max(0, min(1, ratio))), h))
        pygame.draw.rect(surface, S.WHITE, (x, y, w, h), 1)
        surface.blit(self.font.render(label, True, S.WHITE), (x + w + 8, y - 1))

    def draw(self, surface, player, fps: float) -> None:
        ready = 1 - player.dash_cd_left / S.DASH_COOLDOWN
        self._bar(surface, 16, 16, 160, 14, ready, S.CYAN if ready >= 1 else GREY_ORANGE,
                  "DASH PRÊT" if ready >= 1 else f"DASH {player.dash_cd_left:.2f}s")
        self._bar(surface, 16, 38, 160, 14, player.iframes_left / S.DASH_IFRAMES, S.YELLOW,
                  f"I-FRAMES {player.iframes_left:.2f}s")
        lines = [f"FPS {fps:4.0f}", "ZQSD/WASD/flèches : bouger", "ESPACE/MAJ/clic droit : dash", "ÉCHAP : quitter"]
        for i, t in enumerate(lines):
            surface.blit(self.font.render(t, True, S.GREY), (16, S.SCREEN_H - 90 + i * 20))


GREY_ORANGE = (200, 130, 60)
