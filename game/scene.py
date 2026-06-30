import random
import pygame
import config
from game.zombie import Zombie
from game.attack import ATTACK_MAP
from game.player import Player


class FloatingText:
    def __init__(self, text, x, y, color=(255, 220, 50), size=24):
        self.text  = text
        self.x     = float(x)
        self.y     = float(y)
        self.color = color
        self.timer = 0.0
        self.duration = 1.0
        self.font  = pygame.font.SysFont("Arial", size, bold=True)

    def update(self, dt):
        self.timer += dt
        self.y -= 40 * dt

    def done(self):
        return self.timer >= self.duration

    def draw(self, surface):
        alpha = int(255 * (1 - self.timer / self.duration))
        surf  = self.font.render(self.text, True, self.color)
        surf.set_alpha(alpha)
        surface.blit(surf, (int(self.x), int(self.y)))


class Scene:
    def __init__(self):
        self.player       = Player()
        self.zombies      = []
        self.attacks      = []
        self.floats       = []
        self.wave_timer   = 0.0
        self.game_over    = False
        self._spawn_wave()

        self.wave_flash_timer = 0.0

    def _spawn_wave(self):
        wave  = self.player.wave
        count = config.ZOMBIE_COUNT_BASE + (wave - 1) * config.ZOMBIE_COUNT_STEP

        pool = ["NORMAL"]
        if wave >= 2:
            pool.append("FAT")
        if wave >= 4:
            pool.append("FAST")

        for _ in range(count):
            ztype = random.choice(pool)
            self.zombies.append(Zombie(ztype, wave))

        # Elite every 3 waves
        if wave % 3 == 0:
            self.zombies.append(Zombie("ELITE", wave))

        self.wave_flash_timer = 2.0

    def handle_gesture(self, gesture_name):
        """Try to fire skill for the given gesture name string."""
        if gesture_name == "NONE" or self.game_over:
            return
        if not self.player.can_use(gesture_name):
            return
        cls = ATTACK_MAP.get(gesture_name)
        if cls:
            self.attacks.append(cls())
            self.player.use_skill(gesture_name)

    def update(self, dt, confirmed_gesture=None):
        if self.game_over:
            return

        if confirmed_gesture:
            self.handle_gesture(confirmed_gesture)

        self.player.tick(dt)

        # Attacks
        live_zombies = [z for z in self.zombies if not z.is_dead()]
        for atk in self.attacks:
            atk.update(dt, live_zombies)
        self.attacks = [a for a in self.attacks if not a.done]

        # Zombies
        for z in self.zombies:
            z.update(dt)
            if not z.is_dead() and z.reached_left():
                self.player.take_damage()
                z.dead = True  # remove without score

        # Collect kills
        for z in self.zombies:
            if z.is_dead() and not z.death_finished():
                pass
            elif z.is_dead() and z.death_finished() and z.score > 0:
                mult = min(self.player.combo, 3)
                self.player.add_kill(z.score)
                label = f"+{z.score}"
                if mult > 1:
                    label += f" x{mult}"
                self.floats.append(FloatingText(label, z.x, z.y))
                z.score = 0  # prevent double-counting

        self.zombies = [z for z in self.zombies if not z.death_finished()]

        # Floating texts
        for f in self.floats:
            f.update(dt)
        self.floats = [f for f in self.floats if not f.done()]

        # Wave progression
        self.wave_timer += dt
        if self.wave_timer >= config.WAVE_INTERVAL:
            self.wave_timer = 0.0
            self.player.wave += 1
            self._spawn_wave()

        # Cap simultaneous zombies
        if len(self.zombies) > config.MAX_ZOMBIES:
            self.zombies = self.zombies[:config.MAX_ZOMBIES]

        if self.wave_flash_timer > 0:
            self.wave_flash_timer -= dt

        if self.player.is_dead():
            self.game_over = True

    def draw(self, surface):
        # Background
        surface.fill(config.COLORS["bg"])

        # Ground line
        pygame.draw.line(surface, (50, 50, 60),
                         (0, config.SCREEN_H - 100),
                         (config.SCREEN_W, config.SCREEN_H - 100), 2)

        # Attacks (behind zombies)
        for atk in self.attacks:
            atk.draw(surface)

        # Zombies
        for z in self.zombies:
            z.draw(surface)

        # Floating texts
        for f in self.floats:
            f.draw(surface)

        # Wave flash
        if self.wave_flash_timer > 0:
            alpha = int(min(255, self.wave_flash_timer * 150))
            s = pygame.Surface((config.SCREEN_W, config.SCREEN_H), pygame.SRCALPHA)
            s.fill((255, 100, 50, alpha))
            surface.blit(s, (0, 0))
            font = pygame.font.SysFont("Arial", 72, bold=True)
            text = font.render(f"WAVE {self.player.wave}", True, (255, 220, 100))
            x = (config.SCREEN_W - text.get_width()) // 2
            y = (config.SCREEN_H - text.get_height()) // 2
            surface.blit(text, (x, y))

        # Game over overlay
        if self.game_over:
            s = pygame.Surface((config.SCREEN_W, config.SCREEN_H), pygame.SRCALPHA)
            s.fill((0, 0, 0, 160))
            surface.blit(s, (0, 0))
            font_big = pygame.font.SysFont("Arial", 80, bold=True)
            font_sm  = pygame.font.SysFont("Arial", 36)
            t1 = font_big.render("GAME OVER", True, (220, 50, 50))
            t2 = font_sm.render(f"Score: {self.player.score}   Wave: {self.player.wave}", True, (220, 220, 220))
            t3 = font_sm.render("Press R to restart  |  ESC to quit", True, (180, 180, 180))
            cx = config.SCREEN_W // 2
            cy = config.SCREEN_H // 2
            surface.blit(t1, (cx - t1.get_width() // 2, cy - 100))
            surface.blit(t2, (cx - t2.get_width() // 2, cy))
            surface.blit(t3, (cx - t3.get_width() // 2, cy + 60))
