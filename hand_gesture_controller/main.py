from __future__ import annotations

import argparse
import time

import cv2
import numpy as np

from .action_profile import ActionProfile
from .action_runner import ActionRunner, RuntimeControls
from .binding_engine import BindingEngine, HandObservation
from .camera_manager import CameraManager, CameraState, CameraStatus
from .config import (
    DEFAULT_CONFIG,
    AppConfig,
    CameraConfig,
    MediaGestureConfig,
    PointerConfig,
    RuntimeConfig,
    TrackerConfig,
    VirtualCameraConfig,
)
from .desktop_overlay import DesktopOverlay, OverlayStatus
from .gesture_detector import Gesture, GestureDetector, GestureFrame, combine_gestures
from .hand_tracker import HandTracker
from .keyboard_controller import KeyboardController
from .media_control import HybridMediaController
from .media_gestures import MediaGestureController, MediaGestureUpdate
from .models import HandResult
from .settings_store import DEFAULT_SETTINGS_PATH, SettingsStore
from .mouse_controller import MouseController, ScreenRect
from .physical_mouse_guard import PhysicalMouseGuard
from .pointer_stabilizer import PointerStabilizer
from .pose_templates import PoseTemplateStore
from .right_hand_mouse import (
    MouseGestureUpdate,
    RightHandMouseController,
    pointer_anchor,
)
from .screen_context import ScreenContextDetector
from .smoothing import ExponentialSmoother
from .state_machine import GestureStateMachine, StateUpdate
from .virtual_camera import VirtualCameraRelay, VirtualCameraStatus


