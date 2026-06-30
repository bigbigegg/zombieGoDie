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


GESTURES_INFO = [
    ("✊  拳头 Fist",       "冲击波 — 清空屏幕左1/3区域",  "冷却 3s", (255, 120,  60)),
    ("☝  食指 Point",      "精准射击 — 高速单体子弹",     "冷却 1s", (255, 230,  60)),
    ("✋  手掌 Open",       "冰冻术 — 全屏僵尸减速50%",   "冷却 5s", (100, 180, 255)),
    ("✌  剪刀手 Peace",    "双线激光 — 两条水平激光0.5s","冷却 2s", (200,  80, 255)),
    ("👍  大拇指 Thumb Up","投弹 — 延时范围爆炸",         "冷却 4s", (80,  220, 120)),
]


class Scene:
    def __init__(self):
        self.player       = Player()
        self.zombies      = []
        self.attacks      = []
        self.floats       = []
        self.wave_timer   = 0.0
        self.game_over    = False
        self.intro        = True          # show instructions before game starts
        self.wave_flash_timer = 0.0
        self._intro_blink = 0.0

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

    def start_game(self):
        """Called when player dismisses the intro screen."""
        self.intro = False
        self._spawn_wave()

    def handle_gesture(self, gesture_name):
        """Try to fire skill for the given gesture name string."""
        if gesture_name == "NONE" or self.game_over or self.intro:
            return
        if not self.player.can_use(gesture_name):
            return
        cls = ATTACK_MAP.get(gesture_name)
        if cls:
            self.attacks.append(cls())
            self.player.use_skill(gesture_name)

    def update(self, dt, confirmed_gesture=None):
        if self.intro or self.game_over:
            self._intro_blink += dt
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
            text = font.render(f"第 {self.player.wave} 波", True, (255, 220, 100))
            x = (config.SCREEN_W - text.get_width()) // 2
            y = (config.SCREEN_H - text.get_height()) // 2
            surface.blit(text, (x, y))

        # Intro screen
        if self.intro:
            self._draw_intro(surface)
            return

        # Game over overlay
        if self.game_over:
            s = pygame.Surface((config.SCREEN_W, config.SCREEN_H), pygame.SRCALPHA)
            s.fill((0, 0, 0, 160))
            surface.blit(s, (0, 0))
            font_big = pygame.font.SysFont("Arial", 80, bold=True)
            font_sm  = pygame.font.SysFont("Arial", 36)
            t1 = font_big.render("游戏结束", True, (220, 50, 50))
            t2 = font_sm.render(f"得分: {self.player.score}  波次: {self.player.wave}", True, (220, 220, 220))
            t3 = font_sm.render("按 R 重新开始  |  ESC 退出", True, (180, 180, 180))
            cx = config.SCREEN_W // 2
            cy = config.SCREEN_H // 2
            surface.blit(t1, (cx - t1.get_width() // 2, cy - 100))
            surface.blit(t2, (cx - t2.get_width() // 2, cy))
            surface.blit(t3, (cx - t3.get_width() // 2, cy + 60))

    def _draw_intro(self, surface):
        surface.fill(config.COLORS["bg"])

        # Decorative scanlines
        for yy in range(0, config.SCREEN_H, 6):
            pygame.draw.line(surface, (0, 0, 0, 30), (0, yy), (config.SCREEN_W, yy))

        cx = config.SCREEN_W // 2

        font_title  = pygame.font.SysFont("Arial", 72, bold=True)
        font_sub    = pygame.font.SysFont("Arial", 26, bold=True)
        font_body   = pygame.font.SysFont("Arial", 22)
        font_hint   = pygame.font.SysFont("Arial", 28, bold=True)
        font_label  = pygame.font.SysFont("Arial", 20, bold=True)
        font_desc   = pygame.font.SysFont("Arial", 19)

        # Title
        title = font_title.render("ZOMBIE GO DIE", True, (220, 50, 50))
        surface.blit(title, (cx - title.get_width() // 2, 40))

        # Subtitle
        sub = font_sub.render("用手势消灭僵尸！", True, (200, 180, 100))
        surface.blit(sub, (cx - sub.get_width() // 2, 125))

        # Divider
        pygame.draw.line(surface, (60, 60, 80), (80, 165), (config.SCREEN_W - 80, 165), 1)

        # How to play header
        how = font_sub.render("玩法说明", True, (140, 200, 255))
        surface.blit(how, (cx - how.get_width() // 2, 178))

        tips = [
            "面对摄像头，在画面中清晰露出你的手。",
            "每种手势需要稳定保持一小段时间来触发技能。",
            "僵尸从屏幕右侧涌来——别让它们走到最左边！",
            "每 30 秒进入下一波，僵尸更多、更快。",
        ]
        y = 215
        for tip in tips:
            t = font_body.render(f"• {tip}", True, (190, 190, 190))
            surface.blit(t, (cx - t.get_width() // 2, y))
            y += 28

        # Divider
        pygame.draw.line(surface, (60, 60, 80), (80, y + 4), (config.SCREEN_W - 80, y + 4), 1)
        y += 18

        # Gesture skills header
        gh = font_sub.render("手势技能", True, (140, 200, 255))
        surface.blit(gh, (cx - gh.get_width() // 2, y))
        y += 32

        col_gesture = cx - 480
        col_effect  = cx - 200
        col_cd      = cx + 340

        hdr_color = (120, 120, 140)
        surface.blit(font_label.render("手势",      True, hdr_color), (col_gesture, y))
        surface.blit(font_label.render("效果",      True, hdr_color), (col_effect,  y))
        surface.blit(font_label.render("冷却时间",  True, hdr_color), (col_cd,      y))
        y += 24

        for gesture, effect, cd, color in GESTURES_INFO:
            pygame.draw.rect(surface, (30, 30, 45), (80, y - 2, config.SCREEN_W - 160, 26), border_radius=4)
            surface.blit(font_desc.render(gesture, True, color),       (col_gesture, y))
            surface.blit(font_desc.render(effect,  True, (210, 210, 210)), (col_effect, y))
            surface.blit(font_desc.render(cd,      True, (160, 160, 180)), (col_cd,    y))
            y += 30

        # Blinking "press space" prompt
        if int(self._intro_blink * 2) % 2 == 0:
            prompt = font_hint.render("按 空格键 开始游戏", True, (255, 220, 50))
            surface.blit(prompt, (cx - prompt.get_width() // 2, config.SCREEN_H - 58))
