"""Écran d'évolution, comme dans les jeux : « Quoi ? X évolue ! », silhouettes blanches qui alternent
de plus en plus vite entre l'ancienne et la nouvelle forme, puis révélation et message de félicitations."""
import math
import random

import pygame
from pygame import Vector2

from .. import settings as S
from . import theme as T

INTRO, MORPH = 1.6, 3.6         # durées (s) : texte d'intro, alternance des silhouettes
WHITE = (255, 255, 255)


class EvolutionScreen:
    """handle_event() renvoie True quand le joueur confirme la fin (après la révélation)."""

    def __init__(self, old, new):
        self.old, self.new = old, new
        self.t = 0.0
        self.rng = random.Random(7)
        self.sparks = [(self.rng.uniform(0, math.tau), self.rng.uniform(40, 260), self.rng.uniform(0.0, 1.0)) for _ in range(28)]

    @property
    def revealed(self) -> bool:
        return self.t >= INTRO + MORPH

    def update(self, dt: float) -> None:
        self.t += dt

    def handle_event(self, e) -> bool:
        if not self.revealed:
            return False
        return (e.type == pygame.KEYDOWN and e.key in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE)) or \
            (e.type == pygame.MOUSEBUTTONDOWN and e.button == 1)

    # --- rendu ---------------------------------------------------------------
    def draw(self, surface, sprites) -> None:
        w, h = surface.get_size()
        surface.blit(T.blurred_backdrop(surface, (10, 14, 34), 175), (0, 0))
        c = Vector2(w // 2, 290)
        t, scale = self.t, 6
        k = min(1.0, max(0.0, (t - INTRO) / MORPH))             # avancement de la métamorphose

        # halo et rayons qui montent en puissance
        glow_r = 90 + 110 * (k if not self.revealed else max(0.0, 1 - (t - INTRO - MORPH) * 1.2))
        from .attack_fx import glow
        glow(surface, c, glow_r * 1.6, (255, 255, 255), int(60 + 120 * k) if not self.revealed else int(160 * max(0.0, 1 - (t - INTRO - MORPH))))
        for i in range(10):
            ang = i / 10 * math.tau + t * 0.6
            L = 120 + 200 * (k if not self.revealed else 0.4)
            pygame.draw.line(surface, (255, 255, 255), c + Vector2(math.cos(ang), math.sin(ang)) * 70,
                             c + Vector2(math.cos(ang), math.sin(ang)) * L, 2)

        if t < INTRO:                                           # « Quoi ? X évolue ! »
            sprites.draw_icon(surface, self.old.dex, c, "Idle", 0, scale)
            msg = f"Quoi ? {self.old.name} évolue !"
        elif not self.revealed:                                 # alternance de silhouettes, de plus en plus rapide
            interval = 0.38 - 0.32 * k
            phase = int((t - INTRO) / max(interval, 0.05)) % 2
            dex = self.new.dex if phase else self.old.dex
            sprites.draw_icon(surface, dex, c, "Idle", 0, scale, shadow=False, tint=WHITE)
            msg = f"Quoi ? {self.old.name} évolue !"
        else:                                                   # révélation
            r = t - INTRO - MORPH
            flash = max(0.0, 1 - r * 2.2)
            sprites.draw_icon(surface, self.new.dex, c, "Idle", 0, scale)
            if flash > 0:
                sprites.draw_icon(surface, self.new.dex, c, "Idle", 0, scale, shadow=False, tint=WHITE, alpha=int(255 * flash))
            for ang, dist, delay in self.sparks:                # étincelles qui s'écartent
                q = max(0.0, r - delay * 0.3)
                if q > 0:
                    p = c + Vector2(math.cos(ang), math.sin(ang)) * dist * min(1.0, q * 1.4)
                    T.draw_type_icon(surface, self.new.types[0], p, 8)
            msg = f"Félicitations ! {self.old.name} a évolué en {self.new.name} !"

        # boîte de dialogue en bas (comme les messages des jeux)
        box = pygame.Rect(0, 0, 800, 120)
        box.center = (w // 2, 560)
        T.alpha_rect(surface, box, T.NAVY, 235, 16)
        pygame.draw.rect(surface, WHITE, box, 3, border_radius=16)
        T.text(surface, msg, 28, T.WHITE, shadow=True, center=(box.centerx, box.y + 44))
        if self.revealed:
            widths = [T.font(13).size(ty.value.upper())[0] + 40 for ty in self.new.types]     # largeur d'une pastille
            x = box.centerx - (sum(widths) + 10 * (len(widths) - 1)) // 2
            for ty in self.new.types:
                x = T.type_pill(surface, ty, 26, topleft=(x, box.y + 76)).right + 10
            T.prompt_bar(surface, [("Entrée", "Continuer")], w - 28, h - 24, size=15)
