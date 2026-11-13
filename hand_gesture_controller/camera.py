from __future__ import annotations

import cv2

from .config import CameraConfig


class Camera:
    def __init__(self, config: CameraConfig) -> None:
        self.config = config
        self.capture = cv2.VideoCapture(config.index)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, config.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, config.height)

        if not self.capture.isOpened():
            raise RuntimeError(
                f"Cannot open camera index {config.index}. "
                "Check webcam permissions or pass --camera-index."
            )

    def read(self):
        ok, frame = self.capture.read()
        if not ok:
            return None
        if self.config.mirror:
            frame = cv2.flip(frame, 1)
        return frame

    def release(self) -> None:
        self.capture.release()

