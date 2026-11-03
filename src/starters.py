"""Starters jouables (ceux d'Écarlate / Violet) et leurs évolutions, construits à partir des VRAIES
données : types, stats de base et capacités apprises par niveau (src/data/pokedex.py, généré depuis
pokemondb/database et PokeAPI).

Chaque forme a trois emplacements : "basic" (clic gauche : coup rapide), "special" (E : coup lourd ou
onde autour de soi) et "cast" (R : projectile). Chaque emplacement est une **chaîne** de vraies capacités
avec leur niveau d'apprentissage : à chaque montée de niveau, on utilise la dernière débloquée.
Les stats de la première forme sont réglées à la main ; celles des évolutions en découlent par le
rapport des vraies stats de base (Meowscarada a 110/61 de l'Attaque de Sprigatito, etc.).
"""
from dataclasses import dataclass, field

from .combat.moves import MoveSpec, from_db
from .combat.types import PType
from .data.pokedex import EVOLUTIONS, POKEMON
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
    chains: dict = field(repr=False)             # emplacement -> ((niveau, MoveSpec), ...)
    max_hp: float = 100.0
    speed_mult: float = 1.0
    atk: float = 1.0
    spa: float = 1.0
    defense: float = 1.0
    spdef: float = 1.0
    stage: int = 1
    evolves_to: "Starter | None" = None
    evolve_level: int = 0

    def moves_at(self, level: int) -> dict:
        """Capacité active de chaque emplacement à ce niveau (la dernière débloquée)."""
        out = {}
        for slot, chain in self.chains.items():
            unlocked = [spec for lv, spec in chain if lv <= level]
            out[slot] = unlocked[-1] if unlocked else chain[0][1]
        return out

    def next_unlock(self, level: int):
        """(niveau, capacité) du prochain déblocage, ou None."""
        later = [(lv, spec) for chain in self.chains.values() for lv, spec in chain if lv > level]
        return min(later, key=lambda x: x[0]) if later else None

    @property
    def moves(self) -> dict:
        return self.moves_at(START_LEVEL)


def _chain(*entries) -> tuple:
    """entries : (identifiant, niveau, forme[, options])."""
    return tuple((lv, from_db(mid, shape, **(opts[0] if opts else {}))) for mid, lv, shape, *opts in entries)


def _ratio(dex: int, base_dex: int, stat: str) -> float:
    return POKEMON[dex]["stats"][stat] / POKEMON[base_dex]["stats"][stat]


def _types(dex: int) -> tuple:
    return tuple(_T[t] for t in POKEMON[dex]["types"])


def _build(base_dex, mults, forms) -> "Starter":
    """Comme _line, mais renvoie bien le stade 1 en gardant la chaîne d'évolution."""
    built = {}
    for stage in (3, 2, 1):
        dex, desc, chains = forms[stage - 1]
        evo = built.get(stage + 1)
        built[stage] = Starter(
            POKEMON[dex]["name"], dex, _types(dex), desc, chains,
            max_hp=round(mults["hp"] * _ratio(dex, base_dex, "hp"), 1),
            speed_mult=round(mults["speed"] * _ratio(dex, base_dex, "speed") ** 0.35, 3),
            atk=round(mults["atk"] * _ratio(dex, base_dex, "attack"), 3),
            spa=round(mults["spa"] * _ratio(dex, base_dex, "spatk"), 3),
            defense=round(mults["def"] * _ratio(dex, base_dex, "defense"), 3),
            spdef=round(mults["spd"] * _ratio(dex, base_dex, "spdef"), 3),
            stage=stage, evolves_to=evo, evolve_level=EVOLUTIONS[dex][1] if evo else 0)
    return built[1]


# --- Sprigatito -> Floragato -> Meowscarada (Plante, puis Plante/Ténèbres) ------------------------
SPRIGATITO = _build(906, dict(hp=100, speed=1.0, atk=1.10, spa=1.00, **{"def": 1.0, "spd": 1.0}), [
    (906, "Pokémon Chat Herbe. Rapide et griffu : Griffe, Morsure, et Feuille Magik qui ne rate jamais.", {
        "basic": _chain(("scratch", 1, "melee"), ("quick-attack", 15, "melee")),
        "special": _chain(("bite", 7, "wide")),
        "cast": _chain(("leafage", 1, "bolt"), ("magical-leaf", 13, "bolt"))}),
    (907, "Pokémon Chat Herbe. Plus agile et plus robuste : Tranche, Canon Graine puis Éco-Sphère.", {
        "basic": _chain(("scratch", 1, "melee"), ("quick-attack", 15, "melee")),
        "special": _chain(("bite", 7, "wide"), ("u-turn", 24, "wide"), ("slash", 33, "wide"), ("play-rough", 42, "wide")),
        "cast": _chain(("magical-leaf", 13, "bolt"), ("seed-bomb", 20, "bolt"), ("energy-ball", 38, "bolt"),
                       ("leaf-storm", 46, "bolt"))}),
    (908, "Pokémon Illusionniste. Magie Florale, une fleur piégée toujours critique qui ne rate jamais.", {
        "basic": _chain(("scratch", 1, "melee"), ("quick-attack", 15, "melee")),
        "special": _chain(("u-turn", 24, "wide"), ("slash", 33, "wide"), ("night-slash", 38, "wide"),
                          ("knock-off", 52, "wide")),
        "cast": _chain(("flower-trick", 0, "bolt", dict(crit=1.5)), ("energy-ball", 42, "bolt"),
                       ("leaf-storm", 64, "bolt"))}),
])

