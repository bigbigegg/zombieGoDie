import math
import random
import pygame
import config


class BaseAttack:
    def __init__(self):
        self.done = False

    def update(self, dt, zombies, particles=None):
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

    def update(self, dt, zombies, particles=None):
        self.timer += dt
        if not self._hit:
            self._hit = True
            for z in zombies:
                if not z.is_dead() and z.x < self.range_x:
                    z.take_damage(99)
            # Ground dust burst along the shockwave line
            if particles:
                for _ in range(12):
                    px = random.randint(0, self.range_x)
                    py = random.randint(config.SCREEN_H - 100, config.SCREEN_H - 70)
                    particles.emit_burst(px, py, count=3, color=(140, 120, 100),
                                         speed=60, size=3, life=0.5, gravity=200,
                                         spread=180, shape="square")
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
            for i in range(3):
                r = radius + i * 10
                a = alpha // (i + 1)
                pygame.draw.circle(surface, (255, 200, 100, a),
                                   (0, config.SCREEN_H // 2), r, 4)


class BulletAttack(BaseAttack):
    """食指 — 高速子弹"""
    def __init__(self):
        super().__init__()
        self.x     = 60.0
        self.y     = float(config.SCREEN_H // 2)
        self.speed = 900.0
        self.radius = 8
        self._trail_timer = 0.0

    def update(self, dt, zombies, particles=None):
        self.x += self.speed * dt

        # Trail particles
        self._trail_timer += dt
        if particles and self._trail_timer > 0.015:
            self._trail_timer = 0
            particles.emit_trail(self.x, self.y, color=(255, 200, 50), life=0.15, size=3)
            particles.emit_trail(self.x, self.y, color=(255, 100, 20), life=0.1, size=2)

        if self.x > config.SCREEN_W:
            self.done = True
            return
        for z in zombies:
            if not z.is_dead() and z.rect.collidepoint(int(self.x), int(self.y)):
                z.take_damage(3)
                if particles:
                    particles.emit_sparks(self.x, self.y, color=(255, 255, 100), count=8)
                    particles.emit_burst(self.x, self.y, count=5, color=(255, 200, 50),
                                         speed=100, size=2, life=0.2, spread=120, shape="spark")
                self.done = True
                return

    def draw(self, surface):
        # Glow
        glow = pygame.Surface((self.radius * 4, self.radius * 4), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 200, 50, 60), (self.radius * 2, self.radius * 2), self.radius * 2)
        surface.blit(glow, (int(self.x) - self.radius * 2, int(self.y) - self.radius * 2))
        # Core
        pygame.draw.circle(surface, (255, 255, 200),
                           (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surface, (255, 200, 0),
                           (int(self.x), int(self.y)), self.radius - 3)


class FreezeAttack(BaseAttack):
    """手掌 — 全屏冰冻"""
    def __init__(self):
        super().__init__()
        self.timer    = 0.0
        self.duration = 0.6
        self._applied = False

    def update(self, dt, zombies, particles=None):
        self.timer += dt
        if not self._applied:
            self._applied = True
            for z in zombies:
                if not z.is_dead():
                    z.freeze(3.0)
            # Ice crystal burst
            if particles:
                for _ in range(8):
                    px = random.randint(0, config.SCREEN_W)
                    py = random.randint(0, config.SCREEN_H - 100)
                    particles.emit_burst(px, py, count=6, color=(180, 220, 255),
                                         speed=80, size=3, life=0.8, gravity=100,
                                         spread=360, shape="star")
        if self.timer >= self.duration:
            self.done = True

    def draw(self, surface):
        progress = self.timer / self.duration
        alpha    = int(120 * (1 - progress))
        s = pygame.Surface((config.SCREEN_W, config.SCREEN_H), pygame.SRCALPHA)
        s.fill((100, 180, 255, alpha))
        surface.blit(s, (0, 0))

        # Frost edges
        edge = int(20 * progress)
        if edge > 0:
            pygame.draw.rect(surface, (150, 200, 255, alpha // 2),
                             (0, 0, config.SCREEN_W, edge))
            pygame.draw.rect(surface, (150, 200, 255, alpha // 2),
                             (0, config.SCREEN_H - edge, config.SCREEN_W, edge))


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
        self._spark_timer = 0.0

    def update(self, dt, zombies, particles=None):
        self.timer += dt
        self._spark_timer += dt

        for z in zombies:
            if z.is_dead():
                continue
            r = z.rect
            if r.top <= self.y1 <= r.bottom or r.top <= self.y2 <= r.bottom:
                if z.take_damage(1) > 0 and particles:
                    particles.emit_blood(z.x + z.w // 2, z.y + z.h // 2, count=6)

        # Sparks along laser lines
        if particles and self._spark_timer > 0.04:
            self._spark_timer = 0
            for y in (self.y1, self.y2):
                sx = random.randint(0, config.SCREEN_W)
                particles.emit_sparks(sx, y, color=(255, 100, 100), count=2)

        if self.timer >= self.duration:
            self.done = True

    def draw(self, surface):
        progress = self.timer / self.duration
        alpha    = int(255 * (1 - progress * 0.7))

        for y in (self.y1, self.y2):
            # Outer glow
            glow = pygame.Surface((config.SCREEN_W, self.thickness * 6), pygame.SRCALPHA)
            glow.fill((255, 50, 50, alpha // 3))
            surface.blit(glow, (0, y - self.thickness * 3))
            # Core line
            line = pygame.Surface((config.SCREEN_W, self.thickness), pygame.SRCALPHA)
            line.fill((255, 80, 80, alpha))
            surface.blit(line, (0, y - self.thickness // 2))
            # Bright center
            bright = pygame.Surface((config.SCREEN_W, 2), pygame.SRCALPHA)
            bright.fill((255, 200, 200, alpha))
            surface.blit(bright, (0, y - 1))


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
        self.tx = random.randint(config.SCREEN_W // 3, config.SCREEN_W * 2 // 3)
        self.ty = random.randint(config.SCREEN_H // 4, config.SCREEN_H * 3 // 4)
        self._fuse_particles = 0.0

    def update(self, dt, zombies, particles=None):
        self.timer += dt

        if not self.exploded:
            self._fuse_particles += dt
            # Fuse smoke
            if particles and self._fuse_particles > 0.05:
                self._fuse_particles = 0
                ox = random.randint(-10, 10)
                oy = random.randint(-10, 10)
                particles.emit_burst(self.tx + ox, self.ty + oy, count=1,
                                     color=(200, 150, 100), speed=30, size=3,
                                     life=0.4, gravity=0, spread=60, shape="circle")

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
            # Explosion particles!
            if particles:
                # Fireball
                particles.emit_burst(self.tx, self.ty, count=20, color=(255, 200, 50),
                                     speed=200, size=5, life=0.6, gravity=0,
                                     spread=360, shape="circle")
                # Smoke
                particles.emit_burst(self.tx, self.ty, count=10, color=(100, 100, 100),
                                     speed=80, size=8, life=0.8, gravity=-50,
                                     spread=360, shape="circle", decay=True)
                # Debris
                particles.emit_debris(self.tx, self.ty, count=12)
                # Sparks
                particles.emit_sparks(self.tx, self.ty, color=(255, 255, 200), count=15)

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

            # Main explosion
            s = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (255, 160, 30, alpha), (radius, radius), radius)
            surface.blit(s, (self.tx - radius, self.ty - radius))

            # Shockwave ring
            ring_r = int(radius * 1.2)
            ring_a = int(150 * (1 - progress))
            if ring_r > 0 and ring_a > 0:
                pygame.draw.circle(surface, (255, 200, 100, ring_a),
                                   (self.tx, self.ty), ring_r, 4)

            # Bright core
            core_r = max(1, int(radius * (1 - progress) * 0.6))
            pygame.draw.circle(surface, (255, 255, 200),
                               (self.tx, self.ty), core_r)


ATTACK_MAP = {
    "FIST":     ShockwaveAttack,
    "POINT":    BulletAttack,
    "OPEN":     FreezeAttack,
    "PEACE":    LaserAttack,
    "THUMBSUP": BombAttack,
}
