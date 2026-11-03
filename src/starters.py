"""Starters jouables (ceux d'Écarlate / Violet) et leurs évolutions, construits à partir des VRAIES
données : types, stats de base et capacités apprises par niveau (src/data/pokedex.py, généré depuis
pokemondb/database et PokeAPI).

Chaque forme apprend **toutes** les capacités offensives de sa liste Écarlate/Violet, à leur niveau réel
(`learnset`). Trois emplacements sont jouables : "basic" (clic gauche : coup rapide), "special" (E : coup
lourd ou onde autour de soi) et "cast" (R : projectile) ; chaque capacité a son emplacement et sa forme
dans `combat.moves.MOVE_PLAN`. Par défaut on équipe la dernière apprise de chaque emplacement, et le
joueur peut en choisir une autre dans le menu « Capacités ».
Les stats de la première forme sont réglées à la main ; celles des évolutions en découlent par le
rapport des vraies stats de base (Meowscarada a 110/61 de l'Attaque de Sprigatito, etc.).
"""
from dataclasses import dataclass

from .combat.moves import MOVE_PLAN, slot_of, spec_for
from .combat.types import PType
from .data.pokedex import EVOLUTIONS, LEARNSET, POKEMON
from .progression import START_LEVEL

SLOTS = ("basic", "special", "cast")
_T = {"grass": PType.PLANTE, "fire": PType.FEU, "water": PType.EAU, "dark": PType.TENEBRES,
      "ghost": PType.SPECTRE, "fighting": PType.COMBAT}


@dataclass(frozen=True, eq=False)
class Starter:
    """Une forme (stade 1, 2 ou 3) d'une lignée de starter."""
    name: str
    dex: int
    types: tuple
    description: str
    max_hp: float = 100.0
    speed_mult: float = 1.0
    atk: float = 1.0
    spa: float = 1.0
    defense: float = 1.0
    spdef: float = 1.0
    stage: int = 1
    evolves_to: "Starter | None" = None
    evolve_level: int = 0

    @property
    def learnset(self) -> dict:
        """{identifiant: niveau} des capacités offensives apprises par cette forme (Écarlate/Violet)."""
        return {m: lv for m, lv in LEARNSET[self.dex].items() if m in MOVE_PLAN}

    def known_at(self, level: int) -> list:
        """Capacités connues à ce niveau, dans l'ordre où elles sont apprises."""
        return [m for m, lv in sorted(self.learnset.items(), key=lambda kv: (kv[1], kv[0])) if lv <= level]

    def next_unlock(self, level: int):
        """(niveau, capacité) de la prochaine capacité à apprendre, ou None."""
        later = [(lv, m) for m, lv in self.learnset.items() if lv > level]
        if not later:
            return None
        lv, m = min(later)
        return lv, spec_for(m)

    @property
    def moves(self) -> dict:
        """Capacités équipées par défaut au niveau de départ (pour l'écran de choix)."""
        return {slot: spec_for(m) for slot, m in auto_equip(self.known_at(START_LEVEL)).items()}


def auto_equip(known: list, manual: dict | None = None) -> dict:
    """Pour chaque emplacement : le choix manuel s'il est connu, sinon la dernière capacité apprise."""
    out = {}
    for slot in SLOTS:
        pick = (manual or {}).get(slot)
        if pick not in known:
            mine = [m for m in known if slot_of(m) == slot]
            pick = mine[-1] if mine else None
        if pick:
            out[slot] = pick
    return out


def _ratio(dex: int, base_dex: int, stat: str) -> float:
    return POKEMON[dex]["stats"][stat] / POKEMON[base_dex]["stats"][stat]


def _types(dex: int) -> tuple:
    return tuple(_T[t] for t in POKEMON[dex]["types"])


def _build(base_dex: int, mults: dict, forms) -> "Starter":
    """Construit une lignée du stade 3 vers le stade 1 (chaque forme pointe vers la suivante)."""
    built = {}
    for stage in (3, 2, 1):
        dex, desc = forms[stage - 1]
        evo = built.get(stage + 1)
        built[stage] = Starter(
            POKEMON[dex]["name"], dex, _types(dex), desc,
            max_hp=round(mults["hp"] * _ratio(dex, base_dex, "hp"), 1),
            speed_mult=round(mults["speed"] * _ratio(dex, base_dex, "speed") ** 0.35, 3),
            atk=round(mults["atk"] * _ratio(dex, base_dex, "attack"), 3),
            spa=round(mults["spa"] * _ratio(dex, base_dex, "spatk"), 3),
            defense=round(mults["def"] * _ratio(dex, base_dex, "defense"), 3),
            spdef=round(mults["spd"] * _ratio(dex, base_dex, "spdef"), 3),
            stage=stage, evolves_to=evo, evolve_level=EVOLUTIONS[dex][1] if evo else 0)
    return built[1]


SPRIGATITO = _build(906, dict(hp=100, speed=1.0, atk=1.10, spa=1.00, **{"def": 1.0, "spd": 1.0}), [
    (906, "Pokémon Chat Herbe. Rapide et griffu : Griffe, Morsure, et Feuille Magik qui ne rate jamais."),
    (907, "Pokémon Chat Herbe. Plus agile et plus robuste : Tranche, Canon Graine puis Éco-Sphère."),
    (908, "Pokémon Illusionniste. Magie Florale : un bouquet piégé qui ne rate jamais et frappe toujours fort."),
])
FUECOCO = _build(909, dict(hp=125, speed=0.92, atk=1.00, spa=1.10, **{"def": 1.10, "spd": 1.0}), [
    (909, "Pokémon Croco Feu. Robuste et lent : ses chants et ses flammes frappent tout autour de lui."),
    (910, "Pokémon Croco Feu. Sa voix devient une arme : Aboiement et Mégaphone, puis Lance-Flammes."),
    (911, "Pokémon Chanteur. Chant Flamboyant : chaque note augmente son Atq. Spé. ; Ball'Ombre et Châtiment."),
])
QUAXLY = _build(912, dict(hp=95, speed=1.08, atk=1.12, spa=0.95, **{"def": 1.0, "spd": 1.0}), [
    (912, "Pokémon Caneton. Rapide et physique : Écras'Face, Aqua-Jet toujours prioritaire, Pistolet à O."),
    (913, "Pokémon Canardélégant. Ses lames d'eau et d'air traversent les ennemis alignés."),
    (914, "Pokémon Danseur. Danse Aquatique : chaque pas le rend plus rapide ; Balayette de combattant."),
])

STARTERS = [SPRIGATITO, FUECOCO, QUAXLY]
DEFAULT_STARTER = SPRIGATITO


def lineage(first: Starter) -> list:
    out = [first]
    while out[-1].evolves_to:
        out.append(out[-1].evolves_to)
    return out


ALL_FORMS = [f for s in STARTERS for f in lineage(s)]
