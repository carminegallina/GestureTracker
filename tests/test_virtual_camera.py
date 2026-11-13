import time
import unittest

import numpy as np

from hand_gesture_controller.config import VirtualCameraConfig
from hand_gesture_controller.virtual_camera import (
    VirtualCameraRelay,
    VirtualCameraState,
)


def wait_until(predicate, timeout: float = 1.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


class FakeVirtualCamera:
    instances = []

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.frames = []
        self.closed = False
        self.device = "Fake Virtual Camera"
        self.backend = "fake"
        FakeVirtualCamera.instances.append(self)

    def send(self, frame) -> None:
        self.frames.append(frame.copy())

    def sleep_until_next_frame(self) -> None:
        return None

    def close(self) -> None:
        self.closed = True


class VirtualCameraRelayTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeVirtualCamera.instances = []

    def test_disabled_relay_does_not_start_backend(self) -> None:
        created = []
        relay = VirtualCameraRelay(
            VirtualCameraConfig(enabled=False),
            camera_factory=lambda **_kwargs: created.append(True),
        )

        relay.submit(np.zeros((4, 5, 3), dtype=np.uint8))

        self.assertEqual(created, [])
        self.assertEqual(relay.status.state, VirtualCameraState.DISABLED)

    def test_publishes_latest_frame_to_virtual_camera(self) -> None:
        relay = VirtualCameraRelay(
            VirtualCameraConfig(enabled=True, width=2, height=3, fps=25.0),
            camera_factory=FakeVirtualCamera,
        )

        relay.submit(np.full((4, 5, 3), 120, dtype=np.uint8))

        self.assertTrue(
            wait_until(
                lambda: FakeVirtualCamera.instances
                and FakeVirtualCamera.instances[0].frames
            )
        )
        instance = FakeVirtualCamera.instances[0]
        self.assertEqual(instance.kwargs["width"], 2)
        self.assertEqual(instance.kwargs["height"], 3)
        self.assertEqual(instance.kwargs["fps"], 25.0)
        self.assertEqual(instance.frames[-1].shape, (3, 2, 3))
        self.assertEqual(relay.status.state, VirtualCameraState.OPEN)

        relay.stop()

        self.assertTrue(instance.closed)
        self.assertEqual(relay.status.state, VirtualCameraState.STOPPED)

    def test_backend_failure_is_reported_without_raising(self) -> None:
        def failing_factory(**_kwargs):
            raise RuntimeError("driver missing")

        relay = VirtualCameraRelay(
            VirtualCameraConfig(enabled=True, retry_interval_seconds=10.0),
            camera_factory=failing_factory,
        )

        relay.submit(np.zeros((4, 5, 3), dtype=np.uint8))

        self.assertTrue(
            wait_until(lambda: relay.status.state == VirtualCameraState.UNAVAILABLE)
        )
        self.assertIn("driver missing", relay.status.detail)
        relay.close()


if __name__ == "__main__":
    unittest.main()