def build_parser(base: AppConfig = DEFAULT_CONFIG) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Control the desktop mouse and clipboard with hand gestures."
    )
    parser.add_argument(
        "--settings",
        default=None,
        help=(
            "Path of the JSON settings file."
            f" Default: {DEFAULT_SETTINGS_PATH}."
        ),
    )
    parser.add_argument("--camera-index", type=int, default=base.camera.index)
    parser.add_argument("--width", type=int, default=base.camera.width)
    parser.add_argument("--height", type=int, default=base.camera.height)
    parser.add_argument("--dry-run", action="store_true", help="Recognize gestures only.")
    parser.add_argument(
        "--paused",
        action="store_true",
        help="Start with system control paused; press SPACE to resume.",
    )
    parser.add_argument(
        "--no-debug",
        action="store_true",
        help="Hide the camera debug window. Use Ctrl+C to stop in this mode.",
    )
    parser.add_argument(
        "--no-mirror",
        action="store_true",
        help="Disable mirrored webcam view.",
    )
    parser.add_argument(
        "--camera-retry-interval",
        type=float,
        default=base.camera.retry_interval_seconds,
        help="Seconds between automatic webcam reopen attempts.",
    )
    parser.add_argument(
        "--keep-camera-on-pause",
        action="store_true",
        help="Do not release the webcam while paused.",
    )
    parser.add_argument(
        "--camera-backend",
        type=int,
        default=base.camera.backend,
        help="Optional OpenCV backend id, for example cv2.CAP_DSHOW.",
    )
    parser.add_argument(
        "--no-camera-fallback",
        action="store_true",
        help="Only try --camera-index instead of probing fallback indices.",
    )
    parser.add_argument(
        "--camera-fallback-indices",
        default=",".join(str(index) for index in base.camera.fallback_indices),
        help="Comma-separated camera indices to try if --camera-index is unusable.",
    )
    parser.add_argument(
        "--virtual-camera",
        dest="virtual_camera",
        action="store_true",
        default=base.virtual_camera.enabled,
        help="Publish the physical webcam feed to a virtual camera device.",
    )
    parser.add_argument(
        "--no-virtual-camera",
        dest="virtual_camera",
        action="store_false",
        help="Disable virtual camera publishing.",
    )
    parser.add_argument(
        "--virtual-camera-mirror",
        action="store_true",
        default=base.virtual_camera.mirror,
        help="Mirror the virtual camera output. By default only the debug view is mirrored.",
    )
    parser.add_argument(
        "--virtual-camera-width",
        type=int,
        default=base.virtual_camera.width,
        help="Virtual camera output width. Defaults to the physical frame width.",
    )
    parser.add_argument(
        "--virtual-camera-height",
        type=int,
        default=base.virtual_camera.height,
        help="Virtual camera output height. Defaults to the physical frame height.",
    )
    parser.add_argument(
        "--virtual-camera-fps",
        type=float,
        default=base.virtual_camera.fps,
        help="Virtual camera target frame rate.",
    )
    parser.add_argument(
        "--virtual-camera-device",
        default=base.virtual_camera.device,
        help="Optional virtual camera device name, for example OBS Virtual Camera.",
    )
    parser.add_argument(
        "--virtual-camera-backend",
        default=base.virtual_camera.backend,
        help="Optional pyvirtualcam backend, for example obs or unitycapture.",
    )
    parser.add_argument(
        "--virtual-camera-retry-interval",
        type=float,
        default=base.virtual_camera.retry_interval_seconds,
        help="Seconds between automatic virtual camera reopen attempts.",
    )
    parser.add_argument(
        "--virtual-camera-print-fps",
        action="store_true",
        help="Print virtual camera output FPS.",
    )
    parser.add_argument(
        "--model-path",
        default=base.tracker.model_path,
        help="Path to hand_landmarker.task for MediaPipe Tasks builds.",
    )
    parser.add_argument(
        "--max-hands",
        type=int,
        default=base.tracker.max_num_hands,
        choices=(1, 2),
        help="Number of hands to track.",
    )
    parser.add_argument(
        "--detection-confidence",
        type=float,
        default=base.tracker.min_detection_confidence,
        help="Minimum hand detection confidence.",
    )
    parser.add_argument(
        "--tracking-confidence",
        type=float,
        default=base.tracker.min_tracking_confidence,
        help="Minimum hand tracking confidence.",
    )
    parser.add_argument(
        "--lost-hand-grace",
        type=float,
        default=base.tracker.lost_hand_grace_seconds,
        help="Seconds to keep a recently lost second hand visible/actionable.",
    )
    parser.add_argument(
        "--mouse-off",
        action="store_true",
        help="Start with right-hand mouse mode disabled.",
    )
    parser.add_argument(
        "--no-pointer-lock",
        action="store_true",
        help="Do not block physical mouse input while air mouse mode is on.",
    )
    parser.add_argument(
        "--action-profile",
        default=None,
        help="Path to the JSON gesture action profile.",
    )
    parser.add_argument(
        "--gesture-profile",
        default=None,
        help="Path to the JSON custom static gesture profile.",
    )
    parser.add_argument(
        "--screen",
        default="all",
        help="Pointer target: all, primary, or monitor number such as 1/2.",
    )
    parser.add_argument(
        "--screen-rect",
        default=None,
        help="Manual pointer target rect: left,top,width,height.",
    )
    parser.add_argument(
        "--pointer-sensitivity",
        type=float,
        default=base.pointer.sensitivity,
        help="Pointer gain around the active-zone center. 1.0 is neutral.",
    )
    parser.add_argument(
        "--smoothing-alpha",
        type=float,
        default=base.pointer.smoothing_alpha,
        help="Pointer smoothing alpha. Higher follows faster, lower is smoother.",
    )
    parser.add_argument(
        "--dead-zone",
        type=float,
        default=base.pointer.dead_zone_px,
        help="Ignore pointer movements smaller than this many pixels.",
    )
    parser.add_argument(
        "--active-zone",
        default=None,
        help="Camera active zone: left,top,right,bottom normalized 0..1.",
    )
    parser.add_argument(
        "--no-media-gestures",
        action="store_true",
        help="Disable video-player fist gestures.",
    )
    parser.add_argument(
        "--no-native-media",
        action="store_true",
        help=(
            "Disable the Windows media session: use only keyboard shortcuts,"
            " which require the player window to be focused."
        ),
    )
    parser.add_argument(
        "--media-swipe-threshold",
        type=float,
        default=base.media_gesture.swipe_threshold,
        help="Normalized fist movement needed to seek video left/right.",
    )
    parser.add_argument(
        "--media-pause-hold",
        type=float,
        default=base.media_gesture.pause_hold_seconds,
        help="Seconds to hold a still fist to toggle video play/pause.",
    )
    parser.add_argument(
        "--media-seek-repeat",
        type=float,
        default=base.media_gesture.seek_repeat_seconds,
        help="Seconds between repeated video seek commands while holding a right fist.",
    )
    parser.add_argument(
        "--media-window-check-interval",
        type=float,
        default=base.media_gesture.window_check_interval_seconds,
        help="Seconds between active-window media detection checks.",
    )
    parser.add_argument(
        "--overlay",
        action="store_true",
        help="Enable the transparent desktop status overlay.",
    )
    return parser


