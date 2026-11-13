from __future__ import annotations

import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable

import cv2

from .config import CameraConfig


class CameraState(str, Enum):
    OPEN = "open"
    UNAVAILABLE = "unavailable"
    PAUSED = "paused"
    RETRY_WAIT = "retry_wait"


@dataclass(frozen=True)
class CameraStatus:
    state: CameraState
    message: str
    detail: str = ""
    retry_in_seconds: float = 0.0

    @property
    def available(self) -> bool:
        return self.state == CameraState.OPEN


class CameraManager:
    def __init__(
        self,
        config: CameraConfig,
        capture_factory: Callable[..., object] | None = None,
    ) -> None:
        self.config = config
        self._capture_factory = capture_factory or cv2.VideoCapture
        self._capture = None
        self._pending_frame = None
        self._active_index = config.index
        self._paused = False
        self._next_retry_at = 0.0
        self._last_log_message = ""
        self.status = CameraStatus(
            CameraState.UNAVAILABLE,
            "Camera not opened yet",
        )

    def set_paused(self, paused: bool) -> None:
        self._paused = paused
        if paused and self.config.release_on_pause:
            self.release()
            self.status = CameraStatus(
                CameraState.PAUSED,
                "PAUSED - webcam released",
                "Press SPACE to retry/resume.",
            )
        elif not paused:
            self._next_retry_at = 0.0

    def read(self, now: float | None = None):
        now = time.monotonic() if now is None else now

        if self._paused and self.config.release_on_pause:
            self.release()
            self.status = CameraStatus(
                CameraState.PAUSED,
                "PAUSED - webcam released",
                "Press SPACE to retry/resume.",
            )
            return None

        if self._capture is None:
            if now < self._next_retry_at:
                self.status = CameraStatus(
                    CameraState.RETRY_WAIT,
                    "Webcam unavailable or busy",
                    _busy_camera_help(),
                    retry_in_seconds=max(0.0, self._next_retry_at - now),
                )
                return None
            self._open(now)
            if self._capture is None:
                return None

        if self._pending_frame is not None:
            ok = True
            frame = self._pending_frame
            self._pending_frame = None
        else:
            ok, frame = self._capture.read()
        if not ok or frame is None:
            self._mark_unavailable(
                now,
                f"Camera index {self._active_index} did not return a valid frame",
                release=True,
            )
            return None

        if self.config.mirror:
            frame = cv2.flip(frame, 1)

        self.status = CameraStatus(
            CameraState.OPEN,
            f"Camera {self._active_index} active",
        )
        return frame

    def retry_now(self) -> None:
        self._next_retry_at = 0.0

    def release(self) -> None:
        if self._capture is not None:
            try:
                self._capture.release()
            finally:
                self._capture = None
                self._pending_frame = None

    def close(self) -> None:
        self.release()

    def _open(self, now: float) -> None:
        self.release()
        errors = []
        for index in self._candidate_indices():
            try:
                capture = self._create_capture(index)
            except Exception as exc:
                errors.append(f"index {index}: open failed ({exc})")
                continue

            capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.config.width)
            capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.config.height)

            if not capture.isOpened():
                _release_capture(capture)
                errors.append(f"index {index}: not opened")
                continue

            ok, frame = self._probe_frame(capture)
            if not ok or frame is None:
                _release_capture(capture)
                errors.append(f"index {index}: no valid frame")
                continue

            self._capture = capture
            self._pending_frame = frame
            self._active_index = index
            self.status = CameraStatus(
                CameraState.OPEN,
                f"Camera {index} active",
            )
            suffix = "" if index == self.config.index else " via fallback"
            self._log_once(f"[camera] Camera {index} opened{suffix}.")
            return

        detail = "; ".join(errors) if errors else "No camera indices configured"
        self._mark_unavailable(
            now,
            f"Cannot open a usable webcam ({detail})",
            release=True,
        )

    def _create_capture(self, index: int):
        if self.config.backend is None:
            return self._capture_factory(index)
        return self._capture_factory(index, self.config.backend)

    def _candidate_indices(self) -> list[int]:
        indices = [self.config.index]
        if self.config.auto_fallback:
            indices.extend(self.config.fallback_indices)

        unique_indices = []
        for index in indices:
            if index not in unique_indices:
                unique_indices.append(index)
        return unique_indices

    def _probe_frame(self, capture) -> tuple[bool, object | None]:
        attempts = max(1, self.config.probe_frame_attempts)
        for _ in range(attempts):
            ok, frame = capture.read()
            if ok and frame is not None:
                return True, frame
        return False, None

    def _mark_unavailable(
        self,
        now: float,
        message: str,
        *,
        release: bool,
    ) -> None:
        if release:
            self.release()
        self._next_retry_at = now + self.config.retry_interval_seconds
        self.status = CameraStatus(
            CameraState.UNAVAILABLE,
            "Webcam unavailable or busy",
            f"{message}. {_busy_camera_help()}",
            retry_in_seconds=self.config.retry_interval_seconds,
        )
        self._log_once(
            "[camera] Webcam unavailable or busy. "
            f"{message}. Close Discord/browser/Meet/Teams/OBS or use --camera-index."
        )

    def _log_once(self, message: str) -> None:
        if message == self._last_log_message:
            return
        print(message, flush=True)
        self._last_log_message = message


def _busy_camera_help() -> str:
    return (
        "Close other apps using the webcam "
        "(Discord, browser, Meet, Teams, OBS) or change camera index."
    )


def _release_capture(capture) -> None:
    try:
        capture.release()
    except Exception:
        pass
