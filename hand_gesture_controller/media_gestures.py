from __future__ import annotations

from dataclasses import dataclass

from .binding_engine import HandObservation
from .config import MediaGestureConfig
from .gesture_detector import Gesture
from .keyboard_controller import KeyboardController
from .models import LandmarkPoint
from .screen_context import ScreenContext


@dataclass(frozen=True)
class MediaGestureUpdate:
    active: bool
    has_fist: bool = False
    consumed: bool = False
    action: str | None = None
    status: str = "idle"
    context_label: str = ""


@dataclass
class _FistSession:
    handedness: str
    start: LandmarkPoint
    started_at: float
    last_seen_at: float
    mode: str | None = None
    last_fired_at: float = -999.0
    pause_fired: bool = False


class MediaGestureController:
    def __init__(
        self,
        config: MediaGestureConfig,
        keyboard: KeyboardController,
    ) -> None:
        self.config = config
        self.keyboard = keyboard
        self._session: _FistSession | None = None
        self._last_action_at = -999.0

    def update(
        self,
        observations: list[HandObservation],
        context: ScreenContext,
        now: float,
    ) -> MediaGestureUpdate:
        if not self.config.enabled or not context.is_media:
            self.reset()
            return MediaGestureUpdate(
                active=False,
                context_label=_context_label(context),
            )

        fist = self._select_fist(observations)
        if fist is None:
            if self._session and now - self._session.last_seen_at > self.config.lost_fist_grace_seconds:
                self.reset()
            return MediaGestureUpdate(
                active=True,
                has_fist=False,
                consumed=False,
                status="media ready",
                context_label=_context_label(context),
            )

        center = _hand_center(fist)
        if self._session is None or self._session.handedness != fist.hand.handedness:
            self._session = _FistSession(
                handedness=fist.hand.handedness,
                start=center,
                started_at=now,
                last_seen_at=now,
            )

        session = self._session
        session.last_seen_at = now

        if session.pause_fired:
            return MediaGestureUpdate(
                active=True,
                has_fist=True,
                consumed=True,
                status="release fist",
                context_label=_context_label(context),
            )

        if session.mode in {"seek forward", "seek backward"}:
            return self._update_seek_repeat(session.mode, context, now)

        if now - self._last_action_at < self.config.action_cooldown_seconds:
            return MediaGestureUpdate(
                active=True,
                has_fist=True,
                consumed=True,
                status="cooldown",
                context_label=_context_label(context),
            )

        dx = center.x - session.start.x
        dy = center.y - session.start.y
        held_for = now - session.started_at

        if self._is_swipe(dx, dy, held_for):
            session.mode = "seek forward" if dx > 0 else "seek backward"
            return self._fire_seek(session.mode, context, now)

        if self._is_pause_hold(dx, dy, held_for):
            return self._fire_pause(context, now)

        return MediaGestureUpdate(
            active=True,
            has_fist=True,
            consumed=True,
            status="fist tracking",
            context_label=_context_label(context),
        )

    def reset(self) -> None:
        self._session = None

    def _select_fist(
        self, observations: list[HandObservation]
    ) -> HandObservation | None:
        fists = [
            observation
            for observation in observations
            if observation.hand.is_tracked
            and observation.gesture_frame.gesture == Gesture.FIST
            and observation.hand.handedness.lower() == self.config.hand.lower()
        ]
        return fists[0] if fists else None

    def _is_swipe(self, dx: float, dy: float, held_for: float) -> bool:
        return (
            abs(dx) >= self.config.swipe_threshold
            and held_for <= self.config.swipe_max_seconds
            and abs(dx) > abs(dy) * 1.35
        )

    def _is_pause_hold(self, dx: float, dy: float, held_for: float) -> bool:
        return (
            held_for >= self.config.pause_hold_seconds
            and abs(dx) <= self.config.still_threshold
            and abs(dy) <= self.config.still_threshold
        )

    def _update_seek_repeat(
        self,
        action: str,
        context: ScreenContext,
        now: float,
    ) -> MediaGestureUpdate:
        session = self._session
        if (
            session is not None
            and now - session.last_fired_at >= self.config.seek_repeat_seconds
        ):
            return self._fire_seek(action, context, now)

        return MediaGestureUpdate(
            active=True,
            has_fist=True,
            consumed=True,
            status=action,
            context_label=_context_label(context),
        )

    def _fire_seek(
        self,
        action: str,
        context: ScreenContext,
        now: float,
    ) -> MediaGestureUpdate:
        key = (
            self.config.seek_forward_key
            if action == "seek forward"
            else self.config.seek_backward_key
        )
        key = _media_key(action, key, context)
        self.keyboard.press(key)
        if self._session:
            self._session.last_fired_at = now
        self._last_action_at = now
        return MediaGestureUpdate(
            active=True,
            has_fist=True,
            consumed=True,
            action=action,
            status=action,
            context_label=_context_label(context),
        )

    def _fire_pause(
        self,
        context: ScreenContext,
        now: float,
    ) -> MediaGestureUpdate:
        action = "play/pause"
        key = _media_key(action, self.config.play_pause_key, context)
        self.keyboard.press(key)
        if self._session:
            self._session.pause_fired = True
            self._session.last_fired_at = now
        self._last_action_at = now
        return MediaGestureUpdate(
            active=True,
            has_fist=True,
            consumed=True,
            action=action,
            status="release fist",
            context_label=_context_label(context),
        )


def _hand_center(observation: HandObservation) -> LandmarkPoint:
    landmarks = observation.hand.landmarks
    if not landmarks:
        return LandmarkPoint(0.0, 0.0)

    x = sum(point.x for point in landmarks) / len(landmarks)
    y = sum(point.y for point in landmarks) / len(landmarks)
    z = sum(point.z for point in landmarks) / len(landmarks)
    return LandmarkPoint(x, y, z)


def _context_label(context: ScreenContext) -> str:
    if not context.process_name and not context.title:
        return "-"
    title = context.title[:42]
    if context.reason:
        return f"{context.process_name}: {context.reason}"
    if title:
        return f"{context.process_name}: {title}"
    return context.process_name


def _media_key(action: str, default_key: str, context: ScreenContext) -> str:
    title = context.title.lower()
    reason = context.reason.lower()
    if "youtube" not in title and "youtube" not in reason:
        return default_key

    youtube_keys = {
        "play/pause": "k",
        "seek backward": "j",
        "seek forward": "l",
    }
    return youtube_keys.get(action, default_key)
