import sys
import cv2
import pygame
import numpy as np

import config
from gesture.detector import HandDetector
from gesture.classifier import classify, GestureDebouncer, Gesture
from game.scene import Scene
from game.hud import HUD


def cv_frame_to_pygame(frame_bgr, size):
    """Convert OpenCV BGR frame to a scaled Pygame Surface."""
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    frame_rgb = cv2.resize(frame_rgb, size)
    # OpenCV gives (H,W,3); Pygame wants (W,H,3) via surfarray
    surf = pygame.surfarray.make_surface(np.transpose(frame_rgb, (1, 0, 2)))
    return surf


def main():
    pygame.init()
    screen = pygame.display.set_mode((config.SCREEN_W, config.SCREEN_H))
    pygame.display.set_caption("ZombieGoDie")
    clock = pygame.time.Clock()

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot open camera. Running without gesture input.")
        cap = None

    detector  = HandDetector() if cap else None
    debouncer = GestureDebouncer()
    scene     = Scene()
    hud       = HUD()

    cam_surf  = None
    font_fps  = pygame.font.SysFont("Arial", 18)

    while True:
        dt = clock.tick(config.FPS) / 1000.0

        # --- Events ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                _quit(cap, detector)
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    _quit(cap, detector)
                if event.key == pygame.K_r and scene.game_over:
                    scene = Scene()

        # --- Camera + Gesture ---
        confirmed_name = None
        if cap:
            ok, frame = cap.read()
            if ok:
                frame = cv2.flip(frame, 1)
                landmarks, annotated = detector.update(frame)
                raw       = classify(landmarks)
                confirmed = debouncer.update(raw)

                cam_surf  = cv_frame_to_pygame(annotated, (config.CAM_W, config.CAM_H))

                if confirmed != Gesture.NONE:
                    confirmed_name = confirmed.name  # e.g. "FIST"

        # --- Update ---
        scene.update(dt, confirmed_name)

        # --- Draw ---
        scene.draw(screen)
        hud.draw(screen, scene.player, cam_surf)

        fps_text = font_fps.render(f"FPS {int(clock.get_fps())}", True, (120, 120, 120))
        screen.blit(fps_text, (8, config.SCREEN_H - 90))

        pygame.display.flip()

    _quit(cap, detector)


def _quit(cap, detector):
    if detector:
        detector.release()
    if cap:
        cap.release()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
