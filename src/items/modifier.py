"""Modificateurs passifs (les « Boons » de Hades). Trois points d'accroche :
  on_attack  : modifie une Attack juste avant son lancement (élément, puissance, effets on_hit)
  on_update  : effet continu (régénération...)
  on_pickup  : effet immédiat à la récupération (baies)
"""
from ..combat.types import PType
from ..levels.room import RewardKind


class Modifier:
    name = "?"
    description = ""
    kind = RewardKind.OBJET
    instant = False   # True : consommé à la récupération, jamais stocké
    badge_type = None # PType affiché en pastille sur la carte de récompense (optionnel)

    def on_pickup(self, player) -> None: ...
    def on_attack(self, attack, player) -> None: ...
    def on_update(self, player, dt: float) -> None: ...


# --- Objets stratégiques -------------------------------------------------
class Charbon(Modifier):
    name = "Charbon"
    description = "Vive-Attaque devient de type Feu et brûle l'ennemi (6 dégâts/s pendant 3 s)."
    BURN_TIME, BURN_DPS = 3.0, 6.0
    badge_type = PType.FEU

    def on_attack(self, attack, player) -> None:
        if attack.slot != "basic":
            return
        attack.element = PType.FEU
        attack.on_hit.append(self._burn)

    def _burn(self, attack, target, result) -> None:
        if result.multiplier > 0 and PType.FEU not in target.types:  # les types Feu sont immunisés
            target.apply_burn(self.BURN_TIME, self.BURN_DPS)


class Restes(Modifier):
    name = "Restes"
    description = "Régénère 1,5 PV par seconde."

    def on_update(self, player, dt: float) -> None:
        player.hp = min(player.max_hp, player.hp + 1.5 * dt)


class BandeauChoix(Modifier):
    name = "Bandeau Choix"
    description = "Toutes tes attaques infligent 30 % de dégâts en plus."

    def on_attack(self, attack, player) -> None:
        attack.power *= 1.3


class Lunettes(Modifier):
    name = "Lunettes Choix"
    description = "Tes attaques Spéciales (E et R) infligent 40 % de dégâts en plus."

    def on_attack(self, attack, player) -> None:
        if attack.slot in ("special", "cast"):
            attack.power *= 1.4


# --- Capsules Techniques : changent l'élément d'un emplacement -------------
class CT(Modifier):
    kind = RewardKind.CAPSULE
    slot = ""
    element = PType.NORMAL

    @property
    def badge_type(self):
        return self.element

    def on_attack(self, attack, player) -> None:
        if attack.slot == self.slot:
            attack.element = self.element


def _ct(label, slot, element, slot_label):
    return type(label, (CT,), {
        "name": f"CT {label}", "slot": slot, "element": element,
        "description": f"{slot_label} devient de type {element.value}."})


LanceFlammes = _ct("Lance-Flammes", "special", PType.FEU, "Tranch'Herbe (E)")
Surf = _ct("Surf", "cast", PType.EAU, "Ball'Ombre (R)")
RayonGlace = _ct("Rayon Glace", "cast", PType.GLACE, "Ball'Ombre (R)")
Seisme = _ct("Séisme", "special", PType.SOL, "Tranch'Herbe (E)")


# --- Baies : effet immédiat ---------------------------------------------
class Baie(Modifier):
    kind = RewardKind.SOIN
    instant = True


class BaieOran(Baie):
    name = "Baie Oran"
    description = "Soigne 30 PV."

    def on_pickup(self, player) -> None:
        player.hp = min(player.max_hp, player.hp + 30)


class BaieSitrus(Baie):
    name = "Baie Sitrus"
    description = "+20 PV max et soigne 20 PV."

    def on_pickup(self, player) -> None:
        player.max_hp += 20
        player.hp = min(player.max_hp, player.hp + 20)


class BaieMepo(Baie):
    name = "Baie Mepo"
    description = "Soigne entièrement."

    def on_pickup(self, player) -> None:
        player.hp = player.max_hp
