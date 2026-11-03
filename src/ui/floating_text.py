import pygame
from pygame import Vector2


class FloatingTexts:
    def __init__(self):
        self.font = pygame.font.SysFont("monospace", 18, bold=True)
        self.items = []  # [pos, text, color, life]

    def add(self, pos, text, color) -> None:
        self.items.append([Vector2(pos), text, color, 1.0])

    def update(self, dt: float) -> None:
        for it in self.items:
            it[0].y -= 40 * dt
            it[3] -= dt
        self.items = [i for i in self.items if i[3] > 0]

    def draw(self, surface) -> None:
        for pos, text, color, _ in self.items:
            img = self.font.render(text, True, color)
            surface.blit(img, pos - Vector2(img.get_width() / 2, 0))
