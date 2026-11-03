from .attack import Attack
from .damage import compute_damage


class CombatSystem:
    """Possède les attaques actives et résout les collisions -> dégâts.

    Ne dessine rien : renvoie des événements (cible, résultat, position) que l'UI affiche.
    """

    def __init__(self):
        self.attacks: list[Attack] = []
        self.events = []  # (target, DamageResult, attack) du dernier update

    def spawn(self, attack: Attack) -> None:
        self.attacks.append(attack)

    def update(self, dt: float, targets) -> None:
        self.events = []
        for atk in self.attacks:
            atk.update(dt)
            for t in targets:
                if not t.alive or id(t) in atk.hit or t is atk.owner or not atk.overlaps(t):
                    continue
                atk.hit.add(id(t))
                res = compute_damage(atk, t)
                t.take_damage(res.amount)
                self.events.append((t, res, atk))
                for hook in atk.on_hit:
                    hook(atk, t, res)
                if not atk.pierce:
                    atk.kill()
                    break
        self.attacks = [a for a in self.attacks if a.active]
