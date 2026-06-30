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


DEBUG_CAM_W = 480
DEBUG_CAM_H = 360


def _draw_debug_overlay(surface, annotated_frame, raw, confirmed, debouncer, landmarks, clock):
    """Large camera window + gesture info panel shown when debug mode is on."""
    # Large camera feed — top-left
    cam_big = cv_frame_to_pygame(annotated_frame, (DEBUG_CAM_W, DEBUG_CAM_H))
    surface.blit(cam_big, (0, 50))

    panel_x = DEBUG_CAM_W + 10
    panel_y = 50
    panel_w = 340
    panel_h = DEBUG_CAM_H

    bg = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 180))
    surface.blit(bg, (panel_x, panel_y))

    font_title = pygame.font.SysFont("Courier", 18, bold=True)
    font_body  = pygame.font.SysFont("Courier", 15)

    YELLOW = (255, 220, 50)
    WHITE  = (220, 220, 220)
    GREEN  = (80, 220, 100)
    GRAY   = (140, 140, 140)

    y = panel_y + 8
    surface.blit(font_title.render("[ DEBUG MODE — D to toggle ]", True, YELLOW), (panel_x + 8, y))
    y += 26

    # FPS
    surface.blit(font_body.render(f"FPS       : {int(clock.get_fps())}", True, WHITE), (panel_x + 8, y))
    y += 20

    # Raw gesture
    raw_color = GREEN if raw.name != "NONE" else GRAY
    surface.blit(font_body.render(f"Raw       : {raw.name}", True, raw_color), (panel_x + 8, y))
    y += 20

    # Confirmed gesture
    conf_color = (255, 80, 80) if confirmed.name != "NONE" else GRAY
    surface.blit(font_body.render(f"Confirmed : {confirmed.name}", True, conf_color), (panel_x + 8, y))
    y += 20

    # Debounce history bar
    history = list(debouncer._history)
    bar_str = " ".join(g.name[:2] for g in history)
    surface.blit(font_body.render(f"Buffer    : {bar_str}", True, GRAY), (panel_x + 8, y))
    y += 28

    # Finger states
    if landmarks:
        from gesture.classifier import _finger_states
        ext = _finger_states(landmarks)
        names = ["Thumb", "Index", "Mid  ", "Ring ", "Pinky"]
        surface.blit(font_title.render("Finger states:", True, YELLOW), (panel_x + 8, y))
        y += 22
        for name, state in zip(names, ext):
            color = GREEN if state else (180, 60, 60)
            icon  = "UP  ▲" if state else "curl ▼"
            surface.blit(font_body.render(f"  {name} : {icon}", True, color), (panel_x + 8, y))
            y += 18
    else:
        surface.blit(font_title.render("No hand detected", True, (180, 60, 60)), (panel_x + 8, y))

    # Border
    pygame.draw.rect(surface, YELLOW, (panel_x, panel_y, panel_w, panel_h), 1)
    pygame.draw.rect(surface, YELLOW, (0, 50, DEBUG_CAM_W, DEBUG_CAM_H), 1)

    # Label
    label = font_title.render("D=hide debug", True, YELLOW)
    surface.blit(label, (4, 52))


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

    cam_surf      = None
    debug_mode    = True   # on by default for easy debugging
    last_annotated = None
    last_raw       = Gesture.NONE
    last_confirmed = Gesture.NONE
    last_landmarks = None

    font_fps = pygame.font.SysFont("Arial", 18)

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
                if event.key == pygame.K_d:
                    debug_mode = not debug_mode

        # --- Camera + Gesture ---
        confirmed_name = None
        confirmed      = Gesture.NONE
        if cap:
            ok, frame = cap.read()
            if ok:
                frame = cv2.flip(frame, 1)
                landmarks, annotated   = detector.update(frame)
                raw                    = classify(landmarks)
                confirmed              = debouncer.update(raw)

                last_annotated = annotated
                last_raw       = raw
                last_confirmed = confirmed
                last_landmarks = landmarks

                cam_surf = cv_frame_to_pygame(annotated, (config.CAM_W, config.CAM_H))

                if confirmed != Gesture.NONE:
                    confirmed_name = confirmed.name

        # --- Update ---
        scene.update(dt, confirmed_name)

        # --- Draw ---
        scene.draw(screen)
        hud.draw(screen, scene.player, cam_surf)

        if debug_mode and last_annotated is not None:
            _draw_debug_overlay(screen, last_annotated,
                                last_raw, last_confirmed,
                                debouncer, last_landmarks, clock)

        if not debug_mode:
            fps_text = font_fps.render(f"FPS {int(clock.get_fps())}", True, (120, 120, 120))
            screen.blit(fps_text, (8, config.SCREEN_H - 90))

        # Debug mode hint when off
        if not debug_mode:
            hint = font_fps.render("D = debug", True, (80, 80, 80))
            screen.blit(hint, (8, 54))

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
