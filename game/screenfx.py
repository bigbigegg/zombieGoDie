"""Screen-level visual effects — shake, flash, vignette, glow."""
import math
import random
import pygame
import config


class ScreenFX:
    """Manages all screen overlay effects. One instance in main.py."""

    def __init__(self):
        self.shake_intensity = 0.0
        self.shake_duration = 0.0
        self.shake_timer = 0.0

        self.flash_timer = 0.0
        self.flash_duration = 0.0
        self.flash_color = (255, 255, 255)

        self.vignette_timer = 0.0
        self.vignette_duration = 1.0
        self.vignette_intensity = 0.0

        self.low_hp_warning = 0.0      # timer for pulse phase
        self.combo_glow_timer = 0.0    # time since last combo glow activation
        self.combo_glow_intensity = 0.0

        self._shake_offset = (0, 0)

    def shake(self, intensity=4, duration=0.15):
        self.shake_intensity = max(self.shake_intensity, intensity)
        self.shake_duration = max(self.shake_duration, duration)
        self.shake_timer = self.shake_duration

    def flash(self, color=(255, 255, 255), duration=0.08):
        self.flash_color = color
        self.flash_duration = duration
        self.flash_timer = duration

    def damage_vignette(self, intensity=0.5, duration=1.0):
        self.vignette_intensity = max(self.vignette_intensity, intensity)
        self.vignette_duration = max(self.vignette_duration, duration)
        self.vignette_timer = self.vignette_duration

    def combo_glow(self, combo_level):
        self.combo_glow_intensity = max(self.combo_glow_intensity, combo_level / 3.0)
        self.combo_glow_timer = 0.5

    def low_hp_pulse(self, active):
        if active:
            self.low_hp_warning += 0.03
        else:
            self.low_hp_warning = 0.0

    def update(self, dt):
        # Shake
        if self.shake_timer > 0:
            self.shake_timer -= dt
            frac = self.shake_timer / self.shake_duration if self.shake_duration > 0 else 1
            intensity = self.shake_intensity * frac
            self._shake_offset = (
                random.uniform(-intensity, intensity),
                random.uniform(-intensity, intensity),
            )
            if self.shake_timer <= 0:
                self._shake_offset = (0, 0)
                self.shake_intensity = 0
        else:
            self._shake_offset = (0, 0)

        # Flash
        if self.flash_timer > 0:
            self.flash_timer -= dt

        # Vignette
        if self.vignette_timer > 0:
            self.vignette_timer -= dt

        # Combo glow
        if self.combo_glow_timer > 0:
            self.combo_glow_timer -= dt
        else:
            self.combo_glow_intensity = 0

    def get_shake_offset(self):
        return self._shake_offset

    def draw_overlay(self, surface):
        """Draw all overlay effects onto the full-screen surface."""
        w, h = surface.get_width(), surface.get_height()

        # Hit flash
        if self.flash_timer > 0:
            frac = self.flash_timer / self.flash_duration if self.flash_duration > 0 else 1
            alpha = int(180 * frac)
            s = pygame.Surface((w, h), pygame.SRCALPHA)
            s.fill((*self.flash_color[:3], alpha))
            surface.blit(s, (0, 0))

        # Damage vignette
        if self.vignette_timer > 0:
            frac = self.vignette_timer / self.vignette_duration if self.vignette_duration > 0 else 1
            intensity = self.vignette_intensity * frac
            self._draw_vignette(surface, (180, 20, 20), intensity)

        # Low HP warning pulse
        if self.low_hp_warning > 0:
            pulse = abs(math.sin(self.low_hp_warning * math.pi * 3))
            self._draw_vignette(surface, (200, 20, 20), pulse * 0.4)

        # Combo glow
        if self.combo_glow_intensity > 0:
            frac = self.combo_glow_timer / 0.5 if self.combo_glow_timer > 0 else 0
            alpha = int(100 * frac * self.combo_glow_intensity)
            if alpha > 0:
                s = pygame.Surface((w, h), pygame.SRCALPHA)
                # Top and bottom borders glow
                border_h = 12
                pygame.draw.rect(s, (255, 200, 50, alpha), (0, 0, w, border_h))
                pygame.draw.rect(s, (255, 200, 50, alpha), (0, h - border_h, w, border_h))
                # Side borders
                pygame.draw.rect(s, (255, 200, 50, alpha), (0, 0, border_h, h))
                pygame.draw.rect(s, (255, 200, 50, alpha), (w - border_h, 0, border_h, h))
                surface.blit(s, (0, 0))

    @staticmethod
    def _draw_vignette(surface, color, intensity):
        w, h = surface.get_width(), surface.get_height()
        alpha = int(180 * intensity)
        if alpha <= 0:
            return
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        r = max(w, h) // 2
        # Radial gradient via multiple concentric rectangles
        for i in range(5):
            frac = 1.0 - (i / 5) * (1.0 - intensity * 0.5)
            cur_alpha = int(alpha * (1.0 - frac * 0.6))
            if cur_alpha <= 0:
                continue
            margin = int(r * frac)
            pygame.draw.rect(s, (*color, cur_alpha),
                             (margin, margin, w - margin * 2, h - margin * 2))
        surface.blit(s, (0, 0))
