import random

from ..levels.room import RewardKind
from . import modifier as m

CATALOG: dict[RewardKind, list[type]] = {
    RewardKind.OBJET: [m.Charbon, m.Restes, m.BandeauChoix, m.Lunettes],
    RewardKind.CAPSULE: [m.LanceFlammes, m.Surf, m.RayonGlace, m.Seisme],
    RewardKind.SOIN: [m.BaieOran, m.BaieSitrus, m.BaieMepo],
}


def roll_choices(kind: RewardKind, player, rng: random.Random | None = None, n: int = 3) -> list:
    """Jusqu'à `n` récompenses distinctes de la catégorie, hors modificateurs déjà possédés."""
    rng = rng or random
    owned = {type(x) for x in player.modifiers}
    pool = [c for c in CATALOG[kind] if c not in owned]
    if not pool:  # catégorie épuisée -> repli sur une baie
        pool = list(CATALOG[RewardKind.SOIN])
    return [c() for c in rng.sample(pool, min(n, len(pool)))]


def apply_reward(player, mod) -> None:
    mod.on_pickup(player)
    if not mod.instant:
        player.modifiers.append(mod)
