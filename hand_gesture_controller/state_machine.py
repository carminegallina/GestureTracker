from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .config import GestureConfig
from .gesture_detector import Gesture
from .keyboard_controller import KeyboardController
from .mouse_controller import MouseController


class ControllerState(str, Enum):
    IDLE = "idle"
    MOVING = "moving"
    PINCHING = "pinching"
    DRAGGING = "dragging"
    COPY_ARMED = "copy_armed"
    PASTE_ARMED = "paste_armed"
    PAUSED = "paused"


@dataclass(frozen=True)
class StateUpdate:
    state: ControllerState
    action: str | None = None


class GestureStateMachine:
    def __init__(
        self,
        config: GestureConfig,
        paused: bool = False,
        commands_enabled: bool = False,
    ) -> None:
        self.config = config
        self.paused = paused
        self.commands_enabled = commands_enabled
        self._pinch_started_at: float | None = None
        self._mouse_is_down = False
        self._command_candidate: str | None = None
        self._command_started_at: float | None = None
        self._command_fired = False
        self._last_copy_at = -999.0
        self._last_paste_at = -999.0

    def toggle_pause(self, mouse: MouseController) -> bool:
        self.paused = not self.paused
        if self.paused:
            self.cancel_pointer_interaction(mouse)
        return self.paused

    def cancel_pointer_interaction(self, mouse: MouseController) -> None:
        if self._mouse_is_down:
            mouse.mouse_up()
        self._pinch_started_at = None
        self._mouse_is_down = False

    def update(
        self,
        gesture: Gesture,
        now: float,
        mouse: MouseController,
        keyboard: KeyboardController,
    ) -> StateUpdate:
        if self.paused:
            self.cancel_pointer_interaction(mouse)
            return StateUpdate(ControllerState.PAUSED)

        pinch_update = self._update_pinch(gesture, now, mouse)
        if self.commands_enabled:
            command_update = self._update_command(gesture, now, keyboard)
            if command_update.action:
                return command_update
        if pinch_update.state in {ControllerState.PINCHING, ControllerState.DRAGGING}:
            return pinch_update
        if gesture == Gesture.MOVE:
            return StateUpdate(ControllerState.MOVING)
        return StateUpdate(ControllerState.IDLE)

    def _update_pinch(
        self, gesture: Gesture, now: float, mouse: MouseController
    ) -> StateUpdate:
        if gesture == Gesture.PINCH:
            if self._pinch_started_at is None:
                self._pinch_started_at = now
                self._mouse_is_down = False
                return StateUpdate(ControllerState.PINCHING)

            held_for = now - self._pinch_started_at
            if not self._mouse_is_down and held_for >= self.config.drag_hold_seconds:
                mouse.mouse_down()
                self._mouse_is_down = True
                return StateUpdate(ControllerState.DRAGGING, "mouse down")

            if self._mouse_is_down:
                return StateUpdate(ControllerState.DRAGGING)
            return StateUpdate(ControllerState.PINCHING)

        if self._pinch_started_at is None:
            return StateUpdate(ControllerState.IDLE)

        held_for = now - self._pinch_started_at
        was_dragging = self._mouse_is_down
        self._pinch_started_at = None
        self._mouse_is_down = False

        if was_dragging:
            mouse.mouse_up()
            return StateUpdate(ControllerState.IDLE, "mouse up")

        if held_for <= self.config.click_max_seconds:
            mouse.click()
            return StateUpdate(ControllerState.IDLE, "left click")

        return StateUpdate(ControllerState.IDLE)

    def _update_command(
        self, gesture: Gesture, now: float, keyboard: KeyboardController
    ) -> StateUpdate:
        command = None
        hold_seconds = 0.0
        if gesture in {Gesture.FIST, Gesture.TWO_FISTS}:
            command = "copy"
            hold_seconds = self.config.copy_hold_seconds
        elif gesture in {Gesture.THUMBS_UP, Gesture.V_SIGN, Gesture.TWO_V_SIGNS}:
            command = "paste"
            hold_seconds = self.config.paste_hold_seconds

        if command is None:
            self._command_candidate = None
            self._command_started_at = None
            self._command_fired = False
            return StateUpdate(ControllerState.IDLE)

        state = (
            ControllerState.COPY_ARMED
            if command == "copy"
            else ControllerState.PASTE_ARMED
        )

        if self._command_candidate != command:
            self._command_candidate = command
            self._command_started_at = now
            self._command_fired = False
            return StateUpdate(state)

        if self._command_fired or self._command_started_at is None:
            return StateUpdate(state)

        held_for = now - self._command_started_at
        if held_for < hold_seconds:
            return StateUpdate(state)

        if command == "copy":
            if now - self._last_copy_at < self.config.command_cooldown_seconds:
                return StateUpdate(state)
            keyboard.copy()
            self._last_copy_at = now
            self._command_fired = True
            return StateUpdate(state, "Ctrl+C")

        if now - self._last_paste_at < self.config.command_cooldown_seconds:
            return StateUpdate(state)
        keyboard.paste()
        self._last_paste_at = now
        self._command_fired = True
        return StateUpdate(state, "Ctrl+V")
