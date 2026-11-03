"""Table des types (génération 6+, 18 types) et calcul du multiplicateur."""
from enum import Enum


class PType(Enum):
    NORMAL = "Normal"
    FEU = "Feu"
    EAU = "Eau"
    ELECTRIK = "Électrik"
    PLANTE = "Plante"
    GLACE = "Glace"
    COMBAT = "Combat"
    POISON = "Poison"
    SOL = "Sol"
    VOL = "Vol"
    PSY = "Psy"
    INSECTE = "Insecte"
    ROCHE = "Roche"
    SPECTRE = "Spectre"
    DRAGON = "Dragon"
    TENEBRES = "Ténèbres"
    ACIER = "Acier"
    FEE = "Fée"


T = PType
# attaquant -> (super efficace x2, peu efficace x0.5, immunisé x0)
_RAW = {
    T.NORMAL:   ([], [T.ROCHE, T.ACIER], [T.SPECTRE]),
    T.FEU:      ([T.PLANTE, T.GLACE, T.INSECTE, T.ACIER], [T.FEU, T.EAU, T.ROCHE, T.DRAGON], []),
    T.EAU:      ([T.FEU, T.SOL, T.ROCHE], [T.EAU, T.PLANTE, T.DRAGON], []),
    T.ELECTRIK: ([T.EAU, T.VOL], [T.ELECTRIK, T.PLANTE, T.DRAGON], [T.SOL]),
    T.PLANTE:   ([T.EAU, T.SOL, T.ROCHE],
                 [T.FEU, T.PLANTE, T.POISON, T.VOL, T.INSECTE, T.DRAGON, T.ACIER], []),
    T.GLACE:    ([T.PLANTE, T.SOL, T.VOL, T.DRAGON], [T.FEU, T.EAU, T.GLACE, T.ACIER], []),
    T.COMBAT:   ([T.NORMAL, T.GLACE, T.ROCHE, T.TENEBRES, T.ACIER],
                 [T.POISON, T.VOL, T.PSY, T.INSECTE, T.FEE], [T.SPECTRE]),
    T.POISON:   ([T.PLANTE, T.FEE], [T.POISON, T.SOL, T.ROCHE, T.SPECTRE], [T.ACIER]),
    T.SOL:      ([T.FEU, T.ELECTRIK, T.POISON, T.ROCHE, T.ACIER], [T.PLANTE, T.INSECTE], [T.VOL]),
    T.VOL:      ([T.PLANTE, T.COMBAT, T.INSECTE], [T.ELECTRIK, T.ROCHE, T.ACIER], []),
    T.PSY:      ([T.COMBAT, T.POISON], [T.PSY, T.ACIER], [T.TENEBRES]),
    T.INSECTE:  ([T.PLANTE, T.PSY, T.TENEBRES],
                 [T.FEU, T.COMBAT, T.POISON, T.VOL, T.SPECTRE, T.ACIER, T.FEE], []),
    T.ROCHE:    ([T.FEU, T.GLACE, T.VOL, T.INSECTE], [T.COMBAT, T.SOL, T.ACIER], []),
    T.SPECTRE:  ([T.PSY, T.SPECTRE], [T.TENEBRES], [T.NORMAL]),
    T.DRAGON:   ([T.DRAGON], [T.ACIER], [T.FEE]),
    T.TENEBRES: ([T.PSY, T.SPECTRE], [T.COMBAT, T.TENEBRES, T.FEE], []),
    T.ACIER:    ([T.GLACE, T.ROCHE, T.FEE], [T.FEU, T.EAU, T.ELECTRIK, T.ACIER], []),
    T.FEE:      ([T.COMBAT, T.DRAGON, T.TENEBRES], [T.FEU, T.POISON, T.ACIER], []),
}

TYPE_CHART: dict[PType, dict[PType, float]] = {}
for _atk, (_se, _nve, _imm) in _RAW.items():
    row = {d: 1.0 for d in PType}
    row.update({d: 2.0 for d in _se})
    row.update({d: 0.5 for d in _nve})
    row.update({d: 0.0 for d in _imm})
    TYPE_CHART[_atk] = row


def effectiveness(attack_type: PType, defender_types) -> float:
    """Multiplicateur total (double type = produit : x4, x0.25, x0...)."""
    mult = 1.0
    for d in defender_types:
        mult *= TYPE_CHART[attack_type][d]
    return mult
