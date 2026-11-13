import tempfile
import unittest
from pathlib import Path

from hand_gesture_controller.models import HandResult, LandmarkPoint
from hand_gesture_controller.pose_templates import PoseTemplateStore


def sample_hand(offset: float = 0.0) -> HandResult:
    points = [LandmarkPoint(0.5 + offset, 0.8, 0.0)]
    for index in range(1, 21):
        points.append(
            LandmarkPoint(
                0.5 + offset + (index % 5) * 0.02,
                0.8 - (index // 5) * 0.05,
                0.0,
            )
        )
    return HandResult(points, "Left", None)


class PoseTemplateTests(unittest.TestCase):
    def test_recorded_pose_matches_same_shape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = PoseTemplateStore(Path(directory) / "gestures.json")
            template = store.record(sample_hand(), name="custom_copy")

            matches = store.match(sample_hand(offset=0.2))

            self.assertEqual(template.name, "custom_copy")
            self.assertIn("custom_copy", matches)


if __name__ == "__main__":
    unittest.main()

