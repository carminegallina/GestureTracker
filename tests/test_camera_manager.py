import unittest

from hand_gesture_controller.camera_manager import CameraManager, CameraState
from hand_gesture_controller.config import CameraConfig


class FakeCapture:
    released_count = 0

    def __init__(self, opened: bool = True, frame=None) -> None:
        self.opened = opened
        self.frame = frame
        self.released = False

    def set(self, *_args) -> None:
        return None

    def isOpened(self) -> bool:
        return self.opened

    def read(self):
        if self.frame is None:
            return False, None
        return True, self.frame

    def release(self) -> None:
        self.released = True
        FakeCapture.released_count += 1


class CameraManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        FakeCapture.released_count = 0

    def test_busy_camera_does_not_raise_and_schedules_retry(self) -> None:
        manager = CameraManager(
            CameraConfig(retry_interval_seconds=2.0, auto_fallback=False),
            capture_factory=lambda *_args: FakeCapture(opened=False),
        )

        frame = manager.read(now=10.0)

        self.assertIsNone(frame)
        self.assertEqual(manager.status.state, CameraState.UNAVAILABLE)
        self.assertEqual(FakeCapture.released_count, 1)

        retry_frame = manager.read(now=11.0)

        self.assertIsNone(retry_frame)
        self.assertEqual(manager.status.state, CameraState.RETRY_WAIT)
        self.assertGreater(manager.status.retry_in_seconds, 0)

    def test_pause_releases_camera(self) -> None:
        manager = CameraManager(
            CameraConfig(mirror=False, release_on_pause=True),
            capture_factory=lambda *_args: FakeCapture(opened=True, frame=object()),
        )

        manager.read(now=1.0)
        manager.set_paused(True)

        self.assertEqual(manager.status.state, CameraState.PAUSED)
        self.assertEqual(FakeCapture.released_count, 1)

    def test_resume_retries_immediately_after_pause(self) -> None:
        calls = []

        def factory(*_args):
            calls.append(True)
            return FakeCapture(opened=True, frame=object())

        manager = CameraManager(CameraConfig(mirror=False, release_on_pause=True), factory)

        manager.set_paused(True)
        self.assertIsNone(manager.read(now=1.0))
        manager.set_paused(False)
        frame = manager.read(now=1.1)

        self.assertIsNotNone(frame)
        self.assertEqual(len(calls), 1)

    def test_fallback_uses_next_camera_with_valid_frames(self) -> None:
        calls = []
        expected_frame = object()

        def factory(index, *_args):
            calls.append(index)
            if index == 0:
                return FakeCapture(opened=True, frame=None)
            if index == 1:
                return FakeCapture(opened=True, frame=expected_frame)
            return FakeCapture(opened=False)

        manager = CameraManager(
            CameraConfig(
                mirror=False,
                index=0,
                auto_fallback=True,
                fallback_indices=(0, 1, 2),
                probe_frame_attempts=1,
            ),
            factory,
        )

        frame = manager.read(now=1.0)

        self.assertIs(frame, expected_frame)
        self.assertEqual(calls, [0, 1])
        self.assertIn("Camera 1 active", manager.status.message)


if __name__ == "__main__":
    unittest.main()
