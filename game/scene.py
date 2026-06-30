import os
import random
import pygame
import config
from game.zombie import Zombie
from game.attack import ATTACK_MAP
from game.player import Player
from game.effects import ParticleManager

_BG = None


def _load_bg():
    global _BG
    path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                        "assets", "sprites", "background", "bg.png")
    if os.path.exists(path):
        _BG = pygame.image.load(path).convert()
    else:
        _BG = None


GESTURES_INFO = [
    ("✊  拳头 Fist",       "冲击波 — 清空屏幕左1/3区域",  "冷却 3s", (255, 120,  60)),
    ("☝  食指 Point",      "精准射击 — 高速单体子弹",     "冷却 1s", (255, 230,  60)),
    ("✋  手掌 Open",       "冰冻术 — 全屏僵尸减速50%",   "冷却 5s", (100, 180, 255)),
    ("✌  剪刀手 Peace",    "双线激光 — 两条水平激光0.5s","冷却 2s", (200,  80, 255)),
    ("👍  大拇指 Thumb Up","投弹 — 延时范围爆炸",         "冷却 4s", (80,  220, 120)),
]


class FloatingText:
    def __init__(self, text, x, y, color=(255, 220, 50), size=24):
        self.text  = text
        self.x     = float(x)
        self.y     = float(y)
        self.color = color
        self.timer = 0.0
        self.duration = 1.0
        self.font  = config.get_font(size, bold=True)
        # Bounce effect
        self._start_y = float(y)

    def update(self, dt):
        self.timer += dt
        frac = self.timer / self.duration
        # Ease out: fast upward start, slow down
        self.y = self._start_y - 60 * (frac ** 0.6)
        # Scale bounce on first frame
        if self.timer < 0.1:
            self._scale = 1.0 + 0.3 * (1.0 - self.timer / 0.1)
        else:
            self._scale = 1.0

    def done(self):
        return self.timer >= self.duration

    def draw(self, surface):
        alpha = int(255 * (1 - self.timer / self.duration))
        surf  = self.font.render(self.text, True, self.color)
        surf.set_alpha(alpha)
        if hasattr(self, '_scale') and self._scale != 1.0:
            w = int(surf.get_width() * self._scale)
            h = int(surf.get_height() * self._scale)
            surf = pygame.transform.scale(surf, (w, h))
            surface.blit(surf, (int(self.x - (w - surf.get_width()) // 2),
                                int(self.y - (h - surf.get_height()) // 2)))
        else:
            surface.blit(surf, (int(self.x), int(self.y)))


class Scene:
    def __init__(self, screenfx=None):
        self.player       = Player()
        self.zombies      = []
        self.attacks      = []
        self.floats       = []
        self.wave_timer   = 0.0
        self.game_over    = False
        self.intro        = True
        self.wave_flash_timer = 0.0
        self._intro_blink = 0.0

        self.particles = ParticleManager()
        self.screenfx  = screenfx

        # Hitstop
        self.hitstop = 0.0

        if _BG is None:
            _load_bg()

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
            z = Zombie(ztype, wave)
            self.zombies.append(z)
            # Spawn ground dust
            self.particles.emit_burst(
                z.x, config.SCREEN_H - 100, count=4, color=(100, 80, 60),
                speed=40, size=3, life=0.4, gravity=-50, spread=120, shape="square"
            )

        if wave % 3 == 0:
            self.zombies.append(Zombie("ELITE", wave))

        self.wave_flash_timer = 2.0

    def start_game(self):
        self.intro = False
        self._spawn_wave()

    def handle_gesture(self, gesture_name):
        if gesture_name == "NONE" or self.game_over or self.intro:
            return
        if not self.player.can_use(gesture_name):
            return
        cls = ATTACK_MAP.get(gesture_name)
        if cls:
            self.attacks.append(cls())
            self.player.use_skill(gesture_name)
            # Skill confirm flash
            if self.screenfx:
                self.screenfx.flash(color=(255, 220, 100), duration=0.04)

    def update(self, dt, confirmed_gesture=None):
        if self.intro or self.game_over:
            self._intro_blink += dt
            self.particles.update(dt)
            return

        # Hitstop — pause everything
        if self.hitstop > 0:
            self.hitstop -= dt
            self.particles.update(dt)
            return

        if confirmed_gesture:
            self.handle_gesture(confirmed_gesture)

        self.player.tick(dt)

        # Attacks — pass particle manager
        live_zombies = [z for z in self.zombies if not z.is_dead()]
        for atk in self.attacks:
            atk.update(dt, live_zombies, self.particles)
        self.attacks = [a for a in self.attacks if not a.done]

        # Zombies
        for z in self.zombies:
            z.update(dt)
            if not z.is_dead() and z.reached_left():
                self.player.take_damage()
                z.dead = True
                if self.screenfx:
                    self.screenfx.flash(color=(255, 50, 50), duration=0.1)
                    self.screenfx.damage_vignette(intensity=0.6, duration=0.5)
                    self.screenfx.shake(intensity=6, duration=0.15)

        # Collect kills
        for z in self.zombies:
            if z.is_dead() and not z.death_finished():
                pass
            elif z.is_dead() and z.death_finished() and z.score > 0:
                mult = min(self.player.combo, 3)
                was_killed = self.player.add_kill(z.score)
                label = f"+{z.score}"
                if mult > 1:
                    label += f" x{mult}"
                self.floats.append(FloatingText(label, z.x, z.y))
                # Death particles
                self.particles.emit_blood(z.x + z.w // 2, z.y + z.h // 2, count=10)
                # Hitstop on kill
                self.hitstop = 0.05
                if self.screenfx:
                    self.screenfx.shake(intensity=2, duration=0.08)
                    if mult >= 2:
                        self.screenfx.combo_glow(mult)
                z.score = 0

        self.zombies = [z for z in self.zombies if not z.death_finished()]

        # Floating texts
        for f in self.floats:
            f.update(dt)
        self.floats = [f for f in self.floats if not f.done()]

        # Particles
        self.particles.update(dt)

        # Wave progression
        self.wave_timer += dt
        if self.wave_timer >= config.WAVE_INTERVAL:
            self.wave_timer = 0.0
            self.player.wave += 1
            self._spawn_wave()

        if len(self.zombies) > config.MAX_ZOMBIES:
            self.zombies = self.zombies[:config.MAX_ZOMBIES]

        if self.wave_flash_timer > 0:
            self.wave_flash_timer -= dt

        if self.player.is_dead():
            self.game_over = True

    def draw(self, surface):
        if _BG is not None:
            surface.blit(_BG, (0, 0))
        else:
            surface.fill(config.COLORS["bg"])

        # Attacks
        for atk in self.attacks:
            atk.draw(surface)

        # Zombies
        for z in self.zombies:
            z.draw(surface)

        # Particles (behind floating text, over zombies)
        self.particles.draw(surface)

        # Floating texts
        for f in self.floats:
            f.draw(surface)

        # Wave flash
        if self.wave_flash_timer > 0:
            alpha = int(min(255, self.wave_flash_timer * 150))
            s = pygame.Surface((config.SCREEN_W, config.SCREEN_H), pygame.SRCALPHA)
            s.fill((255, 100, 50, alpha))
            surface.blit(s, (0, 0))
            font = config.get_font(72, bold=True)
            text = font.render(f"第 {self.player.wave} 波", True, (255, 220, 100))
            x = (config.SCREEN_W - text.get_width()) // 2
            y = (config.SCREEN_H - text.get_height()) // 2
            surface.blit(text, (x, y))

        # Intro screen
        if self.intro:
            self._draw_intro(surface)
            return

        # Game over
        if self.game_over:
            s = pygame.Surface((config.SCREEN_W, config.SCREEN_H), pygame.SRCALPHA)
            s.fill((0, 0, 0, 160))
            surface.blit(s, (0, 0))
            font_big = config.get_font(80, bold=True)
            font_sm  = config.get_font(36)
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
        for yy in range(0, config.SCREEN_H, 6):
            pygame.draw.line(surface, (0, 0, 0, 30), (0, yy), (config.SCREEN_W, yy))

        cx = config.SCREEN_W // 2
        font_title  = config.get_font(72, bold=True)
        font_sub    = config.get_font(26, bold=True)
        font_body   = config.get_font(22)
        font_hint   = config.get_font(28, bold=True)
        font_label  = config.get_font(20, bold=True)
        font_desc   = config.get_font(19)

        title = font_title.render("ZOMBIE GO DIE", True, (220, 50, 50))
        surface.blit(title, (cx - title.get_width() // 2, 40))
        sub = font_sub.render("用手势消灭僵尸！", True, (200, 180, 100))
        surface.blit(sub, (cx - sub.get_width() // 2, 125))
        pygame.draw.line(surface, (60, 60, 80), (80, 165), (config.SCREEN_W - 80, 165), 1)

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
        pygame.draw.line(surface, (60, 60, 80), (80, y + 4), (config.SCREEN_W - 80, y + 4), 1)
        y += 18

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

        if int(self._intro_blink * 2) % 2 == 0:
            prompt = font_hint.render("按 空格键 开始游戏", True, (255, 220, 50))
            surface.blit(prompt, (cx - prompt.get_width() // 2, config.SCREEN_H - 58))
