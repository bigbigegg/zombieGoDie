import pygame
import config

SKILL_LABELS = {
    "FIST":     ("✊", "拳头"),
    "POINT":    ("☝", "食指"),
    "OPEN":     ("✋", "手掌"),
    "PEACE":    ("✌", "剪刀"),
    "THUMBSUP": ("👍", "拇指"),
}


class HUD:
    def __init__(self):
        self.font_lg = pygame.font.SysFont("Arial", 28, bold=True)
        self.font_md = pygame.font.SysFont("Arial", 20)
        self.font_sm = pygame.font.SysFont("Arial", 16)

    def draw(self, surface, player):
        self._draw_top_bar(surface, player)
        self._draw_skill_bar(surface, player)

    def _draw_top_bar(self, surface, player):
        bar_h = 50
        pygame.draw.rect(surface, config.COLORS["hud_bg"], (0, 0, config.SCREEN_W, bar_h))

        # HP hearts
        hp_x = 12
        for i in range(config.PLAYER_MAX_HP):
            color = config.COLORS["hp_full"] if i < player.hp else config.COLORS["hp_empty"]
            pygame.draw.rect(surface, color, (hp_x + i * 32, 12, 26, 26), border_radius=4)

        # Wave
        wave_text = self.font_lg.render(f"波次  {player.wave}", True, config.COLORS["text"])
        surface.blit(wave_text, (config.SCREEN_W // 2 - wave_text.get_width() // 2, 10))

        # Score
        score_text = self.font_lg.render(f"得分  {player.score}", True, config.COLORS["text"])
        surface.blit(score_text, (config.SCREEN_W - score_text.get_width() - 16, 10))

        # Combo
        if player.combo >= 2:
            combo_text = self.font_lg.render(f"连击 x{min(player.combo, 3)}!", True, config.COLORS["combo"])
            surface.blit(combo_text, (config.SCREEN_W // 2 - combo_text.get_width() // 2 + 160, 10))

    def _draw_skill_bar(self, surface, player):
        bar_h  = 60
        bar_y  = config.SCREEN_H - bar_h
        pygame.draw.rect(surface, config.COLORS["hud_bg"],
                         (0, bar_y, config.SCREEN_W, bar_h))

        skills   = list(config.CD.keys())
        slot_w   = 140
        total_w  = slot_w * len(skills)
        start_x  = (config.SCREEN_W - total_w) // 2

        for i, skill in enumerate(skills):
            x = start_x + i * slot_w
            frac = player.cd_fraction(skill)
            ready = frac <= 0.0

            # Background slot
            slot_color = config.COLORS["cd_ready"] if ready else config.COLORS["cd_cooling"]
            pygame.draw.rect(surface, slot_color,
                             (x + 4, bar_y + 6, slot_w - 8, bar_h - 12), border_radius=6)

            # CD progress overlay (dark)
            if not ready:
                fill_h = int((bar_h - 12) * frac)
                pygame.draw.rect(surface, (20, 20, 30),
                                 (x + 4, bar_y + 6, slot_w - 8, fill_h), border_radius=6)

            # Label
            _, label = SKILL_LABELS.get(skill, ("?", skill))
            text = self.font_sm.render(label, True, (240, 240, 240))
            surface.blit(text, (x + (slot_w - text.get_width()) // 2, bar_y + 8))

            # CD remaining seconds
            if not ready:
                cd_total = config.CD[skill]
                remaining = frac * cd_total
                cd_text = self.font_sm.render(f"{remaining:.1f}秒", True, (180, 180, 200))
                surface.blit(cd_text, (x + (slot_w - cd_text.get_width()) // 2, bar_y + 36))