# --- Fuecoco -> Crocalor -> Skeledirge (Feu, puis Feu/Spectre) --------------------------------------
FUECOCO = _build(909, dict(hp=125, speed=0.92, atk=1.00, spa=1.10, **{"def": 1.10, "spd": 1.0}), [
    (909, "Pokémon Croco Feu. Robuste et lent : ses ondes de voix et ses flammes touchent tout autour de lui.", {
        "basic": _chain(("tackle", 1, "melee")),
        "special": _chain(("round", 7, "zone"), ("incinerate", 15, "zone")),
        "cast": _chain(("ember", 1, "bolt", dict(burn=0.10)))}),
    (910, "Pokémon Croco Feu. Sa voix devient une arme : Aboiement et Mégaphone, puis Lance-Flammes.", {
        "basic": _chain(("tackle", 1, "melee")),
        "special": _chain(("round", 10, "zone"), ("snarl", 24, "zone"), ("hyper-voice", 38, "zone")),
        "cast": _chain(("ember", 1, "bolt", dict(burn=0.10)), ("incinerate", 17, "bolt"),
                       ("flamethrower", 32, "bolt", dict(burn=0.10)), ("fire-blast", 47, "bolt", dict(burn=0.10)))}),
    (911, "Pokémon Chanteur. Chant Flamboyant : chaque note augmente son Atq. Spé., puis Ball'Ombre.", {
        "basic": _chain(("tackle", 1, "melee"), ("lick", 7, "melee")),        # Léchouille : Spectre = bonus de type
        "special": _chain(("snarl", 24, "zone"), ("hyper-voice", 42, "zone")),
        "cast": _chain(("torch-song", 0, "bolt", dict(buff=("spa", 0.12))), ("shadow-ball", 38, "bolt"),
                       ("overheat", 64, "bolt", dict(burn=0.0)))}),
])

# --- Quaxly -> Quaxwell -> Quaquaval (Eau, puis Eau/Combat) ------------------------------------------
QUAXLY = _build(912, dict(hp=95, speed=1.08, atk=1.12, spa=0.95, **{"def": 1.0, "spd": 1.0}), [
    (912, "Pokémon Caneton. Rapide et physique : Écras'Face, Aqua-Jet toujours prioritaire, Pistolet à O.", {
        "basic": _chain(("pound", 1, "melee"), ("aqua-jet", 13, "melee")),
        "special": _chain(("wing-attack", 10, "wide")),
        "cast": _chain(("water-gun", 1, "bolt"))}),
    (913, "Pokémon Canardélégant. Ses lames d'eau et d'air traversent les ennemis alignés.", {
        "basic": _chain(("pound", 1, "melee"), ("aqua-jet", 13, "melee")),
        "special": _chain(("wing-attack", 10, "wide"), ("low-sweep", 19, "wide"), ("acrobatics", 38, "wide"),
                          ("liquidation", 43, "wide")),
        "cast": _chain(("water-gun", 1, "bolt"), ("water-pulse", 17, "bolt"), ("aqua-cutter", 23, "bolt", dict(pierce=True)),
                       ("air-slash", 27, "bolt", dict(pierce=True)))}),
    (914, "Pokémon Danseur. Danse Aquatique : chaque pas le rend plus rapide ; Balayette de combattant.", {
        "basic": _chain(("pound", 1, "melee"), ("aqua-jet", 13, "melee"), ("low-sweep", 17, "melee")),
        "special": _chain(("aqua-step", 0, "wide", dict(buff=("speed", 0.10))), ("mega-kick", 38, "wide"),
                          ("close-combat", 58, "wide")),
        "cast": _chain(("water-gun", 1, "bolt"), ("water-pulse", 17, "bolt"), ("aqua-cutter", 21, "bolt", dict(pierce=True)),
                       ("air-slash", 27, "bolt", dict(pierce=True)), ("wave-crash", 64, "bolt"))}),
])

STARTERS = [SPRIGATITO, FUECOCO, QUAXLY]
DEFAULT_STARTER = SPRIGATITO


def lineage(first: Starter) -> list:
    out = [first]
    while out[-1].evolves_to:
        out.append(out[-1].evolves_to)
    return out


ALL_FORMS = [f for s in STARTERS for f in lineage(s)]
