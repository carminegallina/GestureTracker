from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .keyboard_controller import KeyboardController


@dataclass
class RuntimeControls:
    mouse_enabled: bool = True
    pointer_lock_enabled: bool = True


class ActionRunner:
    def __init__(
        self,
        keyboard: KeyboardController,
        controls: RuntimeControls,
        dry_run: bool = False,
    ) -> None:
        self.keyboard = keyboard
        self.controls = controls
        self.dry_run = dry_run

    def run(self, action: dict[str, Any]) -> str:
        action_type = action.get("type", "noop")

        if action_type == "noop":
            return "noop"
        if action_type == "toggle_mouse":
            self.controls.mouse_enabled = not self.controls.mouse_enabled
            return "mouse on" if self.controls.mouse_enabled else "mouse off"
        if action_type == "mouse_on":
            self.controls.mouse_enabled = True
            return "mouse on"
        if action_type == "mouse_off":
            self.controls.mouse_enabled = False
            return "mouse off"
        if action_type == "hotkey":
            keys = [str(key) for key in action.get("keys", [])]
            if keys:
                self.keyboard.hotkey(*keys)
            return "+".join(keys) if keys else "hotkey"
        if action_type == "key":
            key = str(action.get("key", ""))
            if key:
                self.keyboard.press(key)
            return key if key else "key"
        if action_type == "text":
            value = str(action.get("value", ""))
            if value:
                self.keyboard.write_text(value)
            return "text"
        if action_type == "macro":
            labels = []
            for step in action.get("steps", []):
                if isinstance(step, dict):
                    labels.append(self.run(step))
            return "macro: " + ", ".join(labels)

        return f"unknown action: {action_type}"
