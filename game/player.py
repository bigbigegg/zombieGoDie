import config


class Player:
    def __init__(self):
        self.hp    = config.PLAYER_MAX_HP
        self.score = 0
        self.wave  = 1
        self._cds  = {g: 0.0 for g in config.CD}

        self.combo       = 0
        self.combo_timer = 0.0
        self.combo_window = 2.0  # seconds to keep combo alive

    def tick(self, dt):
        for g in self._cds:
            if self._cds[g] > 0:
                self._cds[g] = max(0.0, self._cds[g] - dt)

        if self.combo > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.combo = 0

    def can_use(self, gesture_name):
        return self._cds.get(gesture_name, 0.0) <= 0.0

    def use_skill(self, gesture_name):
        self._cds[gesture_name] = config.CD.get(gesture_name, 1.0)

    def cd_fraction(self, gesture_name):
        """Returns 0.0 (ready) to 1.0 (full cooldown)."""
        total = config.CD.get(gesture_name, 1.0)
        remaining = self._cds.get(gesture_name, 0.0)
        return remaining / total if total > 0 else 0.0

    def add_kill(self, score):
        self.combo += 1
        self.combo_timer = self.combo_window
        multiplier = min(self.combo, 3)
        self.score += score * multiplier
        return True

    def take_damage(self):
        self.hp = max(0, self.hp - 1)

    def is_dead(self):
        return self.hp <= 0
