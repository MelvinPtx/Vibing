"""Progression : niveaux, expérience, mise à l'échelle des stats et des ennemis.

Les courbes d'expérience sont les vraies (taux de croissance de pokemondb) ; un ennemi rapporte
`expérience de base de l'espèce x niveau de l'ennemi / 7`, comme dans les jeux.
"""
import math

START_LEVEL = 10          # niveau de départ d'une partie
XP_SCALE = 1.0
STAT_PER_LEVEL = 0.025    # +2,5 % d'Attaque/Défense/... par niveau gagné depuis le départ
HP_PER_LEVEL = 0.035      # +3,5 % de PV max par niveau


def exp_for_level(growth: str, n: int) -> int:
    """Expérience totale à avoir pour atteindre le niveau n (taux de croissance des jeux)."""
    if n <= 1:
        return 0
    if growth == "medium fast":
        v = n ** 3
    elif growth == "medium slow":
        v = 6 / 5 * n ** 3 - 15 * n ** 2 + 100 * n - 140
    elif growth == "fast":
        v = 4 * n ** 3 / 5
    elif growth == "slow":
        v = 5 * n ** 3 / 4
    elif growth == "erratic":
        if n < 50:
            v = n ** 3 * (100 - n) / 50
        elif n < 68:
            v = n ** 3 * (150 - n) / 100
        elif n < 98:
            v = n ** 3 * math.floor((1911 - 10 * n) / 3) / 500
        else:
            v = n ** 3 * (160 - n) / 100
    elif growth == "fluctuating":
        if n < 15:
            v = n ** 3 * (math.floor((n + 1) / 3) + 24) / 50
        elif n < 36:
            v = n ** 3 * (n + 14) / 50
        else:
            v = n ** 3 * (math.floor(n / 2) + 32) / 50
    else:
        raise ValueError(f"taux de croissance inconnu : {growth}")
    return max(0, round(v))


def level_from_exp(growth: str, xp: float, cap: int = 100) -> int:
    n = 1
    while n < cap and exp_for_level(growth, n + 1) <= xp:
        n += 1
    return n


def stat_mult(level: int) -> float:
    return 1 + STAT_PER_LEVEL * (level - START_LEVEL)


def hp_mult(level: int) -> float:
    return 1 + HP_PER_LEVEL * (level - START_LEVEL)


def enemy_level(room_number: int, boss: bool = False) -> int:
    return 3 + 2 * room_number + (6 if boss else 0)


def xp_reward(base_exp: int, level: int) -> int:
    return max(1, round(base_exp * level / 7 * XP_SCALE))


def enemy_hp_mult(room_number: int) -> float:
    return 1 + 0.10 * (room_number - 1)


def enemy_power_mult(room_number: int) -> float:
    return 1 + 0.04 * (room_number - 1)
