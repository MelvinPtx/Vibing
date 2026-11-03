from dataclasses import dataclass

from .attack import Attack, Category
from .types import effectiveness


@dataclass
class DamageResult:
    amount: float
    multiplier: float

    @property
    def label(self) -> str:
        if self.multiplier == 0:
            return "Immunisé !"
        if self.multiplier > 1:
            return f"Super efficace x{self.multiplier:g}"
        if self.multiplier < 1:
            return f"Peu efficace x{self.multiplier:g}"
        return ""


def compute_damage(attack: Attack, target) -> DamageResult:
    """dégâts = puissance x (stat off. / stat déf.) x multiplicateur de type."""
    owner = attack.owner
    if attack.category is Category.PHYSICAL:
        ratio = owner.stats.atk / target.stats.defense
    else:
        ratio = owner.stats.spa / target.stats.spdef
    mult = effectiveness(attack.element, target.types)
    return DamageResult(attack.power * ratio * mult, mult)
