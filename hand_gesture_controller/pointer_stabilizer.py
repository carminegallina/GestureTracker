from __future__ import annotations

from dataclasses import dataclass

from .mouse_controller import ScreenPoint


@dataclass(frozen=True)
class StabilizedPointer:
    point: ScreenPoint
    is_holding: bool


class PointerStabilizer:
    def __init__(self, freeze_seconds: float) -> None:
        self.freeze_seconds = freeze_seconds
        self._hold_point: ScreenPoint | None = None
        self._hold_until = 0.0
        self._button_was_active = False

    def update(
        self,
        target: ScreenPoint,
        *,
        button_active: bool,
        dragging: bool,
        now: float,
    ) -> StabilizedPointer:
        if dragging:
            self._hold_point = None
            self._hold_until = 0.0
            self._button_was_active = button_active
            return StabilizedPointer(target, False)

        if button_active:
            if not self._button_was_active or self._hold_point is None:
                self._hold_point = target
            self._button_was_active = True
            self._hold_until = max(self._hold_until, now + self.freeze_seconds)
            return StabilizedPointer(self._hold_point, True)

        if self._button_was_active:
            self._button_was_active = False
            if self._hold_point is None:
                self._hold_point = target
            self._hold_until = now + self.freeze_seconds
            return StabilizedPointer(self._hold_point, True)

        if self._hold_point is not None and now < self._hold_until:
            return StabilizedPointer(self._hold_point, True)

        self._hold_point = None
        return StabilizedPointer(target, False)

    def reset(self) -> None:
        self._hold_point = None
        self._hold_until = 0.0
        self._button_was_active = False

