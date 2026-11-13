from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .action_profile import ActionProfile, BindingEvent
from .gesture_detector import Gesture, GestureFrame
from .models import HandResult


@dataclass(frozen=True)
class HandObservation:
    hand: HandResult
    gesture_frame: GestureFrame
    custom_gestures: list[str]


@dataclass
class _BindingState:
    started_at: float | None = None
    fired: bool = False
    last_fired_at: float = -999.0


class BindingEngine:
    def __init__(self, profile: ActionProfile) -> None:
        self.profile = profile
        self._states: dict[str, _BindingState] = {}

    def update(
        self,
        observations: list[HandObservation],
        effective_gesture: Gesture,
        now: float,
    ) -> BindingEvent | None:
        bindings = self.profile.sorted_bindings()
        active_name = None

        for binding in bindings:
            name = str(binding.get("name", "unnamed"))
            if not self._matches(binding, observations, effective_gesture):
                self._reset(name)
                continue

            active_name = name
            event = self._update_matched_binding(binding, now)
            break
        else:
            event = None

        for binding in bindings:
            name = str(binding.get("name", "unnamed"))
            if name != active_name:
                self._reset(name)

        return event

    def _update_matched_binding(
        self, binding: dict[str, Any], now: float
    ) -> BindingEvent | None:
        name = str(binding.get("name", "unnamed"))
        state = self._states.setdefault(name, _BindingState())

        if state.started_at is None:
            state.started_at = now
            state.fired = False
            return None

        hold_seconds = float(binding.get("hold_seconds", 0.0))
        cooldown_seconds = float(binding.get("cooldown_seconds", 1.0))
        if state.fired or now - state.started_at < hold_seconds:
            return None
        if now - state.last_fired_at < cooldown_seconds:
            return None

        state.fired = True
        state.last_fired_at = now
        action = binding.get("action", {"type": "noop"})
        return BindingEvent(name=name, action=action)

    def _reset(self, name: str) -> None:
        state = self._states.get(name)
        if state is None:
            return
        state.started_at = None
        state.fired = False

    def _matches(
        self,
        binding: dict[str, Any],
        observations: list[HandObservation],
        effective_gesture: Gesture,
    ) -> bool:
        gesture_name = str(binding.get("gesture", "none"))
        hands = [str(hand) for hand in binding.get("hands", ["any"])]

        if gesture_name == effective_gesture.value and len(hands) > 1:
            return self._has_required_hands(hands, observations)

        if hands == ["any"]:
            return any(
                self._observation_has_gesture(observation, gesture_name)
                for observation in observations
            )

        return all(
            any(
                self._hand_name_matches(required_hand, observation.hand.handedness)
                and self._observation_has_gesture(observation, gesture_name)
                for observation in observations
            )
            for required_hand in hands
        )

    def _has_required_hands(
        self, required_hands: list[str], observations: list[HandObservation]
    ) -> bool:
        return all(
            any(self._hand_name_matches(hand, observation.hand.handedness) for observation in observations)
            for hand in required_hands
        )

    @staticmethod
    def _hand_name_matches(required: str, actual: str) -> bool:
        return required.lower() in {"any", actual.lower()}

    @staticmethod
    def _observation_has_gesture(
        observation: HandObservation, gesture_name: str
    ) -> bool:
        return (
            observation.gesture_frame.gesture.value == gesture_name
            or gesture_name in observation.custom_gestures
        )

