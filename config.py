SCREEN_W = 1280
SCREEN_H = 720
FPS = 60

CAM_W = 240
CAM_H = 180
CAM_MARGIN = 10

GESTURE_CONFIRM_FRAMES = 5

CD = {
    "FIST":     3.0,
    "POINT":    1.0,
    "OPEN":     5.0,
    "PEACE":    2.0,
    "THUMBSUP": 4.0,
}

WAVE_INTERVAL = 30
ZOMBIE_SPEED_SCALE = 1.1
ZOMBIE_COUNT_STEP = 2
ZOMBIE_COUNT_BASE = 4
MAX_ZOMBIES = 10

PLAYER_MAX_HP = 5

ZOMBIE_TYPES = {
    "NORMAL": {"hp": 1, "speed": 80,  "score": 10, "color": (60, 179, 113),  "w": 36, "h": 52},
    "FAT":    {"hp": 3, "speed": 50,  "score": 30, "color": (139, 90,  43),  "w": 52, "h": 60},
    "ELITE":  {"hp": 8, "speed": 100, "score": 80, "color": (178, 34,  34),  "w": 44, "h": 60},
    "FAST":   {"hp": 1, "speed": 160, "score": 20, "color": (100, 149, 237), "w": 28, "h": 48},
}

COLORS = {
    "bg":         (20,  20,  30),
    "hud_bg":     (10,  10,  20),
    "hp_full":    (220, 50,  50),
    "hp_empty":   (60,  20,  20),
    "cd_ready":   (80,  200, 120),
    "cd_cooling": (60,  60,  80),
    "text":       (220, 220, 220),
    "combo":      (255, 200, 50),
    "wave_flash": (255, 100, 50),
    "freeze":     (100, 180, 255),
}
