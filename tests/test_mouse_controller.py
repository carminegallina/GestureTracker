import unittest

from hand_gesture_controller.config import PointerConfig
from hand_gesture_controller.models import LandmarkPoint
from hand_gesture_controller.mouse_controller import MouseController, ScreenRect


class MouseControllerMappingTests(unittest.TestCase):
    def test_sensitivity_below_one_still_reaches_screen_edges(self) -> None:
        mouse = MouseController(
            dry_run=True,
            screen_rect=ScreenRect(0, 0, 3200, 1080),
        )
        config = PointerConfig(
            active_zone_left=0.18,
            active_zone_top=0.28,
            active_zone_right=0.82,
            active_zone_bottom=0.92,
            sensitivity=0.85,
            smoothing_alpha=0.22,
            dead_zone_px=5,
        )

        top_left = mouse.landmark_to_screen(LandmarkPoint(0.18, 0.28), config)
        bottom_right = mouse.landmark_to_screen(LandmarkPoint(0.82, 0.92), config)

        self.assertEqual((top_left.x, top_left.y), (0, 0))
        self.assertEqual((bottom_right.x, bottom_right.y), (3199, 1079))

    def test_manual_screen_rect_edges_are_respected(self) -> None:
        mouse = MouseController(
            dry_run=True,
            screen_rect=ScreenRect(1920, 0, 1280, 720),
        )
        config = PointerConfig()

        top_left = mouse.landmark_to_screen(
            LandmarkPoint(config.active_zone_left, config.active_zone_top), config
        )
        bottom_right = mouse.landmark_to_screen(
            LandmarkPoint(config.active_zone_right, config.active_zone_bottom), config
        )

        self.assertEqual((top_left.x, top_left.y), (1920, 0))
        self.assertEqual((bottom_right.x, bottom_right.y), (3199, 719))


if __name__ == "__main__":
    unittest.main()

