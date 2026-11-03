from dataclasses import dataclass

from .attack import Attack, Category
from .types import effectiveness


STAB = 1.5


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
    """dégâts = puissance x (stat off. / stat déf.) x multiplicateur de type x STAB (x1,5 si l'élément
    de l'attaque est un type du lanceur)."""
    owner = attack.owner
    if attack.category is Category.PHYSICAL:
        ratio = owner.stats.atk / target.stats.defense
    else:
        ratio = owner.stats.spa / target.stats.spdef
    mult = effectiveness(attack.element, target.types)
    stab = STAB if attack.element in getattr(owner, "types", ()) else 1.0
    return DamageResult(attack.power * ratio * mult * stab, mult)
