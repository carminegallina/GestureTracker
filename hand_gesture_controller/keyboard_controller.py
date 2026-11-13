from __future__ import annotations


class KeyboardController:
    def __init__(self, dry_run: bool = False) -> None:
        self.dry_run = dry_run
        self._pyautogui = None
        if not dry_run:
            import pyautogui

            pyautogui.PAUSE = 0
            self._pyautogui = pyautogui

    def copy(self) -> None:
        self.hotkey("ctrl", "c")

    def paste(self) -> None:
        self.hotkey("ctrl", "v")

    def hotkey(self, *keys: str) -> None:
        if self.dry_run:
            return
        self._pyautogui.hotkey(*keys)

    def press(self, key: str) -> None:
        if self.dry_run:
            return
        self._pyautogui.press(key)

    def write_text(self, value: str) -> None:
        if self.dry_run:
            return
        self._pyautogui.write(value)
