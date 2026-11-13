from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PACKAGE_DIR = Path(__file__).resolve().parent
PROFILE_DIR = PACKAGE_DIR / "profiles"
DEFAULT_ACTION_PROFILE = PROFILE_DIR / "default_actions.json"


DEFAULT_BINDINGS: list[dict[str, Any]] = [
    {
        "name": "two_fists_copy",
        "enabled": True,
        "gesture": "two_fists",
        "hands": ["Left", "Right"],
        "hold_seconds": 0.50,
        "cooldown_seconds": 1.00,
        "priority": 100,
        "action": {"type": "hotkey", "keys": ["ctrl", "c"]},
    },
    {
        "name": "two_v_paste",
        "enabled": True,
        "gesture": "two_v_signs",
        "hands": ["Left", "Right"],
        "hold_seconds": 0.50,
        "cooldown_seconds": 1.00,
        "priority": 100,
        "action": {"type": "hotkey", "keys": ["ctrl", "v"]},
    },
    {
        "name": "left_v_paste",
        "enabled": True,
        "gesture": "v_sign",
        "hands": ["Left"],
        "hold_seconds": 0.45,
        "cooldown_seconds": 1.00,
        "priority": 60,
        "action": {"type": "hotkey", "keys": ["ctrl", "v"]},
    },
    {
        "name": "left_thumbs_up_copy",
        "enabled": True,
        "gesture": "thumbs_up",
        "hands": ["Left"],
        "hold_seconds": 0.45,
        "cooldown_seconds": 1.00,
        "priority": 60,
        "action": {"type": "hotkey", "keys": ["ctrl", "c"]},
    },
    {
        "name": "left_fist_toggle_mouse",
        "enabled": True,
        "gesture": "fist",
        "hands": ["Left"],
        "hold_seconds": 0.80,
        "cooldown_seconds": 1.00,
        "priority": 40,
        "action": {"type": "toggle_mouse"},
    },
]


@dataclass
class ActionProfile:
    path: Path
    bindings: list[dict[str, Any]]

    @classmethod
    def load(cls, path: Path | str | None = None) -> "ActionProfile":
        profile_path = Path(path) if path else DEFAULT_ACTION_PROFILE
        if not profile_path.exists():
            profile_path.parent.mkdir(parents=True, exist_ok=True)
            profile = cls(profile_path, DEFAULT_BINDINGS.copy())
            profile.save()
            return profile

        with profile_path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        bindings = data.get("bindings", [])
        if not isinstance(bindings, list):
            raise ValueError(f"Invalid action profile bindings in {profile_path}")
        return cls(profile_path, bindings)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"version": 1, "bindings": self.bindings}
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)
            file.write("\n")

    def sorted_bindings(self) -> list[dict[str, Any]]:
        return sorted(
            [binding for binding in self.bindings if binding.get("enabled", True)],
            key=lambda binding: binding.get("priority", 0),
            reverse=True,
        )

    def upsert_binding(
        self,
        *,
        name: str,
        gesture: str,
        hands: list[str],
        action: dict[str, Any],
        hold_seconds: float = 0.50,
        cooldown_seconds: float = 1.00,
        priority: int = 80,
    ) -> None:
        binding = {
            "name": name,
            "enabled": True,
            "gesture": gesture,
            "hands": hands,
            "hold_seconds": hold_seconds,
            "cooldown_seconds": cooldown_seconds,
            "priority": priority,
            "action": action,
        }

        for index, existing in enumerate(self.bindings):
            if existing.get("name") == name:
                self.bindings[index] = binding
                return
        self.bindings.append(binding)


@dataclass(frozen=True)
class BindingEvent:
    name: str
    action: dict[str, Any]