def config_from_args(
    args: argparse.Namespace,
    base: AppConfig = DEFAULT_CONFIG,
) -> AppConfig:
    return AppConfig(
        camera=CameraConfig(
            index=args.camera_index,
            width=args.width,
            height=args.height,
            mirror=not args.no_mirror,
            retry_interval_seconds=args.camera_retry_interval,
            release_on_pause=not args.keep_camera_on_pause,
            backend=args.camera_backend,
            auto_fallback=not args.no_camera_fallback,
            fallback_indices=_parse_int_list(args.camera_fallback_indices),
            probe_frame_attempts=base.camera.probe_frame_attempts,
        ),
        virtual_camera=VirtualCameraConfig(
            enabled=args.virtual_camera,
            mirror=args.virtual_camera_mirror,
            width=args.virtual_camera_width,
            height=args.virtual_camera_height,
            fps=args.virtual_camera_fps,
            device=args.virtual_camera_device,
            backend=args.virtual_camera_backend,
            retry_interval_seconds=args.virtual_camera_retry_interval,
            print_fps=args.virtual_camera_print_fps,
        ),
        tracker=TrackerConfig(
            max_num_hands=args.max_hands,
            min_detection_confidence=args.detection_confidence,
            min_tracking_confidence=args.tracking_confidence,
            model_path=args.model_path,
            flip_handedness=not args.no_mirror,
            lost_hand_grace_seconds=args.lost_hand_grace,
            hand_match_max_distance=base.tracker.hand_match_max_distance,
        ),
        pointer=_pointer_config_from_args(args, base.pointer),
        gesture=base.gesture,
        media_gesture=MediaGestureConfig(
            enabled=not args.no_media_gestures,
            hand=base.media_gesture.hand,
            use_native_media_controls=(
                base.media_gesture.use_native_media_controls
                and not args.no_native_media
            ),
            prefer_native_media_context=(
                base.media_gesture.prefer_native_media_context
                and not args.no_native_media
            ),
            native_seek_seconds=base.media_gesture.native_seek_seconds,
            window_check_interval_seconds=args.media_window_check_interval,
            swipe_threshold=args.media_swipe_threshold,
            swipe_max_seconds=base.media_gesture.swipe_max_seconds,
            seek_repeat_seconds=args.media_seek_repeat,
            pause_hold_seconds=args.media_pause_hold,
            still_threshold=base.media_gesture.still_threshold,
            action_cooldown_seconds=base.media_gesture.action_cooldown_seconds,
            lost_fist_grace_seconds=base.media_gesture.lost_fist_grace_seconds,
            play_pause_key=base.media_gesture.play_pause_key,
            seek_forward_key=base.media_gesture.seek_forward_key,
            seek_backward_key=base.media_gesture.seek_backward_key,
            browser_processes=base.media_gesture.browser_processes,
            player_processes=base.media_gesture.player_processes,
            browser_title_keywords=base.media_gesture.browser_title_keywords,
        ),
        runtime=RuntimeConfig(
            debug_window_name=base.runtime.debug_window_name,
            debug_enabled=not args.no_debug,
            paused_at_start=args.paused,
            dry_run=args.dry_run,
        ),
    )


