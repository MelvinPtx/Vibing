import pygame

from .. import settings as S
from .room_view import ICON

CARD_W, CARD_H, GAP = 250, 320, 30


def _wrap(font, text, width):
    lines, line = [], ""
    for word in text.split():
        test = f"{line} {word}".strip()
        if font.size(test)[0] > width and line:
            lines.append(line)
            line = word
        else:
            line = test
    return lines + [line]


class RewardMenu:
    """Choix d'une récompense parmi N cartes. handle_event() renvoie le Modifier choisi."""

    def __init__(self, choices):
        self.choices = choices
        self.index = 0
        total = len(choices) * CARD_W + (len(choices) - 1) * GAP
        x0 = (S.SCREEN_W - total) // 2
        self.rects = [pygame.Rect(x0 + i * (CARD_W + GAP), 190, CARD_W, CARD_H)
                      for i in range(len(choices))]
        self.title = pygame.font.SysFont("monospace", 28, bold=True)
        self.font = pygame.font.SysFont("monospace", 16)
        self.bold = pygame.font.SysFont("monospace", 20, bold=True)

    def handle_event(self, e):
        n = len(self.choices)
        if e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_LEFT, pygame.K_q, pygame.K_a):
                self.index = (self.index - 1) % n
            elif e.key in (pygame.K_RIGHT, pygame.K_d):
                self.index = (self.index + 1) % n
            elif e.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                return self.choices[self.index]
            elif pygame.K_1 <= e.key <= pygame.K_9 or pygame.K_KP1 <= e.key <= pygame.K_KP9:
                i = e.key - (pygame.K_1 if e.key <= pygame.K_9 else pygame.K_KP1)
                if i < n:
                    return self.choices[i]
        elif e.type == pygame.MOUSEMOTION:
            for i, r in enumerate(self.rects):
                if r.collidepoint(e.pos):
                    self.index = i
        elif e.type == pygame.MOUSEBUTTONDOWN and e.button == 1:
            for i, r in enumerate(self.rects):
                if r.collidepoint(e.pos):
                    return self.choices[i]
        return None

    def draw(self, surface) -> None:
        dim = pygame.Surface((S.SCREEN_W, S.SCREEN_H), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 170))
        surface.blit(dim, (0, 0))
        t = self.title.render("Choisis ta récompense", True, S.WHITE)
        surface.blit(t, t.get_rect(center=(S.SCREEN_W // 2, 130)))
        for i, (mod, r) in enumerate(zip(self.choices, self.rects)):
            color, _ = ICON[mod.kind]
            selected = i == self.index
            pygame.draw.rect(surface, (44, 48, 66), r, border_radius=12)
            pygame.draw.rect(surface, color, (r.x, r.y, r.w, 70), border_top_left_radius=12,
                             border_top_right_radius=12)
            pygame.draw.rect(surface, S.WHITE if selected else S.GREY, r, 4 if selected else 2,
                             border_radius=12)
            for j, line in enumerate(_wrap(self.bold, mod.name, r.w - 24)):
                surface.blit(self.bold.render(line, True, (20, 20, 20)), (r.x + 12, r.y + 12 + j * 24))
            surface.blit(self.font.render(mod.kind.value, True, S.GREY), (r.x + 12, r.y + 84))
            for j, line in enumerate(_wrap(self.font, mod.description, r.w - 24)):
                surface.blit(self.font.render(line, True, S.WHITE), (r.x + 12, r.y + 120 + j * 22))
            surface.blit(self.font.render(f"[{i + 1}]", True, S.YELLOW), (r.right - 40, r.bottom - 28))
        h = self.font.render("← → / souris pour choisir · ENTRÉE ou 1-3 / clic pour valider", True, S.GREY)
        surface.blit(h, h.get_rect(center=(S.SCREEN_W // 2, 560)))
