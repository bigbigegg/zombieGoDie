"""Procedural particle system — no external assets needed."""
import math
import random
import pygame


class Particle:
    __slots__ = ("x", "y", "vx", "vy", "size", "color", "life", "max_life",
                 "gravity", "friction", "decay", "shape")

    def __init__(self, x, y, vx, vy, size, color, life,
                 gravity=0, friction=0, decay=True, shape="circle"):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.size = float(size)
        self.color = color
        self.life = float(life)
        self.max_life = float(life)
        self.gravity = gravity
        self.friction = friction
        self.decay = decay
        self.shape = shape

    @property
    def progress(self):
        return 1.0 - self.life / self.max_life if self.max_life > 0 else 1.0

    @property
    def done(self):
        return self.life <= 0

    def update(self, dt):
        self.life -= dt
        if self.done:
            return
        self.vy += self.gravity * dt
        self.vx *= (1.0 - self.friction * dt)
        self.vy *= (1.0 - self.friction * dt)
        self.x += self.vx * dt
        self.y += self.vy * dt

    def draw(self, surface):
        if self.done:
            return
        frac = self.progress
        a = int(max(0, 255 * (1.0 - frac))) if self.decay else 255
        s = max(1, int(self.size * (1.0 - frac * 0.5) if self.decay else self.size))
        color = self.color[:3] + (min(a, 255),)

        if self.shape == "circle":
            r = pygame.Rect(0, 0, s * 2, s * 2)
            r.center = (int(self.x), int(self.y))
            surf = pygame.Surface((s * 2 + 2, s * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(surf, color, (s + 1, s + 1), s)
            surface.blit(surf, r)
        elif self.shape == "square":
            surf = pygame.Surface((s, s), pygame.SRCALPHA)
            surf.fill(color)
            surface.blit(surf, (int(self.x - s // 2), int(self.y - s // 2)))
        elif self.shape == "spark":
            width = max(1, int(s * 0.3))
            surf = pygame.Surface((s, width + 2), pygame.SRCALPHA)
            surf.fill(color)
            rot_surf = pygame.transform.rotate(surf, math.degrees(math.atan2(self.vy, self.vx)))
            r = rot_surf.get_rect(center=(int(self.x), int(self.y)))
            surface.blit(rot_surf, r)
        elif self.shape == "star":
            points = []
            for i in range(5):
                a = math.radians(-90 + i * 72)
                r = s if i % 2 == 0 else s * 0.4
                points.append((self.x + r * math.cos(a), self.y + r * math.sin(a)))
            pygame.draw.polygon(surface, color[:3], points)


class Decal:
    """Static decal on ground — blood splatter, scorch mark."""
    def __init__(self, x, y, color, size=12, life=4.0):
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.size = float(size)
        self.life = float(life)
        self.max_life = float(life)

    @property
    def progress(self):
        return 1.0 - self.life / self.max_life

    @property
    def done(self):
        return self.life <= 0

    def update(self, dt):
        self.life -= dt

    def draw(self, surface):
        if self.done:
            return
        a = max(0, int(200 * (1.0 - self.progress ** 2)))
        if a <= 0:
            return
        surf = pygame.Surface((int(self.size * 2) + 2, int(self.size * 2) + 2), pygame.SRCALPHA)
        for i in range(5):
            ox = random.randint(-int(self.size * 0.3), int(self.size * 0.3))
            oy = random.randint(-int(self.size * 0.3), int(self.size * 0.3))
            r = random.randint(2, int(self.size * 0.5))
            pygame.draw.circle(surf, (*self.color, a // 2),
                               (int(self.size) + ox, int(self.size) + oy), r)
        pygame.draw.circle(surf, (*self.color, a),
                           (int(self.size), int(self.size)), int(self.size))
        surface.blit(surf, (int(self.x - self.size), int(self.y - self.size)))


class ParticleManager:
    """Manages all particles and decals. Single instance in Scene."""

    def __init__(self):
        self.particles = []
        self.decals = []

    def emit_burst(self, x, y, count=15, color=(255, 200, 50), speed=120,
                   size=3, life=0.6, gravity=0, spread=360, shape="circle", decay=True):
        for _ in range(count):
            angle = math.radians(random.uniform(0, spread))
            spd = random.uniform(speed * 0.3, speed)
            vx = math.cos(angle) * spd
            vy = math.sin(angle) * spd - abs(spread - 360) * 0.1
            sz = random.uniform(size * 0.5, size * 1.5)
            lt = random.uniform(life * 0.6, life)
            self.particles.append(Particle(
                x, y, vx, vy, sz, color, lt,
                gravity=gravity, decay=decay, shape=shape
            ))

    def emit_stream(self, x, y, count=3, color=(255, 200, 50), life=0.3,
                    speed=50, size=3, spread=60, gravity=0, shape="circle"):
        """Emit a small burst every call — good for continuous effects."""
        self.emit_burst(x, y, count, color, speed, size, life, gravity, spread, shape)

    def emit_trail(self, x, y, color=(255, 200, 50), life=0.2, size=2, speed=20):
        self.particles.append(Particle(
            x, y, random.uniform(-speed, speed), random.uniform(-speed, speed),
            size, color, life, decay=True, shape="circle"
        ))

    def emit_blood(self, x, y, count=8):
        self.emit_burst(x, y, count, color=(180, 30, 20), speed=80,
                        size=2, life=0.5, gravity=300, spread=180, shape="square")
        # Ground decal
        self.decals.append(Decal(x, y, (100, 20, 10), size=random.uniform(8, 16)))

    def emit_debris(self, x, y, count=6):
        self.emit_burst(x, y, count, color=(120, 100, 80), speed=150,
                        size=3, life=0.7, gravity=400, spread=360, shape="square", decay=False)

    def emit_sparks(self, x, y, color=(255, 255, 100), count=6):
        self.emit_burst(x, y, count, color=color, speed=200,
                        size=2, life=0.3, gravity=0, spread=120, shape="spark")

    def update(self, dt):
        for p in self.particles:
            p.update(dt)
        self.particles = [p for p in self.particles if not p.done]

        for d in self.decals:
            d.update(dt)
        self.decals = [d for d in self.decals if not d.done]

    def draw(self, surface):
        for p in self.particles:
            p.draw(surface)
        for d in self.decals:
            d.draw(surface)
