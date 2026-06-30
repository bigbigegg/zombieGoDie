"""Standalone gesture recognition tester. Press Q to quit."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import cv2
from gesture.detector import HandDetector
from gesture.classifier import classify, GestureDebouncer, Gesture

LABELS = {
    Gesture.NONE:     ("NONE",     (150, 150, 150)),
    Gesture.FIST:     ("FIST",     (50,  50,  220)),
    Gesture.POINT:    ("POINT",    (50,  200, 50)),
    Gesture.OPEN:     ("OPEN",     (220, 180, 50)),
    Gesture.PEACE:    ("PEACE",    (200, 50,  200)),
    Gesture.THUMBSUP: ("THUMBSUP", (50,  200, 200)),
}

def main():
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Cannot open camera")
        return

    detector  = HandDetector()
    debouncer = GestureDebouncer()

    while True:
        ok, frame = cap.read()
        if not ok:
            break

        frame = cv2.flip(frame, 1)
        landmarks, annotated = detector.update(frame)

        raw       = classify(landmarks)
        confirmed = debouncer.update(raw)

        raw_text, raw_color           = LABELS[raw]
        confirmed_text, confirm_color = LABELS[confirmed if confirmed != Gesture.NONE else raw]

        cv2.putText(annotated, f"Raw: {raw_text}", (10, 40),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, raw_color, 2)
        cv2.putText(annotated, f"Confirmed: {confirmed_text}", (10, 90),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, confirm_color, 3)

        cv2.imshow("Gesture Test — Q to quit", annotated)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    detector.release()
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
