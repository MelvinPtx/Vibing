from .attack import Attack
from ..geometry import circle_hits_rect
from .damage import compute_damage


class CombatSystem:
    """Possède les attaques actives et résout les collisions -> dégâts.

    Ne dessine rien : renvoie des événements (cible, résultat, position) que l'UI affiche.
    """

    def __init__(self):
        self.attacks: list[Attack] = []      # attaques du joueur (touchent les ennemis)
        self.hostile: list[Attack] = []      # attaques ennemies (touchent le joueur)
        self.events = []         # (cible, DamageResult, attaque) : le joueur a touché
        self.hurt_events = []    # (joueur, DamageResult, attaque) : le joueur a été touché

    def spawn(self, attack: Attack) -> None:
        self.attacks.append(attack)

    def spawn_hostile(self, attack: Attack) -> None:
        self.hostile.append(attack)

    def clear(self) -> None:
        self.attacks.clear()
        self.hostile.clear()

    @staticmethod
    def _blocked(atk: Attack, obstacles) -> bool:
        """Un projectile (non perforant) s'arrête contre un rocher ; mêlée et zones passent."""
        return not atk.pierce and any(circle_hits_rect(atk.pos, atk.radius, o) for o in obstacles)

    def update(self, dt: float, targets, player=None, obstacles=()) -> None:
        self.events = []
        self.hurt_events = []
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
        for atk in self.attacks:
            if self._blocked(atk, obstacles):
                atk.kill()
        self.attacks = [a for a in self.attacks if a.active]
        self._update_hostile(dt, player, obstacles)

    def _update_hostile(self, dt: float, player, obstacles=()) -> None:
        for atk in self.hostile:
            atk.update(dt)
            if self._blocked(atk, obstacles):
                atk.kill()
                continue
            if player is None or not player.alive or id(player) in atk.hit or not atk.overlaps(player):
                continue
            res = compute_damage(atk, player)
            if res.multiplier == 0 or player.take_damage(res.amount):
                # Touché (ou immunisé). Si le joueur est invincible (dash), rien n'est consommé :
                # le projectile continue sa route -> esquive.
                atk.hit.add(id(player))
                self.hurt_events.append((player, res, atk))
                if not atk.pierce:
                    atk.kill()
        self.hostile = [a for a in self.hostile if a.active]