def run(
    config: AppConfig,
    *,
    action_profile_path: str | None = None,
    gesture_profile_path: str | None = None,
    mouse_enabled: bool = True,
    pointer_lock_enabled: bool = True,
    screen_target: str = "all",
    screen_rect: ScreenRect | None = None,
    overlay_enabled: bool = False,
) -> None:
    camera = CameraManager(config.camera)
    virtual_camera = VirtualCameraRelay(config.virtual_camera)
    tracker = HandTracker(config.tracker)
    detector = GestureDetector(config.gesture)
    mouse = MouseController(
        dry_run=config.runtime.dry_run,
        screen_target=screen_target,
        screen_rect=screen_rect,
    )
    keyboard = KeyboardController(dry_run=config.runtime.dry_run)
    media_context_detector = ScreenContextDetector(config.media_gesture)
    media_output = HybridMediaController(config.media_gesture, keyboard)
    media_controller = MediaGestureController(config.media_gesture, media_output)
    action_profile = ActionProfile.load(action_profile_path)
    binding_engine = BindingEngine(action_profile)
    pose_templates = PoseTemplateStore(gesture_profile_path)
    controls = RuntimeControls(
        mouse_enabled=mouse_enabled,
        pointer_lock_enabled=pointer_lock_enabled and not config.runtime.dry_run,
    )
    action_runner = ActionRunner(
        keyboard=keyboard,
        controls=controls,
        dry_run=config.runtime.dry_run,
    )
    right_mouse = RightHandMouseController(config.gesture)
    pointer_stabilizer = PointerStabilizer(config.gesture.click_freeze_seconds)
    smoother = ExponentialSmoother(
        alpha=config.pointer.smoothing_alpha,
        dead_zone_px=config.pointer.dead_zone_px,
    )
    state_machine = GestureStateMachine(
        config.gesture,
        paused=config.runtime.paused_at_start,
        commands_enabled=False,
    )
    camera.set_paused(state_machine.paused)
    mouse_guard = PhysicalMouseGuard(
        lambda: controls.pointer_lock_enabled
        and controls.mouse_enabled
        and not state_machine.paused,
        enabled=controls.pointer_lock_enabled,
    )
    mouse_guard.start()
    overlay = DesktopOverlay(enabled=overlay_enabled)
    overlay.start()

    last_action = "dry run" if config.runtime.dry_run else None
    mouse_update = MouseGestureUpdate("idle")
    media_update = MediaGestureUpdate(active=False)
    pointer_is_holding = False

    try:
        while True:
            now = time.monotonic()
            frame = camera.read(now)
            camera_status = camera.status
            if frame is not None:
                virtual_camera.submit(_virtual_camera_frame(frame, config))
            else:
                virtual_camera.stop()
            virtual_camera_status = virtual_camera.status
            hands = tracker.process_many(frame) if frame is not None else []
            hand_gestures = _detect_gestures(detector, hands)
            observations = _build_observations(hand_gestures, pose_templates)
            gesture_frames = [
                observation.gesture_frame for observation in observations
            ]
            effective_gesture = combine_gestures(gesture_frames)
            right_observation = _find_hand_observation(observations, "Right")
            media_context = media_context_detector.update(now)
            native_context = media_output.native_context(now)
            if native_context.is_media:
                media_context = native_context
            media_update = media_controller.update(observations, media_context, now)
            if media_update.action:
                last_action = f"media: {media_update.action}"

            if not state_machine.paused and not media_update.consumed:
                event = binding_engine.update(observations, effective_gesture, now)
                if event:
                    action_label = action_runner.run(event.action)
                    last_action = f"{event.name}: {action_label}"
                    if event.action.get("type") in {
                        "toggle_mouse",
                        "mouse_off",
                        "mouse_on",
                    }:
                        state_machine.cancel_pointer_interaction(mouse)
                        right_mouse.cancel(mouse)
                        pointer_stabilizer.reset()
                        smoother.reset()
            elif media_update.consumed:
                binding_engine.update([], Gesture.NONE, now)

            previous_mouse_update = mouse_update
            mouse_update = MouseGestureUpdate("idle")
            pointer_is_holding = False
            if (
                controls.mouse_enabled
                and right_observation
                and not state_machine.paused
                and not media_update.consumed
            ):
                screen_point = mouse.landmark_to_screen(
                    pointer_anchor(right_observation), config.pointer
                )
                button_active = _right_mouse_button_active(right_observation)
                stabilized = pointer_stabilizer.update(
                    screen_point,
                    button_active=button_active,
                    dragging=previous_mouse_update.state == "left_dragging",
                    now=now,
                )
                pointer_is_holding = stabilized.is_holding
                x, y = smoother.update((stabilized.point.x, stabilized.point.y))
                mouse.move_to(x, y)
                mouse_update = right_mouse.update(right_observation, now, mouse)
                if mouse_update.action:
                    last_action = mouse_update.action
            elif (
                media_update.consumed
                or not right_observation
                or not controls.mouse_enabled
            ):
                smoother.reset()
                pointer_stabilizer.reset()
                action = right_mouse.cancel(mouse)
                if action:
                    last_action = action
                if not controls.mouse_enabled:
                    state_machine.cancel_pointer_interaction(mouse)

            update = state_machine.update(Gesture.NONE, now, mouse, keyboard)

            if config.runtime.debug_enabled:
                debug_frame = (
                    frame
                    if frame is not None
                    else _camera_status_frame(config, camera_status)
                )
                if frame is not None:
                    tracker.draw_many(debug_frame, hands)
                _draw_debug(
                    frame=debug_frame,
                    observations=observations,
                    effective_gesture=effective_gesture,
                    update=update,
                    paused=state_machine.paused,
                    dry_run=config.runtime.dry_run,
                    last_action=last_action,
                    controls=controls,
                    mouse_update=mouse_update,
                    screen_rect=mouse.screen_rect,
                    pointer_is_holding=pointer_is_holding,
                    camera_status=camera_status,
                    virtual_camera_status=virtual_camera_status,
                    media_update=media_update,
                    config=config,
                )
                cv2.imshow(config.runtime.debug_window_name, debug_frame)

                key = cv2.waitKey(1) & 0xFF
                if key == 27:
                    break
                if key == 32:
                    if (
                        not state_machine.paused
                        and camera_status.state
                        in {CameraState.UNAVAILABLE, CameraState.RETRY_WAIT}
                    ):
                        camera.retry_now()
                        last_action = "camera retry"
                    else:
                        paused = state_machine.toggle_pause(mouse)
                        camera.set_paused(paused)
                        right_mouse.cancel(mouse)
                        pointer_stabilizer.reset()
                        last_action = (
                            "paused - webcam released" if paused else "resumed"
                        )
                if key in {ord("r"), ord("1"), ord("2"), ord("3")}:
                    message = _handle_record_key(
                        key=key,
                        observations=observations,
                        pose_templates=pose_templates,
                        action_profile=action_profile,
                    )
                    if message:
                        binding_engine = BindingEngine(action_profile)
                        last_action = message
            else:
                time.sleep(0.001)

            overlay.update(
                _overlay_status(
                    observations=observations,
                    controls=controls,
                    paused=state_machine.paused,
                    mouse_update=mouse_update,
                    screen_rect=mouse.screen_rect,
                    last_action=last_action,
                    pointer_is_holding=pointer_is_holding,
                    camera_status=camera_status,
                )
            )
    finally:
        state_machine.cancel_pointer_interaction(mouse)
        right_mouse.cancel(mouse)
        pointer_stabilizer.reset()
        overlay.stop()
        mouse_guard.stop()
        tracker.close()
        camera.close()
        virtual_camera.close()
        cv2.destroyAllWindows()


