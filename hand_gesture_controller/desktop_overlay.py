from __future__ import annotations

import ctypes
import multiprocessing as mp
import platform
import queue
import tkinter as tk
from dataclasses import dataclass


@dataclass(frozen=True)
class OverlayStatus:
    camera: str
    mouse_enabled: bool
    pointer_lock_enabled: bool
    paused: bool
    hands_count: int
    right_hand: str
    left_hand: str
    mouse_state: str
    last_action: str
    screen: str
    pointer_hold: bool


class DesktopOverlay:
    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self._process: mp.Process | None = None
        self._queue: mp.Queue | None = None

    def start(self) -> None:
        if not self.enabled or self._process is not None:
            return
        self._queue = mp.Queue(maxsize=2)
        self._process = mp.Process(
            target=_run_overlay_process,
            args=(self._queue,),
            daemon=True,
        )
        self._process.start()

    def update(self, status: OverlayStatus) -> None:
        if not self.enabled or self._queue is None:
            return
        try:
            while True:
                self._queue.get_nowait()
        except queue.Empty:
            pass
        try:
            self._queue.put_nowait(status)
        except queue.Full:
            pass

    def stop(self) -> None:
        if self._queue is not None:
            try:
                self._queue.put_nowait(None)
            except queue.Full:
                pass
        if self._process is not None:
            self._process.join(timeout=1.0)
            if self._process.is_alive():
                self._process.terminate()
                self._process.join(timeout=1.0)
        self._process = None
        self._queue = None


def _run_overlay_process(status_queue: mp.Queue) -> None:
    try:
        root = tk.Tk()
    except tk.TclError:
        return

    root.title("GestureTracker HUD")
    root.overrideredirect(True)
    root.attributes("-topmost", True)
    root.attributes("-alpha", 0.78)
    root.configure(bg="#111111")
    root.geometry("+20+20")

    frame = tk.Frame(root, bg="#111111", padx=12, pady=10)
    frame.pack()

    labels: dict[str, tk.Label] = {}
    for key in ("title", "mouse", "state", "hands", "action", "screen"):
        label = tk.Label(
            frame,
            text="",
            anchor="w",
            justify="left",
            bg="#111111",
            fg="#f5f5f5",
            font=("Segoe UI", 10),
        )
        label.pack(anchor="w")
        labels[key] = label

    _make_click_through(root)

    def poll() -> None:
        latest = None
        while True:
            try:
                latest = status_queue.get_nowait()
            except queue.Empty:
                break

        if latest is None and latest is not False:
            root.after(80, poll)
            return
        if latest is False:
            root.destroy()
            return
        if isinstance(latest, OverlayStatus):
            _render(labels, latest)
        root.after(80, poll)

    def poll_with_stop_marker() -> None:
        latest = "empty"
        while True:
            try:
                latest = status_queue.get_nowait()
            except queue.Empty:
                break

        if latest is None:
            root.destroy()
            return
        if isinstance(latest, OverlayStatus):
            _render(labels, latest)
        root.after(80, poll_with_stop_marker)

    poll_with_stop_marker()
    root.mainloop()


def _render(labels: dict[str, tk.Label], status: OverlayStatus) -> None:
    mode = "PAUSED" if status.paused else "ACTIVE"
    mouse = "ON" if status.mouse_enabled else "OFF"
    lock = "LOCK" if status.pointer_lock_enabled else "free"
    hold = "hold" if status.pointer_hold else "free"

    labels["title"].configure(text="Hand Controller")
    labels["mouse"].configure(text=f"camera {status.camera} | {mode}")
    labels["state"].configure(text=f"state {status.mouse_state} | cursor {hold}")
    labels["hands"].configure(
        text=f"hands {status.hands_count} | R {status.right_hand} | L {status.left_hand}"
    )
    labels["action"].configure(text=f"last {status.last_action or '-'}")
    labels["screen"].configure(
        text=f"mouse {mouse} | pointer {lock} | screen {status.screen}"
    )


def _make_click_through(root: tk.Tk) -> None:
    if platform.system() != "Windows":
        return

    hwnd = root.winfo_id()
    user32 = ctypes.windll.user32
    gwl_exstyle = -20
    ws_ex_layered = 0x00080000
    ws_ex_transparent = 0x00000020
    ws_ex_toolwindow = 0x00000080

    style = user32.GetWindowLongW(hwnd, gwl_exstyle)
    style |= ws_ex_layered | ws_ex_transparent | ws_ex_toolwindow
    user32.SetWindowLongW(hwnd, gwl_exstyle, style)
