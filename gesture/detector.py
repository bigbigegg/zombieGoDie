import cv2
import mediapipe as mp


class HandDetector:
    def __init__(self, max_hands=1, detection_conf=0.7, tracking_conf=0.5):
        self._mp_hands = mp.solutions.hands
        self._mp_draw = mp.solutions.drawing_utils
        self._hands = self._mp_hands.Hands(
            max_num_hands=max_hands,
            min_detection_confidence=detection_conf,
            min_tracking_confidence=tracking_conf,
        )

    def update(self, frame_bgr):
        """
        Process a BGR camera frame.
        Returns (landmarks, annotated_frame):
          landmarks: list of 21 (x, y, z) normalized coords, or None if no hand found
          annotated_frame: BGR frame with skeleton drawn
        """
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        result = self._hands.process(rgb)
        rgb.flags.writeable = True

        annotated = frame_bgr.copy()

        if not result.multi_hand_landmarks:
            return None, annotated

        hand = result.multi_hand_landmarks[0]
        self._mp_draw.draw_landmarks(
            annotated, hand, self._mp_hands.HAND_CONNECTIONS
        )

        landmarks = [(lm.x, lm.y, lm.z) for lm in hand.landmark]
        return landmarks, annotated

    def release(self):
        self._hands.close()
