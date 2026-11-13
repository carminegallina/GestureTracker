import unittest

import numpy as np

from hand_gesture_controller.config import AppConfig, CameraConfig, VirtualCameraConfig
from hand_gesture_controller.main import _virtual_camera_frame


class VirtualCameraFrameTests(unittest.TestCase):
    def test_default_virtual_camera_unmirrors_debug_frame(self) -> None:
        frame = np.array([[[1, 0, 0], [2, 0, 0], [3, 0, 0]]], dtype=np.uint8)
        config = AppConfig(
            camera=CameraConfig(mirror=True),
            virtual_camera=VirtualCameraConfig(mirror=False),
        )

        output = _virtual_camera_frame(frame, config)

        self.assertEqual(output[0, :, 0].tolist(), [3, 2, 1])

    def test_virtual_camera_mirror_keeps_mirrored_debug_frame(self) -> None:
        frame = np.array([[[1, 0, 0], [2, 0, 0], [3, 0, 0]]], dtype=np.uint8)
        config = AppConfig(
            camera=CameraConfig(mirror=True),
            virtual_camera=VirtualCameraConfig(mirror=True),
        )

        output = _virtual_camera_frame(frame, config)

        self.assertIs(output, frame)

    def test_unmirrored_camera_stays_unmirrored_by_default(self) -> None:
        frame = np.array([[[1, 0, 0], [2, 0, 0], [3, 0, 0]]], dtype=np.uint8)
        config = AppConfig(
            camera=CameraConfig(mirror=False),
            virtual_camera=VirtualCameraConfig(mirror=False),
        )

        output = _virtual_camera_frame(frame, config)

        self.assertIs(output, frame)


if __name__ == "__main__":
    unittest.main()
