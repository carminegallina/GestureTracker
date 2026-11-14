import unittest

import cv2

from hand_gesture_controller.main import debug_window_is_open


class DebugWindowIsOpenTests(unittest.TestCase):
    """La X deve chiudere l'app, non far ricreare la finestra al frame dopo."""

    def setUp(self) -> None:
        self._original = cv2.getWindowProperty
        self.addCleanup(setattr, cv2, "getWindowProperty", self._original)

    def fake_property(self, value):
        def getter(name: str, prop: int) -> float:
            self.asked = (name, prop)
            return value

        cv2.getWindowProperty = getter

    def test_open_window(self) -> None:
        self.fake_property(1.0)

        self.assertTrue(debug_window_is_open("tracker"))
        self.assertEqual(self.asked, ("tracker", cv2.WND_PROP_VISIBLE))

    def test_closed_window(self) -> None:
        self.fake_property(0.0)

        self.assertFalse(debug_window_is_open("tracker"))

    def test_missing_window(self) -> None:
        self.fake_property(-1.0)

        self.assertFalse(debug_window_is_open("tracker"))

    def test_opencv_error_counts_as_closed(self) -> None:
        def raising(name: str, prop: int) -> float:
            raise cv2.error("no such window")

        cv2.getWindowProperty = raising

        self.assertFalse(debug_window_is_open("tracker"))


if __name__ == "__main__":
    unittest.main()