def _detect_gestures(
    detector: GestureDetector, hands: list[HandResult]
) -> list[tuple[HandResult, GestureFrame]]:
    return [(hand, detector.detect(hand.landmarks)) for hand in hands]


def _pointer_config_from_args(
    args: argparse.Namespace, base: PointerConfig
) -> PointerConfig:
    left = base.active_zone_left
    top = base.active_zone_top
    right = base.active_zone_right
    bottom = base.active_zone_bottom

    if args.active_zone:
        parts = [float(part.strip()) for part in args.active_zone.split(",")]
        if len(parts) != 4:
            raise ValueError("--active-zone must be left,top,right,bottom")
        left, top, right, bottom = parts

    return PointerConfig(
        active_zone_left=left,
        active_zone_top=top,
        active_zone_right=right,
        active_zone_bottom=bottom,
        sensitivity=args.pointer_sensitivity,
        smoothing_alpha=args.smoothing_alpha,
        dead_zone_px=args.dead_zone,
    )


def _parse_int_list(value: str) -> tuple[int, ...]:
    if not value.strip():
        return ()
    return tuple(int(part.strip()) for part in value.split(",") if part.strip())


def _virtual_camera_frame(frame, config: AppConfig):
    if config.camera.mirror == config.virtual_camera.mirror:
        return frame
    return cv2.flip(frame, 1)


def _build_observations(
    hand_gestures: list[tuple[HandResult, GestureFrame]],
    pose_templates: PoseTemplateStore,
) -> list[HandObservation]:
    return [
        HandObservation(
            hand=hand,
            gesture_frame=gesture_frame,
            custom_gestures=pose_templates.match(hand),
        )
        for hand, gesture_frame in hand_gestures
    ]


def _find_hand_observation(
    observations: list[HandObservation], handedness: str
) -> HandObservation | None:
    for observation in observations:
        if observation.hand.handedness == handedness:
            return observation
    return None


def _right_mouse_button_active(observation: HandObservation) -> bool:
    extended = observation.gesture_frame.extended_fingers
    return not extended.get("middle", False) or not extended.get("ring", False)


