import unittest

from hand_gesture_controller.action_profile import ActionProfile
from hand_gesture_controller.action_runner import ActionRunner, RuntimeControls
from hand_gesture_controller.binding_engine import BindingEngine, HandObservation
from hand_gesture_controller.gesture_detector import Gesture, GestureFrame
from hand_gesture_controller.models import HandResult, LandmarkPoint


def hand(handedness: str) -> HandResult:
    return HandResult(
        landmarks=[LandmarkPoint(0.1 * index, 0.1 * index) for index in range(21)],
        handedness=handedness,
        raw_landmarks=None,
    )


def observation(handedness: str, gesture: Gesture) -> HandObservation:
    return HandObservation(
        hand=hand(handedness),
        gesture_frame=GestureFrame(gesture, None, 0.0, {}),
        custom_gestures=[],
    )


class FakeKeyboard:
    def __init__(self) -> None:
        self.calls = []

    def hotkey(self, *keys: str) -> None:
        self.calls.append(("hotkey", keys))

    def press(self, key: str) -> None:
        self.calls.append(("press", key))

    def write_text(self, value: str) -> None:
        self.calls.append(("text", value))


class ActionBindingTests(unittest.TestCase):
    def test_higher_priority_two_hand_binding_wins(self) -> None:
        profile = ActionProfile(
            path=None,
            bindings=[
                {
                    "name": "left_fist",
                    "gesture": "fist",
                    "hands": ["Left"],
                    "hold_seconds": 0.1,
                    "cooldown_seconds": 1.0,
                    "priority": 10,
                    "action": {"type": "toggle_mouse"},
                },
                {
                    "name": "two_fists",
                    "gesture": "two_fists",
                    "hands": ["Left", "Right"],
                    "hold_seconds": 0.1,
                    "cooldown_seconds": 1.0,
                    "priority": 100,
                    "action": {"type": "hotkey", "keys": ["ctrl", "c"]},
                },
            ],
        )
        engine = BindingEngine(profile)
        observations = [
            observation("Left", Gesture.FIST),
            observation("Right", Gesture.FIST),
        ]

        self.assertIsNone(engine.update(observations, Gesture.TWO_FISTS, 0.0))
        event = engine.update(observations, Gesture.TWO_FISTS, 0.2)

        self.assertIsNotNone(event)
        self.assertEqual(event.name, "two_fists")

    def test_custom_gesture_can_match_binding(self) -> None:
        profile = ActionProfile(
            path=None,
            bindings=[
                {
                    "name": "custom_copy",
                    "gesture": "custom_copy",
                    "hands": ["Left"],
                    "hold_seconds": 0.1,
                    "cooldown_seconds": 1.0,
                    "priority": 50,
                    "action": {"type": "hotkey", "keys": ["ctrl", "c"]},
                }
            ],
        )
        engine = BindingEngine(profile)
        obs = observation("Left", Gesture.NONE)
        obs = HandObservation(obs.hand, obs.gesture_frame, ["custom_copy"])

        self.assertIsNone(engine.update([obs], Gesture.NONE, 0.0))
        event = engine.update([obs], Gesture.NONE, 0.2)

        self.assertIsNotNone(event)
        self.assertEqual(event.name, "custom_copy")

    def test_action_runner_toggles_mouse(self) -> None:
        controls = RuntimeControls(mouse_enabled=True)
        runner = ActionRunner(FakeKeyboard(), controls, dry_run=True)

        label = runner.run({"type": "toggle_mouse"})

        self.assertEqual(label, "mouse off")
        self.assertFalse(controls.mouse_enabled)


if __name__ == "__main__":
    unittest.main()

