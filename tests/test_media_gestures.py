import unittest

from hand_gesture_controller.binding_engine import HandObservation
from hand_gesture_controller.config import MediaGestureConfig
from hand_gesture_controller.gesture_detector import Gesture, GestureFrame
from hand_gesture_controller.media_gestures import MediaGestureController
from hand_gesture_controller.models import HandResult, LandmarkPoint
from hand_gesture_controller.screen_context import ScreenContext


class FakeKeyboard:
    def __init__(self) -> None:
        self.keys = []

    def press(self, key: str) -> None:
        self.keys.append(key)


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
        controller = MediaGestureController(MediaGestureConfig(), keyboard)

        controller.update([observation(0.5)], MEDIA_CONTEXT, 0.0)
        update = controller.update([observation(0.51)], MEDIA_CONTEXT, 0.6)

        self.assertEqual(keyboard.keys, ["space"])
        self.assertEqual(update.action, "play/pause")

    def test_fist_swipe_right_seeks_forward(self) -> None:
        keyboard = FakeKeyboard()
        controller = MediaGestureController(MediaGestureConfig(), keyboard)

        controller.update([observation(0.35)], MEDIA_CONTEXT, 0.0)
        update = controller.update([observation(0.54)], MEDIA_CONTEXT, 0.25)

        self.assertEqual(keyboard.keys, ["right"])
        self.assertEqual(update.action, "seek forward")

    def test_fist_swipe_left_seeks_backward(self) -> None:
        keyboard = FakeKeyboard()
        controller = MediaGestureController(MediaGestureConfig(), keyboard)

        controller.update([observation(0.65)], MEDIA_CONTEXT, 0.0)
        update = controller.update([observation(0.46)], MEDIA_CONTEXT, 0.25)

        self.assertEqual(keyboard.keys, ["left"])
        self.assertEqual(update.action, "seek backward")

    def test_seek_repeats_while_right_fist_stays_closed(self) -> None:
        keyboard = FakeKeyboard()
        controller = MediaGestureController(MediaGestureConfig(), keyboard)

        controller.update([observation(0.35)], MEDIA_CONTEXT, 0.0)
        controller.update([observation(0.54)], MEDIA_CONTEXT, 0.25)
        controller.update([observation(0.75)], MEDIA_CONTEXT, 0.50)
        controller.update([observation(0.75)], MEDIA_CONTEXT, 0.61)

        self.assertEqual(keyboard.keys, ["right", "right"])

    def test_pause_does_not_repeat_until_right_fist_released(self) -> None:
        keyboard = FakeKeyboard()
        controller = MediaGestureController(MediaGestureConfig(), keyboard)

        controller.update([observation(0.5)], MEDIA_CONTEXT, 0.0)
        controller.update([observation(0.51)], MEDIA_CONTEXT, 0.6)
        controller.update([observation(0.51)], MEDIA_CONTEXT, 1.2)

        self.assertEqual(keyboard.keys, ["space"])

    def test_left_fist_is_ignored_for_media_controls(self) -> None:
        keyboard = FakeKeyboard()
        controller = MediaGestureController(MediaGestureConfig(), keyboard)

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
        controller = MediaGestureController(MediaGestureConfig(), keyboard)
        context = ScreenContext(False, title="Inbox", process_name="chrome.exe")

        update = controller.update([observation(0.5)], context, 0.0)

        self.assertFalse(update.active)
        self.assertEqual(keyboard.keys, [])

    def test_youtube_uses_native_player_shortcut_keys(self) -> None:
        keyboard = FakeKeyboard()
        controller = MediaGestureController(MediaGestureConfig(), keyboard)

        controller.update([observation(0.35)], YOUTUBE_CONTEXT, 0.0)
        controller.update([observation(0.54)], YOUTUBE_CONTEXT, 0.25)

        self.assertEqual(keyboard.keys, ["l"])


if __name__ == "__main__":
    unittest.main()
