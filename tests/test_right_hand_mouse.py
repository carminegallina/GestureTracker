import unittest

from hand_gesture_controller.binding_engine import HandObservation
from hand_gesture_controller.config import GestureConfig
from hand_gesture_controller.gesture_detector import Gesture, GestureFrame
from hand_gesture_controller.models import HandResult, LandmarkPoint
from hand_gesture_controller.right_hand_mouse import RightHandMouseController


class FakeMouse:
    def __init__(self) -> None:
        self.calls = []

    def click(self) -> None:
        self.calls.append("click")

    def double_click(self) -> None:
        self.calls.append("double_click")

    def right_click(self) -> None:
        self.calls.append("right_click")

    def mouse_down(self) -> None:
        self.calls.append("mouse_down")

    def mouse_up(self) -> None:
        self.calls.append("mouse_up")


def observation(
    index_up: bool = True,
    middle_up: bool = True,
    ring_up: bool = True,
) -> HandObservation:
    points = [LandmarkPoint(0.5, 0.5) for _ in range(21)]
    return HandObservation(
        hand=HandResult(points, "Right", None),
        gesture_frame=GestureFrame(
            gesture=Gesture.MOVE,
            pointer=points[8],
            pinch_distance=1.0,
            extended_fingers={
                "index": index_up,
                "middle": middle_up,
                "ring": ring_up,
                "pinky": True,
            },
        ),
        custom_gestures=[],
    )


class RightHandMouseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.controller = RightHandMouseController(GestureConfig())
        self.mouse = FakeMouse()

    def test_middle_down_short_tap_becomes_left_click_after_delay(self) -> None:
        self.controller.update(observation(middle_up=True), 0.0, self.mouse)
        self.controller.update(observation(middle_up=False), 0.1, self.mouse)
        self.controller.update(observation(middle_up=True), 0.18, self.mouse)
        self.controller.update(observation(middle_up=True), 0.60, self.mouse)

        self.assertEqual(self.mouse.calls, ["click"])

    def test_two_middle_taps_become_double_click(self) -> None:
        self.controller.update(observation(middle_up=True), 0.0, self.mouse)
        self.controller.update(observation(middle_up=False), 0.10, self.mouse)
        self.controller.update(observation(middle_up=True), 0.16, self.mouse)
        self.controller.update(observation(middle_up=False), 0.24, self.mouse)
        update = self.controller.update(observation(middle_up=True), 0.30, self.mouse)

        self.assertEqual(self.mouse.calls, ["click", "click"])
        self.assertEqual(update.action, "left double click")

    def test_middle_hold_drags_until_release(self) -> None:
        self.controller.update(observation(middle_up=True), 0.0, self.mouse)
        self.controller.update(observation(middle_up=False), 0.1, self.mouse)
        self.controller.update(observation(middle_up=False), 0.4, self.mouse)
        self.controller.update(observation(middle_up=True), 0.5, self.mouse)

        self.assertEqual(self.mouse.calls, ["mouse_down", "mouse_up"])

    def test_ring_down_clicks_right_button(self) -> None:
        self.controller.update(observation(ring_up=True), 0.0, self.mouse)
        self.controller.update(observation(middle_up=True, ring_up=False), 0.1, self.mouse)
        self.controller.update(observation(middle_up=True, ring_up=False), 0.3, self.mouse)

        self.assertEqual(self.mouse.calls, ["right_click"])


if __name__ == "__main__":
    unittest.main()
