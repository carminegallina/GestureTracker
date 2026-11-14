from dataclasses import asdict, dataclass, fields
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class CameraConfig:
    index: int = 0
    width: int = 1280
    height: int = 720
    mirror: bool = True
    retry_interval_seconds: float = 2.0
    release_on_pause: bool = True
    backend: int | None = 700
    auto_fallback: bool = True
    fallback_indices: tuple[int, ...] = (0, 1, 2, 3, 4)
    probe_frame_attempts: int = 3


@dataclass(frozen=True)
class VirtualCameraConfig:
    enabled: bool = True
    mirror: bool = False
    width: int | None = None
    height: int | None = None
    fps: float = 30.0
    device: str | None = None
    backend: str | None = None
    retry_interval_seconds: float = 3.0
    print_fps: bool = False


@dataclass(frozen=True)
class TrackerConfig:
    max_num_hands: int = 2
    min_detection_confidence: float = 0.55
    min_tracking_confidence: float = 0.50
    model_path: str | None = None
    flip_handedness: bool = True
    lost_hand_grace_seconds: float = 0.35
    hand_match_max_distance: float = 0.35


@dataclass(frozen=True)
class PointerConfig:
    active_zone_left: float = 0.18
    active_zone_top: float = 0.24
    active_zone_right: float = 0.82
    active_zone_bottom: float = 0.90
    sensitivity: float = 1.0
    smoothing_alpha: float = 0.16
    dead_zone_px: float = 7.0


@dataclass(frozen=True)
class GestureConfig:
    pinch_threshold: float = 0.35
    finger_extension_margin: float = 0.015
    copy_hold_seconds: float = 0.50
    paste_hold_seconds: float = 0.45
    command_cooldown_seconds: float = 1.00
    drag_hold_seconds: float = 0.18
    click_max_seconds: float = 0.25
    double_click_seconds: float = 0.32
    finger_tap_min_seconds: float = 0.04
    right_click_hold_seconds: float = 0.08
    click_freeze_seconds: float = 0.12


@dataclass(frozen=True)
class MediaGestureConfig:
    enabled: bool = True
    hand: str = "Right"
    use_native_media_controls: bool = True
    # Una sessione media di Windows vale come contesto media anche se il player
    # non e' in primo piano: serve perche' di solito davanti c'e' la finestra
    # del tracker, non il player.
    prefer_native_media_context: bool = True
    native_seek_seconds: float = 10.0
    window_check_interval_seconds: float = 0.35
    swipe_threshold: float = 0.16
    swipe_max_seconds: float = 1.10
    seek_repeat_seconds: float = 0.35
    pause_hold_seconds: float = 0.55
    still_threshold: float = 0.055
    action_cooldown_seconds: float = 0.75
    lost_fist_grace_seconds: float = 0.20
    play_pause_key: str = "space"
    seek_forward_key: str = "right"
    seek_backward_key: str = "left"
    browser_processes: tuple[str, ...] = (
        "chrome.exe",
        "msedge.exe",
        "firefox.exe",
        "brave.exe",
        "opera.exe",
        "vivaldi.exe",
    )
    player_processes: tuple[str, ...] = (
        "vlc.exe",
        "mpv.exe",
        "wmplayer.exe",
        "potplayermini.exe",
        "potplayermini64.exe",
        "movies.exe",
        "video.ui.exe",
        "quicktimeplayer.exe",
    )
    browser_title_keywords: tuple[str, ...] = (
        "youtube",
        "netflix",
        "prime video",
        "disney+",
        "twitch",
        "vimeo",
        "dailymotion",
        "raiplay",
        "mediaset infinity",
        "now tv",
        "plex",
        "player",
        "video",
        "watch",
        "stream",
    )


@dataclass(frozen=True)
class RuntimeConfig:
    debug_window_name: str = "GestureTracker"
    debug_enabled: bool = True
    paused_at_start: bool = False
    dry_run: bool = False


@dataclass(frozen=True)
class AppConfig:
    camera: CameraConfig = CameraConfig()
    virtual_camera: VirtualCameraConfig = VirtualCameraConfig()
    tracker: TrackerConfig = TrackerConfig()
    pointer: PointerConfig = PointerConfig()
    gesture: GestureConfig = GestureConfig()
    media_gesture: MediaGestureConfig = MediaGestureConfig()
    runtime: RuntimeConfig = RuntimeConfig()


DEFAULT_CONFIG = AppConfig()


def merge_dataclass(instance: T, values: dict[str, Any]) -> T:
    """Applica a `instance` solo i campi noti, convertendo le liste in tuple."""
    allowed = {field.name for field in fields(instance)}
    clean = {}
    for key, value in values.items():
        if key not in allowed:
            continue
        current = getattr(instance, key)
        if isinstance(current, tuple) and isinstance(value, list):
            value = tuple(value)
        clean[key] = value
    return type(instance)(**{**asdict(instance), **clean})
