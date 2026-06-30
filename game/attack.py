import math
import pygame
import config


class BaseAttack:
    def __init__(self):
        self.done = False

    def update(self, dt, zombies):
        raise NotImplementedError

    def draw(self, surface):
        raise NotImplementedError


class ShockwaveAttack(BaseAttack):
    """拳头 — AOE冲击波，覆盖左1/3屏幕"""
    def __init__(self):
        super().__init__()
        self.timer    = 0.0
        self.duration = 0.5
        self.range_x  = config.SCREEN_W // 3
        self._hit     = False

    def update(self, dt, zombies):
        self.timer += dt
        if not self._hit:
            self._hit = True
            for z in zombies:
                if not z.is_dead() and z.x < self.range_x:
                    z.take_damage(99)
        if self.timer >= self.duration:
            self.done = True

    def draw(self, surface):
        progress = self.timer / self.duration
        alpha    = int(200 * (1 - progress))
        w        = int(self.range_x * progress * 2)
        h        = config.SCREEN_H
        s = pygame.Surface((w, h), pygame.SRCALPHA)
        s.fill((255, 140, 0, alpha))
        surface.blit(s, (0, 0))

        # Ring effect
        radius = int(self.range_x * progress)
        if radius > 0:
            pygame.draw.circle(surface, (255, 200, 100),
                               (0, config.SCREEN_H // 2), radius, 6)


class BulletAttack(BaseAttack):
    """食指 — 高速子弹"""
    def __init__(self):
        super().__init__()
        self.x     = 60.0
        self.y     = float(config.SCREEN_H // 2)
        self.speed = 900.0
        self.radius = 8

    def update(self, dt, zombies):
        self.x += self.speed * dt
        if self.x > config.SCREEN_W:
            self.done = True
            return
        for z in zombies:
            if not z.is_dead() and z.rect.collidepoint(int(self.x), int(self.y)):
                z.take_damage(3)
                self.done = True
                return

    def draw(self, surface):
        pygame.draw.circle(surface, (255, 255, 50),
                           (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (255, 200, 0),
                           (int(self.x), int(self.y)), self.radius - 2)


class FreezeAttack(BaseAttack):
    """手掌 — 全屏冰冻"""
    def __init__(self):
        super().__init__()
        self.timer    = 0.0
        self.duration = 0.6
        self._applied = False

    def update(self, dt, zombies):
        self.timer += dt
        if not self._applied:
            self._applied = True
            for z in zombies:
                if not z.is_dead():
                    z.freeze(3.0)
        if self.timer >= self.duration:
            self.done = True

    def draw(self, surface):
        progress = self.timer / self.duration
        alpha    = int(120 * (1 - progress))
        s = pygame.Surface((config.SCREEN_W, config.SCREEN_H), pygame.SRCALPHA)
        s.fill((100, 180, 255, alpha))
        surface.blit(s, (0, 0))


class LaserAttack(BaseAttack):
    """剪刀手 — 双线激光"""
    def __init__(self):
        super().__init__()
        self.timer    = 0.0
        self.duration = 0.5
        y_mid  = config.SCREEN_H // 2
        self.y1 = y_mid - 80
        self.y2 = y_mid + 80
        self.thickness = 6

    def update(self, dt, zombies):
        self.timer += dt
        for z in zombies:
            if z.is_dead():
                continue
            r = z.rect
            if r.top <= self.y1 <= r.bottom or r.top <= self.y2 <= r.bottom:
                z.take_damage(1)
        if self.timer >= self.duration:
            self.done = True

    def draw(self, surface):
        progress = self.timer / self.duration
        alpha    = int(255 * (1 - progress * 0.7))
        color    = (255, 50, 50, alpha)

        for y in (self.y1, self.y2):
            s = pygame.Surface((config.SCREEN_W, self.thickness * 2), pygame.SRCALPHA)
            s.fill(color)
            surface.blit(s, (0, y - self.thickness))

        # Glow
        glow_color = (255, 150, 150)
        for y in (self.y1, self.y2):
            pygame.draw.line(surface, glow_color,
                             (0, y), (config.SCREEN_W, y), 2)


class BombAttack(BaseAttack):
    """大拇指 — 延迟爆炸投弹"""
    def __init__(self):
        super().__init__()
        import random
        self.timer     = 0.0
        self.fuse      = 0.8
        self.exploded  = False
        self.exp_timer = 0.0
        self.exp_duration = 0.4
        self.radius    = 120
        # Random target in middle area
        self.tx = random.randint(config.SCREEN_W // 3, config.SCREEN_W * 2 // 3)
        self.ty = random.randint(config.SCREEN_H // 4, config.SCREEN_H * 3 // 4)

    def update(self, dt, zombies):
        self.timer += dt

        if not self.exploded and self.timer >= self.fuse:
            self.exploded = True
            for z in zombies:
                if z.is_dead():
                    continue
                cx = z.x + z.w / 2
                cy = z.y + z.h / 2
                dist = math.hypot(cx - self.tx, cy - self.ty)
                if dist <= self.radius:
                    z.take_damage(5)

        if self.exploded:
            self.exp_timer += dt
            if self.exp_timer >= self.exp_duration:
                self.done = True

    def draw(self, surface):
        if not self.exploded:
            # Flashing target indicator
            blink = int(self.timer * 10) % 2 == 0
            color = (255, 80, 0) if blink else (200, 50, 0)
            pygame.draw.circle(surface, color, (self.tx, self.ty), 20, 3)
            pygame.draw.line(surface, color,
                             (self.tx - 25, self.ty), (self.tx + 25, self.ty), 2)
            pygame.draw.line(surface, color,
                             (self.tx, self.ty - 25), (self.tx, self.ty + 25), 2)
        else:
            progress = self.exp_timer / self.exp_duration
            alpha    = int(220 * (1 - progress))
            radius   = int(self.radius * (0.5 + progress * 0.5))
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 160, 30, alpha), (radius, radius), radius)
            surface.blit(s, (self.tx - radius, self.ty - radius))
            # Inner bright core
            core_r = max(1, int(radius * (1 - progress) * 0.6))
            if core_r > 0:
                pygame.draw.circle(surface, (255, 255, 200),
                                   (self.tx, self.ty), core_r)


ATTACK_MAP = {
    "FIST":     ShockwaveAttack,
    "POINT":    BulletAttack,
    "OPEN":     FreezeAttack,
    "PEACE":    LaserAttack,
    "THUMBSUP": BombAttack,
}