def _handle_record_key(
    *,
    key: int,
    observations: list[HandObservation],
    pose_templates: PoseTemplateStore,
    action_profile: ActionProfile,
) -> str | None:
    observation = _select_recording_observation(observations)
    if observation is None:
        return "record failed: no hand"

    if key == ord("r"):
        template = pose_templates.record(observation.hand)
        return f"recorded {template.name}"

    if key == ord("1"):
        template = pose_templates.record(observation.hand, name="custom_copy")
        action_profile.upsert_binding(
            name="custom_copy",
            gesture=template.name,
            hands=[template.handedness],
            hold_seconds=0.45,
            cooldown_seconds=1.00,
            priority=90,
            action={"type": "hotkey", "keys": ["ctrl", "c"]},
        )
        action_profile.save()
        return "recorded custom_copy"

    if key == ord("2"):
        template = pose_templates.record(observation.hand, name="custom_paste")
        action_profile.upsert_binding(
            name="custom_paste",
            gesture=template.name,
            hands=[template.handedness],
            hold_seconds=0.45,
            cooldown_seconds=1.00,
            priority=90,
            action={"type": "hotkey", "keys": ["ctrl", "v"]},
        )
        action_profile.save()
        return "recorded custom_paste"

    if key == ord("3"):
        template = pose_templates.record(observation.hand, name="custom_toggle_mouse")
        action_profile.upsert_binding(
            name="custom_toggle_mouse",
            gesture=template.name,
            hands=[template.handedness],
            hold_seconds=0.65,
            cooldown_seconds=1.00,
            priority=95,
            action={"type": "toggle_mouse"},
        )
        action_profile.save()
        return "recorded custom_toggle_mouse"

    return None


def _select_recording_observation(
    observations: list[HandObservation],
) -> HandObservation | None:
    tracked = [observation for observation in observations if observation.hand.is_tracked]
    candidates = tracked or observations
    for observation in candidates:
        if observation.hand.handedness == "Left":
            return observation
    return candidates[0] if candidates else None


