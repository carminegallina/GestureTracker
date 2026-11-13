from __future__ import annotations

import ctypes
import platform
from dataclasses import dataclass
from ctypes import wintypes

from .config import PointerConfig
from .models import LandmarkPoint
from .smoothing import clamp


@dataclass(frozen=True)
class ScreenPoint:
    x: int
    y: int


@dataclass(frozen=True)
class ScreenRect:
    left: int
    top: int
    width: int
    height: int

    @property
    def right(self) -> int:
        return self.left + self.width

    @property
    def bottom(self) -> int:
        return self.top + self.height

    @classmethod
    def parse(cls, value: str) -> "ScreenRect":
        parts = [int(part.strip()) for part in value.split(",")]
        if len(parts) != 4:
            raise ValueError("screen rect must be left,top,width,height")
        return cls(parts[0], parts[1], parts[2], parts[3])


class MouseController:
    def __init__(
        self,
        dry_run: bool = False,
        screen_width: int | None = None,
        screen_height: int | None = None,
        screen_target: str = "all",
        screen_rect: ScreenRect | None = None,
    ) -> None:
        self.dry_run = dry_run
        self._pyautogui = None
        self._user32 = ctypes.windll.user32 if platform.system() == "Windows" else None

        if screen_rect is not None:
            self._screen = screen_rect
        elif dry_run:
            self._screen = ScreenRect(0, 0, screen_width or 1920, screen_height or 1080)
        else:
            import pyautogui

            pyautogui.FAILSAFE = True
            pyautogui.PAUSE = 0
            self._pyautogui = pyautogui
            self._screen = self._select_screen_rect(screen_target)

    @property
    def screen_size(self) -> tuple[int, int]:
        return self._screen.width, self._screen.height

    @property
    def screen_rect(self) -> ScreenRect:
        return self._screen

    def landmark_to_screen(
        self, point: LandmarkPoint, config: PointerConfig
    ) -> ScreenPoint:
        normalized_x = (
            point.x - config.active_zone_left
        ) / (config.active_zone_right - config.active_zone_left)
        normalized_y = (
            point.y - config.active_zone_top
        ) / (config.active_zone_bottom - config.active_zone_top)

        normalized_x = clamp(normalized_x, 0.0, 1.0)
        normalized_y = clamp(normalized_y, 0.0, 1.0)
        normalized_x = _apply_pointer_sensitivity(
            normalized_x, config.sensitivity
        )
        normalized_y = _apply_pointer_sensitivity(
            normalized_y, config.sensitivity
        )

        return ScreenPoint(
            self._screen.left + int(normalized_x * (self._screen.width - 1)),
            self._screen.top + int(normalized_y * (self._screen.height - 1)),
        )

    def move_to(self, x: int, y: int) -> None:
        if self.dry_run:
            return
        if self._user32 is not None:
            self._user32.SetCursorPos(int(x), int(y))
            return
        self._pyautogui.moveTo(x, y, duration=0)

    def click(self) -> None:
        if self.dry_run:
            return
        self._pyautogui.click()

    def double_click(self) -> None:
        if self.dry_run:
            return
        self._pyautogui.doubleClick()

    def right_click(self) -> None:
        if self.dry_run:
            return
        self._pyautogui.click(button="right")

    def mouse_down(self) -> None:
        if self.dry_run:
            return
        self._pyautogui.mouseDown()

    def mouse_up(self) -> None:
        if self.dry_run:
            return
        self._pyautogui.mouseUp()

    def _select_screen_rect(self, screen_target: str) -> ScreenRect:
        target = screen_target.lower()
        if target == "all":
            return self._detect_virtual_screen_rect()
        if target == "primary":
            return self._detect_primary_screen_rect()

        monitors = self._detect_monitor_rects()
        if target.isdigit() and monitors:
            index = int(target) - 1
            if 0 <= index < len(monitors):
                return monitors[index]

        return self._detect_virtual_screen_rect()

    def _detect_virtual_screen_rect(self) -> ScreenRect:
        if self._user32 is None:
            width, height = self._pyautogui.size()
            return ScreenRect(0, 0, int(width), int(height))

        sm_xvirtualscreen = 76
        sm_yvirtualscreen = 77
        sm_cxvirtualscreen = 78
        sm_cyvirtualscreen = 79

        left = self._user32.GetSystemMetrics(sm_xvirtualscreen)
        top = self._user32.GetSystemMetrics(sm_yvirtualscreen)
        width = self._user32.GetSystemMetrics(sm_cxvirtualscreen)
        height = self._user32.GetSystemMetrics(sm_cyvirtualscreen)

        if width <= 0 or height <= 0:
            width, height = self._pyautogui.size()
            return ScreenRect(0, 0, int(width), int(height))

        return ScreenRect(int(left), int(top), int(width), int(height))

    def _detect_primary_screen_rect(self) -> ScreenRect:
        if self._user32 is None:
            width, height = self._pyautogui.size()
            return ScreenRect(0, 0, int(width), int(height))

        width = self._user32.GetSystemMetrics(0)
        height = self._user32.GetSystemMetrics(1)
        return ScreenRect(0, 0, int(width), int(height))

    def _detect_monitor_rects(self) -> list[ScreenRect]:
        if self._user32 is None:
            return [self._detect_primary_screen_rect()]

        rects: list[ScreenRect] = []

        monitor_enum_proc = ctypes.WINFUNCTYPE(
            ctypes.c_int,
            wintypes.HMONITOR,
            wintypes.HDC,
            ctypes.POINTER(wintypes.RECT),
            wintypes.LPARAM,
        )

        @monitor_enum_proc
        def callback(_monitor, _hdc, rect_pointer, _data):
            rect = rect_pointer.contents
            rects.append(
                ScreenRect(
                    int(rect.left),
                    int(rect.top),
                    int(rect.right - rect.left),
                    int(rect.bottom - rect.top),
                )
            )
            return 1

        self._user32.EnumDisplayMonitors(None, None, callback, 0)
        return sorted(rects, key=lambda rect: (rect.left, rect.top))


def _apply_pointer_sensitivity(value: float, sensitivity: float) -> float:
    """Adjust response around center while preserving exact 0 and 1 edges."""
    value = clamp(value, 0.0, 1.0)
    sensitivity = max(float(sensitivity), 0.05)
    if sensitivity == 1.0:
        return value

    centered = (value * 2.0) - 1.0
    exponent = 1.0 / sensitivity
    shaped = _signed_power(centered, exponent)
    return clamp((shaped + 1.0) / 2.0, 0.0, 1.0)


def _signed_power(value: float, exponent: float) -> float:
    if value < 0:
        return -(abs(value) ** exponent)
    return value**exponent
