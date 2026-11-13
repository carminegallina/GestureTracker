from __future__ import annotations

import ctypes
import os
import time
from ctypes import wintypes
from dataclasses import dataclass
from typing import Protocol

from .config import MediaGestureConfig


@dataclass(frozen=True)
class ActiveWindow:
    title: str = ""
    process_name: str = ""


@dataclass(frozen=True)
class ScreenContext:
    is_media: bool
    title: str = ""
    process_name: str = ""
    reason: str = ""


class ActiveWindowProvider(Protocol):
    def get_active_window(self) -> ActiveWindow:
        ...


class ScreenContextDetector:
    def __init__(
        self,
        config: MediaGestureConfig,
        provider: ActiveWindowProvider | None = None,
    ) -> None:
        self.config = config
        self._provider = provider or WindowsActiveWindowProvider()
        self._last_checked_at = -999.0
        self._context = ScreenContext(False)

    def update(self, now: float | None = None) -> ScreenContext:
        now = time.monotonic() if now is None else now
        if now - self._last_checked_at < self.config.window_check_interval_seconds:
            return self._context

        self._last_checked_at = now
        window = self._provider.get_active_window()
        self._context = classify_active_window(window, self.config)
        return self._context


def classify_active_window(
    window: ActiveWindow, config: MediaGestureConfig
) -> ScreenContext:
    process_name = window.process_name.lower()
    title = window.title.lower()

    player_processes = {process.lower() for process in config.player_processes}
    browser_processes = {process.lower() for process in config.browser_processes}

    if process_name in player_processes:
        return ScreenContext(
            True,
            title=window.title,
            process_name=window.process_name,
            reason="player process",
        )

    if process_name in browser_processes:
        for keyword in config.browser_title_keywords:
            if keyword.lower() in title:
                return ScreenContext(
                    True,
                    title=window.title,
                    process_name=window.process_name,
                    reason=f"browser video: {keyword}",
                )

    return ScreenContext(
        False,
        title=window.title,
        process_name=window.process_name,
    )


class WindowsActiveWindowProvider:
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    def __init__(self) -> None:
        self._available = os.name == "nt"
        if not self._available:
            return

        self._user32 = ctypes.WinDLL("user32", use_last_error=True)
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

        self._user32.GetForegroundWindow.restype = wintypes.HWND
        self._user32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
        self._user32.GetWindowTextLengthW.restype = ctypes.c_int
        self._user32.GetWindowTextW.argtypes = [
            wintypes.HWND,
            wintypes.LPWSTR,
            ctypes.c_int,
        ]
        self._user32.GetWindowTextW.restype = ctypes.c_int
        self._user32.GetWindowThreadProcessId.argtypes = [
            wintypes.HWND,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self._user32.GetWindowThreadProcessId.restype = wintypes.DWORD

        self._kernel32.OpenProcess.argtypes = [
            wintypes.DWORD,
            wintypes.BOOL,
            wintypes.DWORD,
        ]
        self._kernel32.OpenProcess.restype = wintypes.HANDLE
        self._kernel32.QueryFullProcessImageNameW.argtypes = [
            wintypes.HANDLE,
            wintypes.DWORD,
            wintypes.LPWSTR,
            ctypes.POINTER(wintypes.DWORD),
        ]
        self._kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL
        self._kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
        self._kernel32.CloseHandle.restype = wintypes.BOOL

    def get_active_window(self) -> ActiveWindow:
        if not self._available:
            return ActiveWindow()

        hwnd = self._user32.GetForegroundWindow()
        if not hwnd:
            return ActiveWindow()

        return ActiveWindow(
            title=self._get_window_title(hwnd),
            process_name=self._get_process_name(hwnd),
        )

    def _get_window_title(self, hwnd) -> str:
        length = self._user32.GetWindowTextLengthW(hwnd)
        if length <= 0:
            return ""

        buffer = ctypes.create_unicode_buffer(length + 1)
        self._user32.GetWindowTextW(hwnd, buffer, length + 1)
        return buffer.value

    def _get_process_name(self, hwnd) -> str:
        process_id = wintypes.DWORD()
        self._user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        if not process_id.value:
            return ""

        handle = self._kernel32.OpenProcess(
            self.PROCESS_QUERY_LIMITED_INFORMATION,
            False,
            process_id.value,
        )
        if not handle:
            return ""

        try:
            size = wintypes.DWORD(32768)
            buffer = ctypes.create_unicode_buffer(size.value)
            ok = self._kernel32.QueryFullProcessImageNameW(
                handle,
                0,
                buffer,
                ctypes.byref(size),
            )
            if not ok:
                return ""
            return os.path.basename(buffer.value)
        finally:
            self._kernel32.CloseHandle(handle)
