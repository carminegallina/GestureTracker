from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .config import AppConfig, DEFAULT_CONFIG, merge_dataclass

DEFAULT_SETTINGS_PATH = Path("hand_gesture_controller") / "settings.json"


class SettingsStore:
    """Impostazioni su file JSON, cosi' i valori si cambiano senza toccare il codice.

    Precedenza: default del codice, poi il file, poi gli argomenti da riga di comando.
    Un file assente o illeggibile non e' un errore: si usano i default.
    """

    def __init__(self, path: str | Path | None = None) -> None:
        self.path = Path(path) if path else DEFAULT_SETTINGS_PATH

    def load(self, base: AppConfig = DEFAULT_CONFIG) -> AppConfig:
        if not self.path.exists():
            return base

        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return base

        if not isinstance(data, dict):
            return base

        return AppConfig(
            camera=merge_dataclass(base.camera, _section(data, "camera")),
            virtual_camera=merge_dataclass(
                base.virtual_camera, _section(data, "virtual_camera")
            ),
            tracker=merge_dataclass(base.tracker, _section(data, "tracker")),
            pointer=merge_dataclass(base.pointer, _section(data, "pointer")),
            gesture=merge_dataclass(base.gesture, _section(data, "gesture")),
            media_gesture=merge_dataclass(
                base.media_gesture, _section(data, "media_gesture")
            ),
            runtime=merge_dataclass(base.runtime, _section(data, "runtime")),
        )

    def save(self, config: AppConfig = DEFAULT_CONFIG) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(asdict(config), indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    section = data.get(name, {})
    return section if isinstance(section, dict) else {}


def main() -> None:
    """Rigenera settings.example.json dai default del codice."""
    path = Path("hand_gesture_controller") / "settings.example.json"
    SettingsStore(path).save()
    print(f"scritto {path}")


if __name__ == "__main__":
    main()
