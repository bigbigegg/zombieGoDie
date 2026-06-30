"""Asset loader — loads and caches pixel art sprites from the assets directory."""
import os
import pygame

_SPRITE_CACHE = {}

_ASSET_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "sprites")

_ZOMBIE_FRAME_MAP = {
    "NORMAL": ("normal", [(72, 85, 51)]),       # green zombie
    "FAT":    ("fat",    [(64, 77, 47)]),        # alt zombie/darker
    "ELITE":  ("elite",  [(70, 86, 52)]),        # skeleton
    "FAST":   ("normal", [(72, 100, 180, 100)]), # blue-tinted normal zombie
}

DEATH_FRAMES = None


def _load_png(path, scale=1.0):
    """Load a PNG and return a list of scaled frames."""
    surf = pygame.image.load(path).convert_alpha()
    if scale != 1.0:
        w = int(surf.get_width() * scale)
        h = int(surf.get_height() * scale)
        surf = pygame.transform.scale(surf, (w, h))
    return surf


def _load_frames_dir(ztype_dir, count=8):
    """Load walk_{0..count-1}.png from the given subdirectory."""
    base = os.path.join(_ASSET_DIR, "zombie", ztype_dir)
    frames = []
    for i in range(count):
        path = os.path.join(base, f"walk_{i}.png")
        if os.path.exists(path):
            frames.append(path)
    return frames


def _recolor_surface(surf, tint_color):
    """Multiply-tint a surface by a target RGB or RGBA color."""
    if len(tint_color) == 3:
        tint_color = tint_color + (255,)
    r, g, b, a = tint_color
    from pygame import BLEND_MULT, BLEND_ADD
    color_surf = pygame.Surface(surf.get_size(), pygame.SRCALPHA)
    color_surf.fill((r, g, b, 255))
    result = surf.copy()
    result.blit(color_surf, (0, 0), special_flags=BLEND_MULT)
    return result


def get_zombie_frames(ztype, target_h=None):
    """Return a list of pygame Surfaces (walk animation frames) for a zombie type."""
    cache_key = f"zombie_{ztype}_{target_h}"
    if cache_key in _SPRITE_CACHE:
        return _SPRITE_CACHE[cache_key]

    # Determine frame source directory and tint color
    dir_name, tints = _ZOMBIE_FRAME_MAP.get(ztype, ("normal", [(72, 85, 51)]))
    paths = _load_frames_dir(dir_name)

    if not paths:
        return None

    frames = []
    for p in paths:
        surf = _load_png(p)
        if tint_color := tints[0]:
            surf = _recolor_surface(surf, tint_color)
        if target_h and surf.get_height() != target_h:
            scale = target_h / surf.get_height()
            w = int(surf.get_width() * scale)
            surf = pygame.transform.scale(surf, (w, int(target_h)))
        frames.append(surf)

    _SPRITE_CACHE[cache_key] = frames
    return frames


def get_death_frames(target_h=None):
    """Return a simple pixel-explosion death animation (procedural)."""
    # Generate 4 frames of expanding orange/red particles
    frames = []
    for i in range(4):
        size = int(target_h * 0.8) if target_h else 48
        s = pygame.Surface((size, size), pygame.SRCALPHA)
        progress = (i + 1) / 4
        radius = int(size * 0.4 * progress)
        if radius > 0:
            pygame.draw.circle(s, (255, 200, 50, 220), (size // 2, size // 2), radius)
            pygame.draw.circle(s, (255, 100, 20, 180), (size // 2, size // 2), max(1, radius - 4))
        frames.append(s)
    return frames
