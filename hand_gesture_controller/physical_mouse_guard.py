from __future__ import annotations

import ctypes
import platform
import threading
from ctypes import wintypes
from typing import Callable


WH_MOUSE_LL = 14
WM_QUIT = 0x0012
LLMHF_INJECTED = 0x00000001


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("pt", wintypes.POINT),
        ("mouseData", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


LowLevelMouseProc = ctypes.WINFUNCTYPE(
    ctypes.c_ssize_t,
    ctypes.c_int,
    wintypes.WPARAM,
    wintypes.LPARAM,
)


class PhysicalMouseGuard:
    """Blocks physical mouse input while air mouse mode owns the pointer."""

    def __init__(
        self,
        should_block: Callable[[], bool],
        *,
        enabled: bool = True,
    ) -> None:
        self.should_block = should_block
        self.enabled = enabled and platform.system() == "Windows"
        self._thread: threading.Thread | None = None
        self._thread_id = wintypes.DWORD(0)
        self._hook = None
        self._callback = None
        self._ready = threading.Event()
        self._stopped = threading.Event()

        if self.enabled:
            self._user32 = ctypes.WinDLL("user32", use_last_error=True)
            self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            self._configure_winapi()
        else:
            self._user32 = None
            self._kernel32 = None

    def start(self) -> None:
        if not self.enabled or self._thread is not None:
            return
        self._thread = threading.Thread(
            target=self._run_message_loop,
            name="PhysicalMouseGuard",
            daemon=True,
        )
        self._thread.start()
        self._ready.wait(timeout=2.0)

    def stop(self) -> None:
        if not self.enabled or self._thread is None:
            return
        if self._thread_id.value:
            self._user32.PostThreadMessageW(self._thread_id.value, WM_QUIT, 0, 0)
        self._thread.join(timeout=2.0)
        self._thread = None

    def _run_message_loop(self) -> None:
        self._thread_id = wintypes.DWORD(self._kernel32.GetCurrentThreadId())

        @LowLevelMouseProc
        def callback(n_code, w_param, l_param):
            if n_code >= 0 and self._should_block_event(l_param):
                return 1
            return self._user32.CallNextHookEx(self._hook, n_code, w_param, l_param)

        self._callback = callback
        module_handle = self._kernel32.GetModuleHandleW(None)
        self._hook = self._user32.SetWindowsHookExW(
            WH_MOUSE_LL,
            self._callback,
            module_handle,
            0,
        )
        if not self._hook:
            self._hook = self._user32.SetWindowsHookExW(
                WH_MOUSE_LL,
                self._callback,
                None,
                0,
            )
        self._ready.set()

        if not self._hook:
            self.enabled = False
            return

        message = wintypes.MSG()
        while self._user32.GetMessageW(ctypes.byref(message), None, 0, 0) > 0:
            self._user32.TranslateMessage(ctypes.byref(message))
            self._user32.DispatchMessageW(ctypes.byref(message))

        self._user32.UnhookWindowsHookEx(self._hook)
        self._hook = None
        self._callback = None
        self._stopped.set()

    def _should_block_event(self, l_param) -> bool:
        try:
            hook_data = ctypes.cast(l_param, ctypes.POINTER(MSLLHOOKSTRUCT)).contents
            is_injected = bool(hook_data.flags & LLMHF_INJECTED)
            return self.should_block() and not is_injected
        except Exception:
            return False

    def _configure_winapi(self) -> None:
        self._kernel32.GetCurrentThreadId.argtypes = []
        self._kernel32.GetCurrentThreadId.restype = wintypes.DWORD

        self._kernel32.GetModuleHandleW.argtypes = [wintypes.LPCWSTR]
        self._kernel32.GetModuleHandleW.restype = wintypes.HMODULE

        self._user32.SetWindowsHookExW.argtypes = [
            ctypes.c_int,
            LowLevelMouseProc,
            wintypes.HINSTANCE,
            wintypes.DWORD,
        ]
        self._user32.SetWindowsHookExW.restype = wintypes.HHOOK

        self._user32.CallNextHookEx.argtypes = [
            wintypes.HHOOK,
            ctypes.c_int,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        self._user32.CallNextHookEx.restype = ctypes.c_ssize_t

        self._user32.UnhookWindowsHookEx.argtypes = [wintypes.HHOOK]
        self._user32.UnhookWindowsHookEx.restype = wintypes.BOOL

        self._user32.GetMessageW.argtypes = [
            ctypes.POINTER(wintypes.MSG),
            wintypes.HWND,
            wintypes.UINT,
            wintypes.UINT,
        ]
        self._user32.GetMessageW.restype = wintypes.BOOL

        self._user32.TranslateMessage.argtypes = [ctypes.POINTER(wintypes.MSG)]
        self._user32.TranslateMessage.restype = wintypes.BOOL

        self._user32.DispatchMessageW.argtypes = [ctypes.POINTER(wintypes.MSG)]
        self._user32.DispatchMessageW.restype = ctypes.c_ssize_t

        self._user32.PostThreadMessageW.argtypes = [
            wintypes.DWORD,
            wintypes.UINT,
            wintypes.WPARAM,
            wintypes.LPARAM,
        ]
        self._user32.PostThreadMessageW.restype = wintypes.BOOL
