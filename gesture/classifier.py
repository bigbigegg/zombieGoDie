from collections import deque
from enum import Enum, auto

import config


class Gesture(Enum):
    NONE     = auto()
    FIST     = auto()   # 拳头 → 冲击波
    POINT    = auto()   # 食指指向 → 精准射击
    OPEN     = auto()   # 张开手掌 → 冰冻术
    PEACE    = auto()   # 剪刀手 → 双线激光
    THUMBSUP = auto()   # 大拇指朝上 → 投弹


# MediaPipe hand landmark indices
TIP   = [4, 8, 12, 16, 20]   # thumb, index, middle, ring, pinky tips
PIP   = [3, 6, 10, 14, 18]   # second joints (PIP for fingers, IP for thumb)
MCP   = [2, 5, 9,  13, 17]   # knuckle joints


def _finger_states(lm):
    """Return list of 5 booleans: True = finger extended."""
    extended = []

    # Thumb: compare x-axis (horizontal), accounting for hand orientation
    # Use tip vs MCP x distance vs wrist (lm[0]) to determine direction
    wrist_x = lm[0][0]
    thumb_mcp_x = lm[2][0]
    thumb_tip_x = lm[4][0]
    # If thumb MCP is to the right of wrist, hand faces right; thumb extends further right
    if thumb_mcp_x > wrist_x:
        extended.append(thumb_tip_x > thumb_mcp_x)
    else:
        extended.append(thumb_tip_x < thumb_mcp_x)

    # Other 4 fingers: tip y < PIP y means extended (y increases downward)
    for i in range(1, 5):
        extended.append(lm[TIP[i]][1] < lm[PIP[i]][1])

    return extended  # [thumb, index, middle, ring, pinky]


def classify(landmarks):
    """
    Classify hand landmarks into a Gesture enum.
    landmarks: list of 21 (x, y, z) tuples (normalized 0-1)
    """
    if landmarks is None:
        return Gesture.NONE

    lm = landmarks
    ext = _finger_states(lm)
    thumb, index, middle, ring, pinky = ext

    # Open hand: all 5 extended
    if all(ext):
        return Gesture.OPEN

    # Fist: all 4 fingers curled (thumb ignored)
    if not index and not middle and not ring and not pinky:
        return Gesture.FIST

    # Thumbs up: only thumb extended, hand roughly vertical
    # Additional check: index tip below index MCP (definitely curled)
    if thumb and not index and not middle and not ring and not pinky:
        return Gesture.THUMBSUP

    # Peace / Scissors: index + middle extended, ring + pinky curled
    if not thumb and index and middle and not ring and not pinky:
        return Gesture.PEACE

    # Point: only index extended
    if not thumb and index and not middle and not ring and not pinky:
        return Gesture.POINT

    return Gesture.NONE


class GestureDebouncer:
    """Requires N consecutive identical gestures before firing a confirmed gesture."""

    def __init__(self, n=None):
        self._n = n if n is not None else config.GESTURE_CONFIRM_FRAMES
        self._history = deque(maxlen=self._n)
        self._last_confirmed = Gesture.NONE

    def update(self, gesture):
        """
        Feed the latest raw gesture.
        Returns the confirmed gesture if stable for N frames, else Gesture.NONE.
        """
        self._history.append(gesture)

        if len(self._history) < self._n:
            return Gesture.NONE

        if len(set(self._history)) == 1:
            confirmed = self._history[0]
            if confirmed != self._last_confirmed:
                self._last_confirmed = confirmed
                return confirmed

        return Gesture.NONE

    @property
    def current_raw(self):
        return self._history[-1] if self._history else Gesture.NONE
