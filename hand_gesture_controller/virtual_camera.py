from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass
from enum import Enum
from typing import Callable

import cv2
import numpy as np

from .config import VirtualCameraConfig


class VirtualCameraState(str, Enum):
    DISABLED = "disabled"
    STOPPED = "stopped"
    STARTING = "starting"
    OPEN = "open"
    UNAVAILABLE = "unavailable"


@dataclass(frozen=True)
class VirtualCameraStatus:
    state: VirtualCameraState
    message: str
    detail: str = ""
    device: str = ""
    backend: str = ""


VirtualCameraFactory = Callable[..., object]
_STOP = object()


class VirtualCameraRelay:
    """Publishes the latest physical webcam frame to a virtual camera device."""

    def __init__(
        self,
        config: VirtualCameraConfig,
        camera_factory: VirtualCameraFactory | None = None,
        pixel_format: object | None = None,
    ) -> None:
        self.config = config
        self._camera_factory = camera_factory
        self._pixel_format = pixel_format
        self._lock = threading.Lock()
        self._queue: queue.Queue[object] = queue.Queue(maxsize=1)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._next_retry_at = 0.0
        self._last_log_message = ""
        initial_state = (
            VirtualCameraState.STOPPED
            if self.config.enabled
            else VirtualCameraState.DISABLED
        )
        self._status = VirtualCameraStatus(
            initial_state,
            "Virtual camera ready" if self.config.enabled else "Virtual camera disabled",
        )

    @property
    def status(self) -> VirtualCameraStatus:
        with self._lock:
            return self._status

    def submit(self, frame_bgr: np.ndarray) -> None:
        if not self.config.enabled:
            return

        height, width = frame_bgr.shape[:2]
        if not self._ensure_started(width, height):
            return

        latest_frame = np.ascontiguousarray(frame_bgr.copy())
        self._replace_latest(latest_frame)

    def stop(self) -> None:
        thread = self._thread
        if thread is None:
            if self.config.enabled:
                self._set_status(
                    VirtualCameraState.STOPPED,
                    "Virtual camera stopped",
                    "No frame is being published.",
                )
            return

        self._stop_event.set()
        self._replace_latest(_STOP)
        thread.join(timeout=1.0)
        if not thread.is_alive():
            self._thread = None
            if self.config.enabled:
                self._set_status(
                    VirtualCameraState.STOPPED,
                    "Virtual camera stopped",
                    "Released because the physical webcam is paused or unavailable.",
                )

    def close(self) -> None:
        self.stop()

    def _ensure_started(self, source_width: int, source_height: int) -> bool:
        with self._lock:
            thread = self._thread
            if thread is not None and thread.is_alive():
                return True

            now = time.monotonic()
            if now < self._next_retry_at:
                return False

            self._thread = None
            self._queue = queue.Queue(maxsize=1)
            self._stop_event = threading.Event()
            width = self.config.width or source_width
            height = self.config.height or source_height
            thread = threading.Thread(
                target=self._run,
                args=(width, height),
                name="VirtualCameraRelay",
                daemon=True,
            )
            self._thread = thread
            self._status = VirtualCameraStatus(
                VirtualCameraState.STARTING,
                f"Starting virtual camera {width}x{height}@{self.config.fps:g}",
            )
            thread.start()
            return True

    def _run(self, width: int, height: int) -> None:
        virtual_camera = None
        try:
            camera_factory, pixel_format = self._resolve_backend()
            virtual_camera = camera_factory(
                width=width,
                height=height,
                fps=self.config.fps,
                fmt=pixel_format,
                device=self.config.device,
                backend=self.config.backend,
                print_fps=self.config.print_fps,
            )
            device = str(getattr(virtual_camera, "device", "") or self.config.device or "")
            backend = str(
                getattr(virtual_camera, "backend", "") or self.config.backend or ""
            )
            self._set_status(
                VirtualCameraState.OPEN,
                "Virtual camera active",
                "Select this virtual camera in Discord/browser/Meet/Teams.",
                device=device,
                backend=backend,
            )
            self._log_once(
                "[virtual-camera] Started"
                + (f" device='{device}'" if device else "")
                + (f" backend='{backend}'" if backend else "")
                + f" at {width}x{height}@{self.config.fps:g}."
            )

            while not self._stop_event.is_set():
                item = self._next_frame()
                if item is _STOP:
                    break
                if item is None:
                    continue
                frame = self._prepare_frame(item, width, height)
                virtual_camera.send(frame)
                sleep_until_next_frame = getattr(
                    virtual_camera, "sleep_until_next_frame", None
                )
                if callable(sleep_until_next_frame):
                    sleep_until_next_frame()
        except Exception as exc:
            self._next_retry_at = time.monotonic() + self.config.retry_interval_seconds
            self._set_status(
                VirtualCameraState.UNAVAILABLE,
                "Virtual camera unavailable",
                (
                    f"{exc}. Install/initialize a supported virtual camera "
                    "driver, then keep using the app; it will retry automatically."
                ),
            )
            self._log_once(
                "[virtual-camera] Unavailable. "
                f"{exc}. Install OBS Virtual Camera or Unity Capture and retry."
            )
        finally:
            if virtual_camera is not None:
                close = getattr(virtual_camera, "close", None)
                if callable(close):
                    close()

    def _resolve_backend(self) -> tuple[VirtualCameraFactory, object]:
        if self._camera_factory is not None:
            return self._camera_factory, self._pixel_format or "BGR"

        try:
            import pyvirtualcam
        except ImportError as exc:
            raise RuntimeError(
                "Python package 'pyvirtualcam' is not installed"
            ) from exc

        return pyvirtualcam.Camera, pyvirtualcam.PixelFormat.BGR

    def _next_frame(self) -> object | None:
        try:
            item = self._queue.get(timeout=0.2)
        except queue.Empty:
            return None

        latest = item
        while True:
            try:
                latest = self._queue.get_nowait()
            except queue.Empty:
                return latest

    def _prepare_frame(self, item: object, width: int, height: int) -> np.ndarray:
        frame = item
        if not isinstance(frame, np.ndarray):
            raise TypeError("Virtual camera frame is not a numpy array")

        if frame.shape[1] != width or frame.shape[0] != height:
            frame = cv2.resize(frame, (width, height), interpolation=cv2.INTER_LINEAR)
        return np.ascontiguousarray(frame)

    def _replace_latest(self, item: object) -> None:
        while True:
            try:
                self._queue.put_nowait(item)
                return
            except queue.Full:
                try:
                    self._queue.get_nowait()
                except queue.Empty:
                    continue

    def _set_status(
        self,
        state: VirtualCameraState,
        message: str,
        detail: str = "",
        *,
        device: str = "",
        backend: str = "",
    ) -> None:
        with self._lock:
            self._status = VirtualCameraStatus(
                state=state,
                message=message,
                detail=detail,
                device=device,
                backend=backend,
            )

    def _log_once(self, message: str) -> None:
        if message == self._last_log_message:
            return
        print(message, flush=True)
        self._last_log_message = message
