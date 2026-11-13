import unittest

from hand_gesture_controller.config import GestureConfig
from hand_gesture_controller.gesture_detector import (
    Gesture,
    GestureDetector,
    combine_gestures,
)
from hand_gesture_controller.models import LandmarkPoint


def landmarks() -> list[LandmarkPoint]:
    points = [LandmarkPoint(0.5, 0.6) for _ in range(21)]
    points[0] = LandmarkPoint(0.5, 0.85)
    points[4] = LandmarkPoint(0.34, 0.60)
    points[5] = LandmarkPoint(0.45, 0.60)
    points[6] = LandmarkPoint(0.45, 0.50)
    points[8] = LandmarkPoint(0.45, 0.66)
    points[9] = LandmarkPoint(0.50, 0.58)
    points[10] = LandmarkPoint(0.50, 0.49)
    points[12] = LandmarkPoint(0.50, 0.65)
    points[14] = LandmarkPoint(0.55, 0.51)
    points[16] = LandmarkPoint(0.55, 0.66)
    points[18] = LandmarkPoint(0.60, 0.53)
    points[20] = LandmarkPoint(0.60, 0.67)
    return points


class GestureDetectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.detector = GestureDetector(GestureConfig())

    def test_fist_is_detected(self) -> None:
        frame = self.detector.detect(landmarks())
        self.assertEqual(frame.gesture, Gesture.FIST)

    def test_thumbs_up_is_detected(self) -> None:
        points = landmarks()
        points[4] = LandmarkPoint(0.38, 0.30)

        frame = self.detector.detect(points)

        self.assertEqual(frame.gesture, Gesture.THUMBS_UP)

    def test_v_sign_is_detected(self) -> None:
        points = landmarks()
        points[8] = LandmarkPoint(0.45, 0.25)
        points[12] = LandmarkPoint(0.50, 0.24)

        frame = self.detector.detect(points)

        self.assertEqual(frame.gesture, Gesture.V_SIGN)

    def test_pinch_is_detected_before_move(self) -> None:
        points = landmarks()
        points[8] = LandmarkPoint(0.39, 0.45)
        points[4] = LandmarkPoint(0.40, 0.46)

        frame = self.detector.detect(points)

        self.assertEqual(frame.gesture, Gesture.PINCH)
        self.assertIsNotNone(frame.pointer)

    def test_two_fists_are_combined_as_copy_gesture(self) -> None:
        first = self.detector.detect(landmarks())
        second = self.detector.detect(landmarks())

        self.assertEqual(combine_gestures([first, second]), Gesture.TWO_FISTS)

    def test_two_v_signs_are_combined_as_paste_gesture(self) -> None:
        first_points = landmarks()
        first_points[8] = LandmarkPoint(0.45, 0.25)
        first_points[12] = LandmarkPoint(0.50, 0.24)
        second_points = landmarks()
        second_points[8] = LandmarkPoint(0.55, 0.25)
        second_points[12] = LandmarkPoint(0.60, 0.24)

        first = self.detector.detect(first_points)
        second = self.detector.detect(second_points)

        self.assertEqual(combine_gestures([first, second]), Gesture.TWO_V_SIGNS)


if __name__ == "__main__":
    unittest.main()
