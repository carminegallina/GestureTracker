import unittest

from hand_gesture_controller.mouse_controller import ScreenPoint
from hand_gesture_controller.pointer_stabilizer import PointerStabilizer


class PointerStabilizerTests(unittest.TestCase):
    def test_button_press_holds_initial_pointer(self) -> None:
        stabilizer = PointerStabilizer(freeze_seconds=0.12)

        first = stabilizer.update(
            ScreenPoint(100, 100),
            button_active=True,
            dragging=False,
            now=1.0,
        )
        second = stabilizer.update(
            ScreenPoint(400, 400),
            button_active=True,
            dragging=False,
            now=1.05,
        )

        self.assertEqual(first.point, ScreenPoint(100, 100))
        self.assertEqual(second.point, ScreenPoint(100, 100))
        self.assertTrue(second.is_holding)

    def test_dragging_releases_pointer_hold(self) -> None:
        stabilizer = PointerStabilizer(freeze_seconds=0.12)
        stabilizer.update(
            ScreenPoint(100, 100),
            button_active=True,
            dragging=False,
            now=1.0,
        )

        update = stabilizer.update(
            ScreenPoint(400, 400),
            button_active=True,
            dragging=True,
            now=1.2,
        )

        self.assertEqual(update.point, ScreenPoint(400, 400))
        self.assertFalse(update.is_holding)


if __name__ == "__main__":
    unittest.main()

