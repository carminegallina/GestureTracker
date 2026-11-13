from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import hypot
from typing import Dict, List

from .config import GestureConfig
from .models import LandmarkPoint


class Gesture(str, Enum):
    NONE = "none"
    MOVE = "move"
    PINCH = "pinch"
    FIST = "fist"
    THUMBS_UP = "thumbs_up"
    V_SIGN = "v_sign"
    TWO_FISTS = "two_fists"
    TWO_V_SIGNS = "two_v_signs"


@dataclass(frozen=True)
class GestureFrame:
    gesture: Gesture
    pointer: LandmarkPoint | None
    pinch_distance: float
    extended_fingers: Dict[str, bool]

    @property
    def can_point(self) -> bool:
        return self.gesture in {Gesture.MOVE, Gesture.PINCH} and self.pointer is not None


class HandLandmark:
    WRIST = 0
    THUMB_TIP = 4
    INDEX_MCP = 5
    INDEX_PIP = 6
    INDEX_TIP = 8
    MIDDLE_MCP = 9
    MIDDLE_PIP = 10
    MIDDLE_TIP = 12
    RING_PIP = 14
    RING_TIP = 16
    PINKY_PIP = 18
    PINKY_TIP = 20


class GestureDetector:
    def __init__(self, config: GestureConfig) -> None:
        self.config = config

    def detect(self, landmarks: List[LandmarkPoint]) -> GestureFrame:
        if len(landmarks) < 21:
            return GestureFrame(Gesture.NONE, None, 0.0, {})

        extended = self._extended_fingers(landmarks)
        pinch_distance = self._normalized_distance(
            landmarks, HandLandmark.THUMB_TIP, HandLandmark.INDEX_TIP
        )

        is_fist = self._is_fist(extended)
        is_thumbs_up = self._is_thumbs_up(landmarks, extended)
        is_v_sign = self._is_v_sign(extended)
        is_pinch = pinch_distance < self.config.pinch_threshold and not is_fist

        if is_thumbs_up:
            gesture = Gesture.THUMBS_UP
            pointer = None
        elif is_fist:
            gesture = Gesture.FIST
            pointer = None
        elif is_v_sign:
            gesture = Gesture.V_SIGN
            pointer = None
        elif is_pinch:
            gesture = Gesture.PINCH
            pointer = landmarks[HandLandmark.INDEX_TIP]
        elif extended.get("index", False):
            gesture = Gesture.MOVE
            pointer = landmarks[HandLandmark.INDEX_TIP]
        else:
            gesture = Gesture.NONE
            pointer = None

        return GestureFrame(
            gesture=gesture,
            pointer=pointer,
            pinch_distance=pinch_distance,
            extended_fingers=extended,
        )

    def _extended_fingers(self, landmarks: List[LandmarkPoint]) -> Dict[str, bool]:
        margin = self.config.finger_extension_margin
        return {
            "index": landmarks[HandLandmark.INDEX_TIP].y
            < landmarks[HandLandmark.INDEX_PIP].y - margin,
            "middle": landmarks[HandLandmark.MIDDLE_TIP].y
            < landmarks[HandLandmark.MIDDLE_PIP].y - margin,
            "ring": landmarks[HandLandmark.RING_TIP].y
            < landmarks[HandLandmark.RING_PIP].y - margin,
            "pinky": landmarks[HandLandmark.PINKY_TIP].y
            < landmarks[HandLandmark.PINKY_PIP].y - margin,
        }

    def _is_fist(self, extended: Dict[str, bool]) -> bool:
        tracked = ("index", "middle", "ring", "pinky")
        return all(not extended.get(name, False) for name in tracked)

    def _is_thumbs_up(
        self, landmarks: List[LandmarkPoint], extended: Dict[str, bool]
    ) -> bool:
        fingers_folded = self._is_fist(extended)
        thumb_tip = landmarks[HandLandmark.THUMB_TIP]
        wrist = landmarks[HandLandmark.WRIST]
        index_mcp = landmarks[HandLandmark.INDEX_MCP]
        middle_mcp = landmarks[HandLandmark.MIDDLE_MCP]

        thumb_is_high = thumb_tip.y < min(index_mcp.y, middle_mcp.y) - 0.06
        thumb_above_wrist = thumb_tip.y < wrist.y - 0.18
        return fingers_folded and thumb_is_high and thumb_above_wrist

    def _is_v_sign(self, extended: Dict[str, bool]) -> bool:
        return (
            extended.get("index", False)
            and extended.get("middle", False)
            and not extended.get("ring", False)
            and not extended.get("pinky", False)
        )

    def _normalized_distance(
        self, landmarks: List[LandmarkPoint], first: int, second: int
    ) -> float:
        scale = self._hand_scale(landmarks)
        return self._distance(landmarks[first], landmarks[second]) / scale

    def _hand_scale(self, landmarks: List[LandmarkPoint]) -> float:
        return max(
            self._distance(
                landmarks[HandLandmark.WRIST], landmarks[HandLandmark.MIDDLE_MCP]
            ),
            1e-6,
        )

    @staticmethod
    def _distance(first: LandmarkPoint, second: LandmarkPoint) -> float:
        return hypot(first.x - second.x, first.y - second.y)


def combine_gestures(frames: List[GestureFrame]) -> Gesture:
    gestures = [frame.gesture for frame in frames if frame.gesture != Gesture.NONE]

    if gestures.count(Gesture.FIST) >= 2:
        return Gesture.TWO_FISTS
    if gestures.count(Gesture.V_SIGN) >= 2:
        return Gesture.TWO_V_SIGNS

    for gesture in (
        Gesture.FIST,
        Gesture.THUMBS_UP,
        Gesture.V_SIGN,
        Gesture.PINCH,
        Gesture.MOVE,
    ):
        if gesture in gestures:
            return gesture

    return Gesture.NONE
