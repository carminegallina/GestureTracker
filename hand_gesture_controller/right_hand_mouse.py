from __future__ import annotations

from dataclasses import dataclass

from .binding_engine import HandObservation
from .config import GestureConfig
from .gesture_detector import HandLandmark
from .mouse_controller import MouseController


@dataclass(frozen=True)
class MouseGestureUpdate:
    state: str
    action: str | None = None


class RightHandMouseController:
    def __init__(self, config: GestureConfig) -> None:
        self.config = config
        self._middle_started_at: float | None = None
        self._middle_dragging = False
        self._seen_middle_up = False
        self._last_left_click_at: float | None = None
        self._ring_started_at: float | None = None
        self._ring_fired = False
        self._seen_ring_up = False

    def update(
        self,
        observation: HandObservation | None,
        now: float,
        mouse: MouseController,
    ) -> MouseGestureUpdate:
        if observation is None:
            release_action = self.cancel(mouse)
            return MouseGestureUpdate("idle", release_action)

        extended = observation.gesture_frame.extended_fingers
        middle_up = extended.get("middle", False)
        ring_up = extended.get("ring", False)

        if middle_up:
            self._seen_middle_up = True
        if ring_up:
            self._seen_ring_up = True

        action = self._update_middle(middle_up, ring_up, now, mouse)
        action = self._update_ring(middle_up, ring_up, now, mouse) or action

        if self._middle_dragging:
            return MouseGestureUpdate("left_dragging", action)
        if self._middle_started_at is not None:
            return MouseGestureUpdate("middle_down", action)
        if self._ring_started_at is not None:
            return MouseGestureUpdate("ring_down", action)
        return MouseGestureUpdate("moving", action)

    def cancel(self, mouse: MouseController) -> str | None:
        action = None
        if self._middle_dragging:
            mouse.mouse_up()
            action = "left drag release"
        self._middle_started_at = None
        self._middle_dragging = False
        self._ring_started_at = None
        self._ring_fired = False
        return action

    def _update_middle(
        self,
        middle_up: bool,
        ring_up: bool,
        now: float,
        mouse: MouseController,
    ) -> str | None:
        middle_click_pose = self._seen_middle_up and not middle_up and ring_up

        if middle_click_pose:
            if self._middle_started_at is None:
                self._middle_started_at = now
                self._middle_dragging = False
                return None

            held_for = now - self._middle_started_at
            if not self._middle_dragging and held_for >= self.config.drag_hold_seconds:
                mouse.mouse_down()
                self._middle_dragging = True
                return "left drag start"
            return None

        if self._middle_started_at is None:
            return None

        held_for = now - self._middle_started_at
        was_dragging = self._middle_dragging
        self._middle_started_at = None
        self._middle_dragging = False

        if was_dragging:
            mouse.mouse_up()
            return "left drag release"

        if held_for >= self.config.finger_tap_min_seconds:
            return self._register_left_tap(now, mouse)
        return None

    def _update_ring(
        self,
        middle_up: bool,
        ring_up: bool,
        now: float,
        mouse: MouseController,
    ) -> str | None:
        ring_click_pose = self._seen_ring_up and middle_up and not ring_up

        if ring_click_pose:
            if self._ring_started_at is None:
                self._ring_started_at = now
                self._ring_fired = False
                return None

            held_for = now - self._ring_started_at
            if (
                not self._ring_fired
                and held_for >= self.config.right_click_hold_seconds
            ):
                mouse.right_click()
                self._ring_fired = True
                return "right click"
            return None

        self._ring_started_at = None
        self._ring_fired = False
        return None

    def _register_left_tap(self, now: float, mouse: MouseController) -> str:
        mouse.click()
        if (
            self._last_left_click_at is not None
            and now - self._last_left_click_at <= self.config.double_click_seconds
        ):
            self._last_left_click_at = None
            return "left double click"

        self._last_left_click_at = now
        return "left click"


def pointer_anchor(observation: HandObservation):
    return observation.hand.landmarks[HandLandmark.INDEX_TIP]
