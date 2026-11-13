import unittest

from hand_gesture_controller.config import MediaGestureConfig
from hand_gesture_controller.media_control import HybridMediaController, NativeMediaInfo
from hand_gesture_controller.screen_context import ScreenContext


class FakeKeyboard:
    def __init__(self) -> None:
        self.keys = []

    def press(self, key: str) -> None:
        self.keys.append(key)


class FakeNative:
    def __init__(self, succeeds: bool, info: NativeMediaInfo | None = None) -> None:
        self.succeeds = succeeds
        self.info = info or NativeMediaInfo(False, detail="no current media session")
        self.toggles = 0
        self.seeks = []

    def get_info(self, now=None) -> NativeMediaInfo:
        return self.info

    def toggle_play_pause(self) -> bool:
        self.toggles += 1
        return self.succeeds

    def seek_relative(self, seconds: float) -> bool:
        self.seeks.append(seconds)
        return self.succeeds


MEDIA = ScreenContext(True, "Video", "chrome.exe", "browser video: video")


class HybridMediaControllerTests(unittest.TestCase):
    def test_uses_native_when_available(self) -> None:
        keyboard = FakeKeyboard()
        native = FakeNative(True)
        controller = HybridMediaController(MediaGestureConfig(), keyboard, native)

        label = controller.seek_forward(MEDIA)

        self.assertEqual(label, "native seek forward")
        self.assertEqual(native.seeks, [10.0])
        self.assertEqual(keyboard.keys, [])

    def test_falls_back_to_keyboard_when_native_fails(self) -> None:
        keyboard = FakeKeyboard()
        native = FakeNative(False)
        controller = HybridMediaController(MediaGestureConfig(), keyboard, native)

        label = controller.play_pause(MEDIA)

        self.assertEqual(label, "key play/pause")
        self.assertEqual(native.toggles, 1)
        self.assertEqual(keyboard.keys, ["space"])

    def test_disabled_native_goes_straight_to_keyboard(self) -> None:
        keyboard = FakeKeyboard()
        native = FakeNative(True)
        config = MediaGestureConfig(use_native_media_controls=False)
        controller = HybridMediaController(config, keyboard, native)

        label = controller.seek_backward(MEDIA)

        self.assertEqual(label, "key seek backward")
        self.assertEqual(native.seeks, [])
        self.assertEqual(keyboard.keys, ["left"])

    def test_youtube_fallback_uses_player_shortcuts(self) -> None:
        keyboard = FakeKeyboard()
        config = MediaGestureConfig(use_native_media_controls=False)
        controller = HybridMediaController(config, keyboard, FakeNative(False))
        youtube = ScreenContext(True, "Clip - YouTube", "chrome.exe", "browser video: youtube")

        controller.play_pause(youtube)
        controller.seek_forward(youtube)
        controller.seek_backward(youtube)

        self.assertEqual(keyboard.keys, ["k", "l", "j"])

    def test_native_session_becomes_the_media_context(self) -> None:
        native = FakeNative(
            True,
            NativeMediaInfo(True, title="Song", artist="Band", app_id="vlc.exe"),
        )
        controller = HybridMediaController(MediaGestureConfig(), FakeKeyboard(), native)

        context = controller.native_context(0.0)

        self.assertTrue(context.is_media)
        self.assertEqual(context.title, "Song")
        self.assertEqual(context.process_name, "vlc.exe")

    def test_no_native_session_leaves_context_empty(self) -> None:
        controller = HybridMediaController(
            MediaGestureConfig(), FakeKeyboard(), FakeNative(False)
        )

        self.assertFalse(controller.native_context(0.0).is_media)


if __name__ == "__main__":
    unittest.main()