def _draw_debug(
    frame,
    observations: list[HandObservation],
    effective_gesture: Gesture,
    update: StateUpdate,
    paused: bool,
    dry_run: bool,
    last_action: str | None,
    controls: RuntimeControls,
    mouse_update: MouseGestureUpdate,
    screen_rect: ScreenRect,
    pointer_is_holding: bool,
    camera_status: CameraStatus,
    virtual_camera_status: VirtualCameraStatus,
    media_update: MediaGestureUpdate,
    config: AppConfig,
) -> None:
    height, width = frame.shape[:2]
    left = int(config.pointer.active_zone_left * width)
    top = int(config.pointer.active_zone_top * height)
    right = int(config.pointer.active_zone_right * width)
    bottom = int(config.pointer.active_zone_bottom * height)

    cv2.rectangle(frame, (left, top), (right, bottom), (80, 200, 120), 2)

    lines = [
        f"camera: {camera_status.state.value} - {camera_status.message}",
        (
            f"virtual cam: {virtual_camera_status.state.value}"
            f" - {virtual_camera_status.message}"
        ),
        (
            f"media: {'on' if media_update.active else 'off'}"
            f" - {media_update.status} - {media_update.context_label}"
        ),
        f"gesture: {effective_gesture.value}",
        f"state: {update.state.value}",
        f"hands: {len(observations)}",
        f"action: {last_action or '-'}",
        f"mouse state: {mouse_update.state}",
        "cursor hold: on" if pointer_is_holding else "cursor hold: off",
        "mouse: on" if controls.mouse_enabled else "mouse: off",
        "pointer lock: on"
        if controls.pointer_lock_enabled and not dry_run
        else "pointer lock: off",
        f"screen: {screen_rect.left},{screen_rect.top} "
        f"{screen_rect.width}x{screen_rect.height}",
        f"sens: {config.pointer.sensitivity:.2f} "
        f"smooth: {config.pointer.smoothing_alpha:.2f}",
        "mode: paused" if paused else "mode: dry-run" if dry_run else "mode: active",
        "MID down click/drag/double | RING down right | SPACE pause",
    ]
    if camera_status.detail:
        lines.insert(1, camera_status.detail)
    if camera_status.retry_in_seconds > 0:
        lines.insert(2, f"retry in: {camera_status.retry_in_seconds:.1f}s")
    if virtual_camera_status.detail:
        lines.insert(3, virtual_camera_status.detail)

    if observations:
        hand_lines = [
            f"{index + 1}:{_hand_label(observation.hand)}:"
            f"{observation.gesture_frame.gesture.value}:"
            f"{observation.gesture_frame.pinch_distance:.2f}"
            f"{_custom_label(observation)}"
            for index, observation in enumerate(observations)
        ]
        lines.insert(3, " | ".join(hand_lines))

    y = 28
    for line in lines:
        cv2.putText(
            frame,
            line,
            (16, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (0, 0, 0),
            4,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            line,
            (16, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        y += 26

    for index, observation in enumerate(observations, start=1):
        wrist = observation.hand.landmarks[0]
        label = (
            f"{index} {_hand_label(observation.hand)} "
            f"{observation.gesture_frame.gesture.value}"
            f"{_custom_label(observation)}"
        )
        cv2.putText(
            frame,
            label,
            (int(wrist.x * width), int(wrist.y * height)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 0, 0),
            3,
            cv2.LINE_AA,
        )
        cv2.putText(
            frame,
            label,
            (int(wrist.x * width), int(wrist.y * height)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (80, 240, 255),
            1,
            cv2.LINE_AA,
        )


def _hand_label(hand: HandResult) -> str:
    suffix = "" if hand.is_tracked else " hold"
    return f"{hand.handedness}{suffix}"


def _custom_label(observation: HandObservation) -> str:
    if not observation.custom_gestures:
        return ""
    return " [" + ",".join(observation.custom_gestures[:2]) + "]"


def _camera_status_frame(
    config: AppConfig, camera_status: CameraStatus
):
    frame = np.full(
        (max(config.camera.height, 480), max(config.camera.width, 640), 3),
        34,
        dtype=np.uint8,
    )
    lines = [
        "Camera unavailable",
        camera_status.message,
        camera_status.detail,
        "Press SPACE to retry/resume",
        "Press ESC to exit",
    ]
    if camera_status.state == CameraState.PAUSED:
        lines[0] = "PAUSED - webcam released"
    if camera_status.retry_in_seconds > 0:
        lines.insert(3, f"Automatic retry in {camera_status.retry_in_seconds:.1f}s")

    y = 90
    for line in [line for line in lines if line]:
        cv2.putText(
            frame,
            line,
            (40, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (230, 230, 230),
            2,
            cv2.LINE_AA,
        )
        y += 42
    return frame


def _overlay_status(
    *,
    observations: list[HandObservation],
    controls: RuntimeControls,
    paused: bool,
    mouse_update: MouseGestureUpdate,
    screen_rect: ScreenRect,
    last_action: str | None,
    pointer_is_holding: bool,
    camera_status: CameraStatus,
) -> OverlayStatus:
    right = _find_hand_observation(observations, "Right")
    left = _find_hand_observation(observations, "Left")
    return OverlayStatus(
        camera=camera_status.state.value,
        mouse_enabled=controls.mouse_enabled,
        pointer_lock_enabled=controls.pointer_lock_enabled,
        paused=paused,
        hands_count=len(observations),
        right_hand=_observation_label(right),
        left_hand=_observation_label(left),
        mouse_state=mouse_update.state,
        last_action=last_action or "-",
        screen=f"{screen_rect.left},{screen_rect.top} {screen_rect.width}x{screen_rect.height}",
        pointer_hold=pointer_is_holding,
    )


def _observation_label(observation: HandObservation | None) -> str:
    if observation is None:
        return "-"
    custom = _custom_label(observation)
    return f"{observation.gesture_frame.gesture.value}{custom}"


def _settings_path_from_argv() -> str | None:
    """Legge solo --settings, perche' il file decide i default del parser."""
    pre = argparse.ArgumentParser(add_help=False)
    pre.add_argument("--settings", default=None)
    return pre.parse_known_args()[0].settings


def main() -> None:
    base = SettingsStore(_settings_path_from_argv()).load()
    args = build_parser(base).parse_args()
    config = config_from_args(args, base)
    screen_rect = ScreenRect.parse(args.screen_rect) if args.screen_rect else None
    run(
        config,
        action_profile_path=args.action_profile,
        gesture_profile_path=args.gesture_profile,
        mouse_enabled=not args.mouse_off,
        pointer_lock_enabled=not args.no_pointer_lock,
        screen_target=args.screen,
        screen_rect=screen_rect,
        overlay_enabled=args.overlay,
    )


if __name__ == "__main__":
    main()
