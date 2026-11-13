import unittest

from hand_gesture_controller.config import MediaGestureConfig
from hand_gesture_controller.screen_context import ActiveWindow, classify_active_window


class ScreenContextTests(unittest.TestCase):
    def test_player_process_is_media(self) -> None:
        context = classify_active_window(
            ActiveWindow(title="Movie", process_name="vlc.exe"),
            MediaGestureConfig(),
        )

        self.assertTrue(context.is_media)
        self.assertEqual(context.reason, "player process")

    def test_browser_video_title_is_media(self) -> None:
        context = classify_active_window(
            ActiveWindow(title="My Video - YouTube", process_name="chrome.exe"),
            MediaGestureConfig(),
        )

        self.assertTrue(context.is_media)
        self.assertIn("youtube", context.reason)

    def test_browser_without_video_keyword_is_not_media(self) -> None:
        context = classify_active_window(
            ActiveWindow(title="Inbox", process_name="chrome.exe"),
            MediaGestureConfig(),
        )

        self.assertFalse(context.is_media)


if __name__ == "__main__":
    unittest.main()
