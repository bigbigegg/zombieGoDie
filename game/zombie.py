import random
import math
import pygame
import config
from game.sprites import get_zombie_frames, get_death_frames


class Zombie:
    def __init__(self, ztype="NORMAL", wave=1):
        cfg = config.ZOMBIE_TYPES[ztype]
        self.ztype    = ztype
        self.color    = cfg["color"]
        self.hp       = cfg["hp"]
        self.max_hp   = cfg["hp"]
        self.speed    = cfg["speed"] * (config.ZOMBIE_SPEED_SCALE ** (wave - 1))
        self.score    = cfg["score"]
        self.w        = cfg["w"]
        self.h        = cfg["h"]

        self.x = float(config.SCREEN_W + self.w)
        self.y = float(random.randint(80, config.SCREEN_H - 120 - self.h))

        self.frozen       = False
        self.freeze_timer = 0.0
        self.dead         = False
        self.death_timer  = 0.0
        self.death_duration = 0.5

        # Sprite frames
        self._frames = get_zombie_frames(ztype, target_h=self.h)
        self._death_frames = get_death_frames(target_h=self.h)

        self._anim_idx   = 0
        self._anim_speed = 8 + random.uniform(-2, 2)  # frames per second

    def update(self, dt):
        if self.dead:
            self.death_timer += dt
            return

        self._anim_idx += self._anim_speed * dt

        if self.frozen:
            self.freeze_timer -= dt
            if self.freeze_timer <= 0:
                self.frozen = False
            effective_speed = self.speed * 0.5
        else:
            effective_speed = self.speed

        self.x -= effective_speed * dt

    def take_damage(self, dmg=1):
        if self.dead:
            return
        self.hp -= dmg
        if self.hp <= 0:
            self.hp   = 0
            self.dead = True

    def freeze(self, duration=3.0):
        self.frozen       = True
        self.freeze_timer = duration

    def is_dead(self):
        return self.dead

    def death_finished(self):
        return self.dead and self.death_timer >= self.death_duration

    def reached_left(self):
        return self.x + self.w < 0

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.w, self.h)

    def draw(self, surface):
        bob = int(3 * math.sin(self._anim_idx))

        if self.dead:
            death_frame = min(int(self.death_timer / self.death_duration * 4), 3)
            if self._death_frames and death_frame < len(self._death_frames):
                frame = self._death_frames[death_frame]
                cx = int(self.x) + self.w // 2 - frame.get_width() // 2
                cy = int(self.y) + self.h // 2 - frame.get_height() // 2
                alpha = int(200 * (1 - self.death_timer / self.death_duration))
                frame.set_alpha(alpha)
                surface.blit(frame, (cx, cy))
            return

        # Draw zombie sprite
        if self._frames:
            idx = int(self._anim_idx) % len(self._frames)
            frame = self._frames[idx]
            if self.frozen:
                tint = pygame.Surface(frame.get_size(), pygame.SRCALPHA)
                tint.fill((100, 180, 255, 80))
                frame = frame.copy()
                frame.blit(tint, (0, 0))
            surface.blit(frame, (int(self.x), int(self.y) + bob))
        else:
            # Fallback: colored rectangle
            r = pygame.Rect(int(self.x), int(self.y) + bob, self.w, self.h)
            draw_color = config.COLORS["freeze"] if self.frozen else self.color
            pygame.draw.rect(surface, draw_color, r, border_radius=4)

        # HP bar
        if self.hp < self.max_hp:
            bar_w = self.w
            filled = int(bar_w * self.hp / self.max_hp)
            pygame.draw.rect(surface, (80, 20, 20),  (int(self.x), int(self.y) - 8, bar_w, 5))
            pygame.draw.rect(surface, (220, 50, 50), (int(self.x), int(self.y) - 8, filled, 5))
