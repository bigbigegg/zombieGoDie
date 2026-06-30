import sys
import cv2
import pygame
import numpy as np

import config
from gesture.detector import HandDetector
from gesture.classifier import classify, GestureDebouncer, Gesture, _finger_states
from game.scene import Scene
from game.hud import HUD

# Debug sidebar dimensions
DBG_W  = config.DEBUG_PANEL_W
DBG_H  = config.SCREEN_H
CAM_W  = DBG_W
CAM_H  = DBG_W * 3 // 4   # 4:3 aspect → 300×225


def cv_frame_to_pygame(frame_bgr, w, h):
    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    frame_rgb = cv2.resize(frame_rgb, (w, h))
    return pygame.surfarray.make_surface(np.transpose(frame_rgb, (1, 0, 2)))


def _draw_debug_panel(panel, annotated_frame, raw, confirmed, debouncer, landmarks, clock):
    """Render everything into the fixed-size debug sidebar surface."""
    panel.fill((12, 12, 20))

    YELLOW = (255, 220, 50)
    GREEN  = (80, 220, 100)
    RED    = (220, 80, 80)
    WHITE  = (220, 220, 220)
    GRAY   = (120, 120, 130)

    font_title = config.get_font(14, bold=True)
    font_body  = config.get_font(13)

    # Title bar
    pygame.draw.rect(panel, (30, 30, 50), (0, 0, DBG_W, 26))
    panel.blit(font_title.render("调试图层  [D] 开关", True, YELLOW), (8, 5))

    y = 30

    # Camera feed
    if annotated_frame is not None:
        cam_surf = cv_frame_to_pygame(annotated_frame, CAM_W, CAM_H)
        panel.blit(cam_surf, (0, y))
        pygame.draw.rect(panel, YELLOW, (0, y, CAM_W, CAM_H), 1)
        y += CAM_H + 8
    else:
        pygame.draw.rect(panel, GRAY, (0, y, CAM_W, CAM_H), 1)
        no_cam = font_title.render("No camera", True, GRAY)
        panel.blit(no_cam, ((DBG_W - no_cam.get_width()) // 2, y + CAM_H // 2 - 8))
        y += CAM_H + 8

    # Divider
    pygame.draw.line(panel, (40, 40, 60), (0, y), (DBG_W, y))
    y += 6

    # FPS
    panel.blit(font_body.render(f"帧率  {int(clock.get_fps())}", True, WHITE), (8, y))
    y += 18

    # Raw gesture
    rc = GREEN if raw.name != "NONE" else GRAY
    panel.blit(font_body.render(f"当前  {raw.name}", True, rc), (8, y))
    y += 18

    # Confirmed gesture — highlight box when active
    if confirmed.name != "NONE":
        pygame.draw.rect(panel, (60, 20, 20), (4, y - 2, DBG_W - 8, 20))
    cc = RED if confirmed.name != "NONE" else GRAY
    panel.blit(font_body.render(f"触发  {confirmed.name}", True, cc), (8, y))
    y += 22

    # Debounce buffer
    history = list(debouncer._history)
    bar_str  = " ".join(g.name[:2] for g in history)
    panel.blit(font_body.render(f"缓存  {bar_str}", True, GRAY), (8, y))
    y += 22

    # Divider
    pygame.draw.line(panel, (40, 40, 60), (0, y), (DBG_W, y))
    y += 8

    # Finger states
    panel.blit(font_title.render("手指状态", True, YELLOW), (8, y))
    y += 18

    if landmarks:
        ext   = _finger_states(landmarks)
        names = ["拇指", "食指", "中指", "无名", "小指"]
        for name, state in zip(names, ext):
            color = GREEN if state else RED
            icon  = "伸 ▲" if state else "曲 ▼"
            panel.blit(font_body.render(f"  {name}  {icon}", True, color), (8, y))
            y += 17
    else:
        panel.blit(font_title.render("  未检测到手部", True, RED), (8, y))

    # Right border separator
    pygame.draw.line(panel, (50, 50, 80), (DBG_W - 1, 0), (DBG_W - 1, DBG_H), 1)


def main():
    pygame.init()

    # Window resizes based on debug mode
    debug_mode = True
    win_w = config.SCREEN_W + DBG_W if debug_mode else config.SCREEN_W

    screen = pygame.display.set_mode((win_w, config.SCREEN_H))
    pygame.display.set_caption("ZombieGoDie")
    clock = pygame.time.Clock()

    # Offscreen surface for the game — always SCREEN_W wide
    game_surf = pygame.Surface((config.SCREEN_W, config.SCREEN_H))
    dbg_panel = pygame.Surface((DBG_W, DBG_H))

    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("[ERROR] Cannot open camera.")
        cap = None

    detector  = HandDetector() if cap else None
    debouncer = GestureDebouncer()
    scene     = Scene()
    hud       = HUD()

    last_annotated = None
    last_raw       = Gesture.NONE
    last_confirmed = Gesture.NONE
    last_landmarks = None

    font_hint = config.get_font(16)

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
                    new_w = config.SCREEN_W + DBG_W if debug_mode else config.SCREEN_W
                    screen = pygame.display.set_mode((new_w, config.SCREEN_H))
                if event.key == pygame.K_SPACE and scene.intro:
                    scene.start_game()

        # --- Camera + Gesture ---
        confirmed_name = None
        confirmed      = Gesture.NONE
        if cap:
            ok, frame = cap.read()
            if ok:
                frame = cv2.flip(frame, 1)
                landmarks, annotated = detector.update(frame)
                raw       = classify(landmarks)
                confirmed = debouncer.update(raw)

                last_annotated = annotated
                last_raw       = raw
                last_confirmed = confirmed
                last_landmarks = landmarks

                if confirmed != Gesture.NONE:
                    confirmed_name = confirmed.name

        # --- Update ---
        scene.update(dt, confirmed_name)

        # --- Draw game to offscreen surface ---
        scene.draw(game_surf)
        hud.draw(game_surf, scene.player)

        if not debug_mode:
            fps = font_hint.render(f"帧率 {int(clock.get_fps())}  D=调试", True, (80, 80, 80))
            game_surf.blit(fps, (8, config.SCREEN_H - 88))

        # --- Compose final window ---
        screen.fill((0, 0, 0))
        if debug_mode:
            _draw_debug_panel(dbg_panel, last_annotated,
                              last_raw, last_confirmed,
                              debouncer, last_landmarks, clock)
            screen.blit(dbg_panel, (0, 0))
            screen.blit(game_surf, (DBG_W, 0))
        else:
            screen.blit(game_surf, (0, 0))

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
