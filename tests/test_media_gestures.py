from __future__ import annotations

import unittest

from hand_gesture_controller.binding_engine import HandObservation
from hand_gesture_controller.config import MediaGestureConfig
from hand_gesture_controller.gesture_detector import Gesture, GestureFrame
from hand_gesture_controller.main import _observations_for_bindings
from hand_gesture_controller.media_control import HybridMediaController
from hand_gesture_controller.media_gestures import (
    MediaGestureController,
    MediaGestureUpdate,
)
from hand_gesture_controller.models import HandResult, LandmarkPoint
from hand_gesture_controller.screen_context import ScreenContext


class FakeKeyboard:
    def __init__(self) -> None:
        self.keys = []

    def press(self, key: str) -> None:
        self.keys.append(key)


def make_controller(
    keyboard: FakeKeyboard,
    config: MediaGestureConfig | None = None,
) -> MediaGestureController:
    """Controller con la sessione media nativa disattivata: usa i tasti."""
    config = config or MediaGestureConfig(use_native_media_controls=False)
    return MediaGestureController(config, HybridMediaController(config, keyboard))


def observation(x: float, y: float = 0.5, handedness: str = "Right") -> HandObservation:
    landmarks = [LandmarkPoint(x, y) for _ in range(21)]
    return HandObservation(
        hand=HandResult(landmarks, handedness, raw_landmarks=None),
        gesture_frame=GestureFrame(Gesture.FIST, None, 0.0, {}),
        custom_gestures=[],
    )


MEDIA_CONTEXT = ScreenContext(
    True,
    title="Example Video",
    process_name="chrome.exe",
    reason="browser video: video",
)

YOUTUBE_CONTEXT = ScreenContext(
    True,
    title="Example - YouTube",
    process_name="chrome.exe",
    reason="browser video: youtube",
)


class MediaGestureControllerTests(unittest.TestCase):
    def test_stationary_fist_toggles_play_pause(self) -> None:
        keyboard = FakeKeyboard()
        controller = make_controller(keyboard)

        controller.update([observation(0.5)], MEDIA_CONTEXT, 0.0)
        update = controller.update([observation(0.51)], MEDIA_CONTEXT, 0.6)

        self.assertEqual(keyboard.keys, ["space"])
        self.assertEqual(update.action, "key play/pause")

    def test_fist_swipe_right_seeks_forward(self) -> None:
        keyboard = FakeKeyboard()
        controller = make_controller(keyboard)

        controller.update([observation(0.35)], MEDIA_CONTEXT, 0.0)
        update = controller.update([observation(0.54)], MEDIA_CONTEXT, 0.25)

        self.assertEqual(keyboard.keys, ["right"])
        self.assertEqual(update.action, "key seek forward")

    def test_fist_swipe_left_seeks_backward(self) -> None:
        keyboard = FakeKeyboard()
        controller = make_controller(keyboard)

        controller.update([observation(0.65)], MEDIA_CONTEXT, 0.0)
        update = controller.update([observation(0.46)], MEDIA_CONTEXT, 0.25)

        self.assertEqual(keyboard.keys, ["left"])
        self.assertEqual(update.action, "key seek backward")

    def test_seek_repeats_while_right_fist_stays_closed(self) -> None:
        keyboard = FakeKeyboard()
        controller = make_controller(keyboard)

        controller.update([observation(0.35)], MEDIA_CONTEXT, 0.0)
        controller.update([observation(0.54)], MEDIA_CONTEXT, 0.25)
        controller.update([observation(0.75)], MEDIA_CONTEXT, 0.50)
        controller.update([observation(0.75)], MEDIA_CONTEXT, 0.61)

        self.assertEqual(keyboard.keys, ["right", "right"])

    def test_pause_does_not_repeat_until_right_fist_released(self) -> None:
        keyboard = FakeKeyboard()
        controller = make_controller(keyboard)

        controller.update([observation(0.5)], MEDIA_CONTEXT, 0.0)
        controller.update([observation(0.51)], MEDIA_CONTEXT, 0.6)
        controller.update([observation(0.51)], MEDIA_CONTEXT, 1.2)

        self.assertEqual(keyboard.keys, ["space"])

    def test_left_fist_is_ignored_for_media_controls(self) -> None:
        keyboard = FakeKeyboard()
        controller = make_controller(keyboard)

        update = controller.update(
            [observation(0.35, handedness="Left")],
            MEDIA_CONTEXT,
            0.0,
        )

        self.assertTrue(update.active)
        self.assertFalse(update.consumed)
        self.assertEqual(keyboard.keys, [])

    def test_non_media_context_does_not_send_keys(self) -> None:
        keyboard = FakeKeyboard()
        controller = make_controller(keyboard)
        context = ScreenContext(False, title="Inbox", process_name="chrome.exe")

        update = controller.update([observation(0.5)], context, 0.0)

        self.assertFalse(update.active)
        self.assertEqual(keyboard.keys, [])

    def test_youtube_uses_native_player_shortcut_keys(self) -> None:
        keyboard = FakeKeyboard()
        controller = make_controller(keyboard)

        controller.update([observation(0.35)], YOUTUBE_CONTEXT, 0.0)
        controller.update([observation(0.54)], YOUTUBE_CONTEXT, 0.25)

        self.assertEqual(keyboard.keys, ["l"])


class BindingObservationsTests(unittest.TestCase):
    """Le gesture media non devono zittire i comandi dell'altra mano."""

    def test_consumed_hides_only_the_media_hand(self) -> None:
        hands = [observation(0.5, handedness="Right"), observation(0.5, handedness="Left")]

        kept = _observations_for_bindings(
            hands, MediaGestureUpdate(active=True, consumed=True), "Right"
        )

        self.assertEqual([o.hand.handedness for o in kept], ["Left"])

    def test_nothing_is_hidden_when_media_did_not_consume(self) -> None:
        hands = [observation(0.5, handedness="Right"), observation(0.5, handedness="Left")]

        kept = _observations_for_bindings(
            hands, MediaGestureUpdate(active=True, consumed=False), "Right"
        )

        self.assertEqual(kept, hands)

    def test_the_media_hand_is_matched_case_insensitively(self) -> None:
        hands = [observation(0.5, handedness="Right")]

        kept = _observations_for_bindings(
            hands, MediaGestureUpdate(active=True, consumed=True), "right"
        )

        self.assertEqual(kept, [])


if __name__ == "__main__":
    unittest.main()
