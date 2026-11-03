import pygame

from .. import settings as S
from ..combat.types import PType
from .entity import Entity

TYPE_COLORS = {
    PType.NORMAL: (170, 170, 140), PType.FEU: (240, 110, 50), PType.EAU: (70, 130, 240),
    PType.PLANTE: (90, 190, 80), PType.SPECTRE: (110, 80, 150), PType.INSECTE: (160, 190, 40),
    PType.ELECTRIK: (250, 210, 60), PType.ROCHE: (180, 160, 90),
}


class TrainingDummy(Entity):
    """Mannequin statique d'un/deux types. Se relève 1,5 s après sa mort."""

    def __init__(self, pos, types, max_hp: float = 300):
        super().__init__(pos, 24, TYPE_COLORS.get(types[0], S.GREY), types, max_hp)
        self.flash = 0.0
        self.respawn = 0.0
        self.font = pygame.font.SysFont("monospace", 14)

    def take_damage(self, amount: float) -> bool:
        if not self.alive:
            return False
        hit = super().take_damage(amount)
        if hit:
            self.flash = 0.12
            if not self.alive:
                self.respawn = 1.5
        return hit

    def update(self, dt: float) -> None:
        self.flash = max(0.0, self.flash - dt)
        self.tick_status(dt)
        if not self.alive:
            self.respawn -= dt
            if self.respawn <= 0:
                self.alive, self.hp = True, self.max_hp

    def draw(self, surface) -> None:
        if not self.alive:
            return
        color = S.WHITE if self.flash > 0 else self.color
        pygame.draw.circle(surface, color, self.pos, self.radius)
        pygame.draw.circle(surface, (20, 20, 20), self.pos, self.radius, 3)
        self.draw_status(surface)
        w = 60
        x, y = self.pos.x - w / 2, self.pos.y - self.radius - 14
        pygame.draw.rect(surface, (60, 20, 20), (x, y, w, 6))
        pygame.draw.rect(surface, S.RED, (x, y, w * self.hp / self.max_hp, 6))
        label = self.font.render("/".join(t.value for t in self.types), True, S.WHITE)
        surface.blit(label, (self.pos.x - label.get_width() / 2, self.pos.y + self.radius + 6))
