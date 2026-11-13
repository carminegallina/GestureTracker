from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from math import sqrt
from pathlib import Path
from typing import Any

from .models import HandResult


PACKAGE_DIR = Path(__file__).resolve().parent
TEMPLATE_PROFILE = PACKAGE_DIR / "profiles" / "custom_gestures.json"


@dataclass(frozen=True)
class PoseTemplate:
    name: str
    handedness: str
    vector: list[float]
    threshold: float
    created_at: str


class PoseTemplateStore:
    def __init__(self, path: Path | str | None = None) -> None:
        self.path = Path(path) if path else TEMPLATE_PROFILE
        self.templates = self._load()

    def _load(self) -> list[PoseTemplate]:
        if not self.path.exists():
            return []

        with self.path.open("r", encoding="utf-8") as file:
            data = json.load(file)

        templates = []
        for item in data.get("templates", []):
            templates.append(
                PoseTemplate(
                    name=str(item["name"]),
                    handedness=str(item.get("handedness", "any")),
                    vector=[float(value) for value in item["vector"]],
                    threshold=float(item.get("threshold", 0.18)),
                    created_at=str(item.get("created_at", "")),
                )
            )
        return templates

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data: dict[str, Any] = {
            "version": 1,
            "templates": [
                {
                    "name": template.name,
                    "handedness": template.handedness,
                    "vector": template.vector,
                    "threshold": template.threshold,
                    "created_at": template.created_at,
                }
                for template in self.templates
            ],
        }
        with self.path.open("w", encoding="utf-8") as file:
            json.dump(data, file, indent=2)
            file.write("\n")

    def record(
        self,
        hand: HandResult,
        *,
        name: str | None = None,
        threshold: float = 0.18,
    ) -> PoseTemplate:
        template = PoseTemplate(
            name=name or self._next_name(),
            handedness=hand.handedness,
            vector=pose_vector(hand),
            threshold=threshold,
            created_at=datetime.now().isoformat(timespec="seconds"),
        )

        for index, existing in enumerate(self.templates):
            if existing.name == template.name:
                self.templates[index] = template
                self.save()
                return template

        self.templates.append(template)
        self.save()
        return template

    def match(self, hand: HandResult) -> list[str]:
        vector = pose_vector(hand)
        matches = []
        for template in self.templates:
            if template.handedness.lower() not in {"any", hand.handedness.lower()}:
                continue
            if pose_distance(vector, template.vector) <= template.threshold:
                matches.append(template.name)
        return matches

    def _next_name(self) -> str:
        existing = {template.name for template in self.templates}
        index = 1
        while True:
            name = f"custom_{index:03d}"
            if name not in existing:
                return name
            index += 1


def pose_vector(hand: HandResult) -> list[float]:
    landmarks = hand.landmarks
    wrist = landmarks[0]
    scale = max(
        sqrt((landmarks[9].x - wrist.x) ** 2 + (landmarks[9].y - wrist.y) ** 2),
        1e-6,
    )

    vector = []
    for point in landmarks:
        vector.append((point.x - wrist.x) / scale)
        vector.append((point.y - wrist.y) / scale)
    return vector


def pose_distance(first: list[float], second: list[float]) -> float:
    if len(first) != len(second):
        return 999.0
    return sqrt(sum((a - b) ** 2 for a, b in zip(first, second)) / len(first))

