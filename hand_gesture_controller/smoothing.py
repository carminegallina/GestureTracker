from __future__ import annotations

from dataclasses import dataclass
from math import hypot


@dataclass
class ExponentialSmoother:
    alpha: float
    dead_zone_px: float
    _value: tuple[float, float] | None = None

    def reset(self) -> None:
        self._value = None

    def update(self, target: tuple[float, float]) -> tuple[int, int]:
        if self._value is None:
            self._value = target
            return int(target[0]), int(target[1])

        previous_x, previous_y = self._value
        target_x, target_y = target
        if hypot(target_x - previous_x, target_y - previous_y) < self.dead_zone_px:
            return int(previous_x), int(previous_y)

        smoothed = (
            previous_x + self.alpha * (target_x - previous_x),
            previous_y + self.alpha * (target_y - previous_y),
        )
        self._value = smoothed
        return int(smoothed[0]), int(smoothed[1])


def clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))

