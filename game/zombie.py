import random
import pygame
import config


class Zombie:
    def __init__(self, ztype="NORMAL", wave=1):
        cfg = config.ZOMBIE_TYPES[ztype]
        self.ztype  = ztype
        self.hp     = cfg["hp"]
        self.max_hp = cfg["hp"]
        self.speed  = cfg["speed"] * (config.ZOMBIE_SPEED_SCALE ** (wave - 1))
        self.score  = cfg["score"]
        self.color  = cfg["color"]
        self.w      = cfg["w"]
        self.h      = cfg["h"]

        self.x = float(config.SCREEN_W + self.w)
        self.y = float(random.randint(80, config.SCREEN_H - 120 - self.h))

        self.frozen      = False
        self.freeze_timer = 0.0
        self.dead        = False
        self.death_timer  = 0.0
        self.death_duration = 0.4

        # Simple walk animation: oscillate y offset
        self._anim_t = random.uniform(0, 6.28)

    def update(self, dt):
        if self.dead:
            self.death_timer += dt
            return

        self._anim_t += dt * 8

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
        if self.dead:
            alpha = max(0, 1.0 - self.death_timer / self.death_duration)
            color = tuple(int(c * alpha) for c in self.color)
            # Expand slightly on death
            expand = int(self.death_timer * 40)
            r = pygame.Rect(int(self.x) - expand, int(self.y) - expand,
                            self.w + expand * 2, self.h + expand * 2)
            pygame.draw.rect(surface, color, r, border_radius=4)
            return

        bob = int(3 * __import__("math").sin(self._anim_t))
        r = pygame.Rect(int(self.x), int(self.y) + bob, self.w, self.h)

        draw_color = config.COLORS["freeze"] if self.frozen else self.color
        pygame.draw.rect(surface, draw_color, r, border_radius=4)

        # Eyes
        eye_y = r.y + self.h // 4
        pygame.draw.circle(surface, (255, 255, 255), (r.x + self.w // 3,     eye_y), 4)
        pygame.draw.circle(surface, (255, 255, 255), (r.x + self.w * 2 // 3, eye_y), 4)
        pygame.draw.circle(surface, (20,  20,  20),  (r.x + self.w // 3,     eye_y), 2)
        pygame.draw.circle(surface, (20,  20,  20),  (r.x + self.w * 2 // 3, eye_y), 2)

        # HP bar
        if self.hp < self.max_hp:
            bar_w = self.w
            filled = int(bar_w * self.hp / self.max_hp)
            pygame.draw.rect(surface, (80, 20, 20),  (r.x, r.y - 8, bar_w, 5))
            pygame.draw.rect(surface, (220, 50, 50), (r.x, r.y - 8, filled, 5))
