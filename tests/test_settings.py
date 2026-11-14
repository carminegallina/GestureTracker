import json
import tempfile
import unittest
from pathlib import Path

from hand_gesture_controller.config import DEFAULT_CONFIG
from hand_gesture_controller.settings_store import SettingsStore


class SettingsStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.path = Path(self._tmp.name) / "settings.json"
        self.addCleanup(self._tmp.cleanup)

    def write(self, data: object) -> None:
        self.path.write_text(json.dumps(data), encoding="utf-8")

    def test_missing_file_keeps_defaults(self) -> None:
        config = SettingsStore(self.path).load()

        self.assertEqual(config, DEFAULT_CONFIG)
        self.assertFalse(self.path.exists())

    def test_file_overrides_only_the_listed_fields(self) -> None:
        self.write({"media_gesture": {"swipe_threshold": 0.33}, "camera": {"index": 2}})

        config = SettingsStore(self.path).load()

        self.assertEqual(config.media_gesture.swipe_threshold, 0.33)
        self.assertEqual(config.camera.index, 2)
        self.assertEqual(
            config.media_gesture.pause_hold_seconds,
            DEFAULT_CONFIG.media_gesture.pause_hold_seconds,
        )

    def test_lists_become_tuples(self) -> None:
        self.write({"camera": {"fallback_indices": [1, 2]}})

        config = SettingsStore(self.path).load()

        self.assertEqual(config.camera.fallback_indices, (1, 2))

    def test_unknown_fields_are_ignored(self) -> None:
        self.write({"media_gesture": {"non_esiste": 1}, "non_esiste": {"a": 1}})

        self.assertEqual(SettingsStore(self.path).load(), DEFAULT_CONFIG)

    def test_broken_json_falls_back_to_defaults(self) -> None:
        self.path.write_text("{ questo non e' json", encoding="utf-8")

        self.assertEqual(SettingsStore(self.path).load(), DEFAULT_CONFIG)

    def test_saved_file_reloads_unchanged(self) -> None:
        store = SettingsStore(self.path)
        store.save(DEFAULT_CONFIG)

        self.assertEqual(store.load(), DEFAULT_CONFIG)


class DefaultPathTests(unittest.TestCase):
    def test_the_default_path_does_not_depend_on_the_working_directory(self) -> None:
        """Avviata da un'altra cartella, l'app deve trovare lo stesso file."""
        from hand_gesture_controller.settings_store import DEFAULT_SETTINGS_PATH

        self.assertTrue(DEFAULT_SETTINGS_PATH.is_absolute())
        self.assertEqual(DEFAULT_SETTINGS_PATH.name, "settings.json")
        self.assertEqual(DEFAULT_SETTINGS_PATH.parent.name, "hand_gesture_controller")

    def test_the_store_uses_that_path_by_default(self) -> None:
        from hand_gesture_controller.settings_store import DEFAULT_SETTINGS_PATH

        self.assertEqual(SettingsStore().path, DEFAULT_SETTINGS_PATH)


if __name__ == "__main__":
    unittest.main()
