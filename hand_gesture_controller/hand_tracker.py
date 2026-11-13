from __future__ import annotations

import time
from pathlib import Path
from typing import Optional

import cv2
import mediapipe as mp

from .config import TrackerConfig
from .model_assets import HAND_LANDMARKER_MODEL, HAND_LANDMARKER_URL
from .models import HandResult, LandmarkPoint


class HandTracker:
    def __init__(self, config: TrackerConfig) -> None:
        self._config = config
        self._backend = "legacy" if hasattr(mp, "solutions") else "tasks"
        self._timestamp_ms = 0
        self._recent_hands: list[tuple[HandResult, float]] = []

        if self._backend == "legacy":
            self._hands_solution = mp.solutions.hands
            self._drawing = mp.solutions.drawing_utils
            self._drawing_styles = mp.solutions.drawing_styles
            self._hands = self._hands_solution.Hands(
                static_image_mode=False,
                max_num_hands=config.max_num_hands,
                model_complexity=1,
                min_detection_confidence=config.min_detection_confidence,
                min_tracking_confidence=config.min_tracking_confidence,
            )
            return

        model_path = Path(config.model_path) if config.model_path else HAND_LANDMARKER_MODEL
        if not model_path.exists():
            raise RuntimeError(
                "MediaPipe Tasks requires a local hand landmark model.\n"
                f"Missing: {model_path}\n"
                "Run this once from the project root:\n"
                "  python -m hand_gesture_controller.download_model\n"
                f"Model source: {HAND_LANDMARKER_URL}"
            )

        vision = mp.tasks.vision
        options = vision.HandLandmarkerOptions(
            base_options=mp.tasks.BaseOptions(model_asset_path=str(model_path)),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=config.max_num_hands,
            min_hand_detection_confidence=config.min_detection_confidence,
            min_hand_presence_confidence=config.min_detection_confidence,
            min_tracking_confidence=config.min_tracking_confidence,
        )
        self._landmarker = vision.HandLandmarker.create_from_options(options)
        self._drawing = vision.drawing_utils
        self._drawing_styles = vision.drawing_styles
        self._connections = vision.HandLandmarksConnections

    def process(self, frame_bgr) -> Optional[HandResult]:
        hands = self.process_many(frame_bgr)
        return hands[0] if hands else None

    def process_many(self, frame_bgr) -> list[HandResult]:
        if self._backend == "legacy":
            detected = self._process_legacy_many(frame_bgr)
        else:
            detected = self._process_tasks(frame_bgr)
        return self._stabilize_hands(detected, time.monotonic())

    def _process_legacy_many(self, frame_bgr) -> list[HandResult]:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        rgb.flags.writeable = False
        result = self._hands.process(rgb)

        if not result.multi_hand_landmarks:
            return []

        hands = []
        for index, raw in enumerate(result.multi_hand_landmarks):
            handedness = "unknown"
            if result.multi_handedness and index < len(result.multi_handedness):
                handedness = result.multi_handedness[index].classification[0].label
            handedness = self._display_handedness(handedness)

            landmarks = [
                LandmarkPoint(point.x, point.y, point.z) for point in raw.landmark
            ]
            hands.append(
                HandResult(
                    landmarks=landmarks,
                    handedness=handedness,
                    raw_landmarks=raw,
                )
            )
        return hands

    def _process_tasks(self, frame_bgr) -> list[HandResult]:
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
        result = self._landmarker.detect_for_video(mp_image, self._next_timestamp_ms())

        if not result.hand_landmarks:
            return []

        hands = []
        for index, raw in enumerate(result.hand_landmarks):
            handedness = "unknown"
            if result.handedness and index < len(result.handedness):
                category = result.handedness[index][0]
                handedness = getattr(
                    category,
                    "category_name",
                    getattr(category, "display_name", "unknown"),
                )
            handedness = self._display_handedness(handedness)

            landmarks = [
                LandmarkPoint(point.x, point.y, getattr(point, "z", 0.0))
                for point in raw
            ]
            hands.append(
                HandResult(
                    landmarks=landmarks,
                    handedness=handedness,
                    raw_landmarks=raw,
                )
            )
        return hands

    def _stabilize_hands(
        self, detected_hands: list[HandResult], now: float
    ) -> list[HandResult]:
        if not detected_hands:
            self._recent_hands = []
            return []

        matched_recent: set[int] = set()
        stabilized: list[HandResult] = []
        next_recent: list[tuple[HandResult, float]] = []

        for hand in detected_hands:
            match_index = self._find_recent_match(hand, matched_recent)
            if match_index is not None:
                matched_recent.add(match_index)
            stabilized.append(hand)
            next_recent.append((hand, now))

        for index, (recent_hand, seen_at) in enumerate(self._recent_hands):
            if index in matched_recent:
                continue
            if len(stabilized) >= self._config.max_num_hands:
                break
            if now - seen_at <= self._config.lost_hand_grace_seconds:
                stabilized.append(self._mark_held(recent_hand))
                next_recent.append((recent_hand, seen_at))

        self._recent_hands = next_recent[: self._config.max_num_hands]
        return stabilized[: self._config.max_num_hands]

    def _find_recent_match(
        self, hand: HandResult, matched_recent: set[int]
    ) -> int | None:
        hand_center = self._hand_center(hand)
        best_index = None
        best_distance = self._config.hand_match_max_distance

        for index, (recent_hand, _) in enumerate(self._recent_hands):
            if index in matched_recent:
                continue
            if (
                hand.handedness != "unknown"
                and recent_hand.handedness != "unknown"
                and hand.handedness != recent_hand.handedness
            ):
                continue

            distance = self._distance(hand_center, self._hand_center(recent_hand))
            if distance < best_distance:
                best_index = index
                best_distance = distance

        return best_index

    def _display_handedness(self, handedness: str) -> str:
        if not self._config.flip_handedness:
            return handedness
        if handedness == "Left":
            return "Right"
        if handedness == "Right":
            return "Left"
        return handedness

    @staticmethod
    def _hand_center(hand: HandResult) -> tuple[float, float]:
        count = max(len(hand.landmarks), 1)
        return (
            sum(point.x for point in hand.landmarks) / count,
            sum(point.y for point in hand.landmarks) / count,
        )

    @staticmethod
    def _distance(first: tuple[float, float], second: tuple[float, float]) -> float:
        return ((first[0] - second[0]) ** 2 + (first[1] - second[1]) ** 2) ** 0.5

    @staticmethod
    def _mark_held(hand: HandResult) -> HandResult:
        return HandResult(
            landmarks=hand.landmarks,
            handedness=hand.handedness,
            raw_landmarks=hand.raw_landmarks,
            is_tracked=False,
        )

    def _next_timestamp_ms(self) -> int:
        timestamp_ms = int(time.monotonic() * 1000)
        if timestamp_ms <= self._timestamp_ms:
            timestamp_ms = self._timestamp_ms + 1
        self._timestamp_ms = timestamp_ms
        return timestamp_ms

    def draw(self, frame_bgr, hand: Optional[HandResult]) -> None:
        if hand is None:
            return

        if self._backend == "legacy":
            self._drawing.draw_landmarks(
                frame_bgr,
                hand.raw_landmarks,
                self._hands_solution.HAND_CONNECTIONS,
                self._drawing_styles.get_default_hand_landmarks_style(),
                self._drawing_styles.get_default_hand_connections_style(),
            )
            return

        self._drawing.draw_landmarks(
            frame_bgr,
            hand.raw_landmarks,
            self._connections.HAND_CONNECTIONS,
            self._drawing_styles.get_default_hand_landmarks_style(),
            self._drawing_styles.get_default_hand_connections_style(),
        )

    def draw_many(self, frame_bgr, hands: list[HandResult]) -> None:
        for hand in hands:
            self.draw(frame_bgr, hand)

    def close(self) -> None:
        if self._backend == "legacy":
            self._hands.close()
        else:
            self._landmarker.close()
