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

    name = "Mannequin"

    def __init__(self, pos, types, species=None, name: str = "Mannequin", max_hp: float = 300):
        super().__init__(pos, 30, TYPE_COLORS.get(types[0], S.GREY), types, max_hp)
        self.species = species
        self.name = name
        self.flash = 0.0
        self.respawn = 0.0

    @property
    def sprite_anim(self) -> tuple:
        return ("Hurt", 1.0) if self.flash > 0 else ("Idle", 1.0)

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
        self.tick_death(dt)
        if not self.alive:
            self.respawn -= dt
            if self.respawn <= 0:
                self.alive, self.hp, self.death_t = True, self.max_hp, None

    def draw(self, surface) -> None:     # cercle de secours (sans sprite)
        if self.dying:
            pygame.draw.circle(surface, self.color, self.pos, max(1, self.radius * (1 - self.death_t / S.DEATH_DURATION)))
            return
        if not self.alive:
            return
        color = S.WHITE if self.flash > 0 else self.color
        pygame.draw.circle(surface, color, self.pos, self.radius)
        pygame.draw.circle(surface, (20, 20, 20), self.pos, self.radius, 3)
        self.draw_status(surface)
