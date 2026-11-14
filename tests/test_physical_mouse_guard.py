import unittest

from hand_gesture_controller.physical_mouse_guard import should_block_event


class ShouldBlockEventTests(unittest.TestCase):
    def test_blocks_the_physical_mouse_elsewhere(self) -> None:
        self.assertTrue(
            should_block_event(
                should_block=True, is_injected=False, is_own_window=False
            )
        )

    def test_lets_through_the_events_the_app_generates(self) -> None:
        """Altrimenti l'air mouse bloccherebbe se stesso."""
        self.assertFalse(
            should_block_event(should_block=True, is_injected=True, is_own_window=False)
        )

    def test_lets_through_the_events_on_the_app_windows(self) -> None:
        """Serve per poter spostare o chiudere la finestra del tracker."""
        self.assertFalse(
            should_block_event(should_block=True, is_injected=False, is_own_window=True)
        )

    def test_blocks_nothing_when_the_guard_is_off(self) -> None:
        for injected in (True, False):
            for own in (True, False):
                self.assertFalse(
                    should_block_event(
                        should_block=False, is_injected=injected, is_own_window=own
                    )
                )


if __name__ == "__main__":
    unittest.main()
