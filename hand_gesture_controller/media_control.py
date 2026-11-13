from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Protocol

from .config import MediaGestureConfig
from .keyboard_controller import KeyboardController
from .screen_context import ScreenContext

TICKS_PER_SECOND = 10_000_000


@dataclass(frozen=True)
class NativeMediaInfo:
    available: bool
    title: str = ""
    artist: str = ""
    app_id: str = ""
    playback_status: str = ""
    detail: str = ""


class NativeMediaController(Protocol):
    def get_info(self, now: float | None = None) -> NativeMediaInfo:
        ...

    def toggle_play_pause(self) -> bool:
        ...

    def seek_relative(self, seconds: float) -> bool:
        ...


class WindowsNativeMediaController:
    def __init__(self, enabled: bool = True, info_cache_seconds: float = 0.50) -> None:
        self.enabled = enabled
        self.info_cache_seconds = info_cache_seconds
        self._manager = None
        self._last_info_at = -999.0
        self._last_info = NativeMediaInfo(False, detail="not checked")
        self._last_error = ""

    def get_info(self, now: float | None = None) -> NativeMediaInfo:
        if not self.enabled:
            return NativeMediaInfo(False, detail="native media disabled")
        now = time.monotonic() if now is None else now
        if now - self._last_info_at < self.info_cache_seconds:
            return self._last_info
        self._last_info_at = now
        self._last_info = self._run(self._get_info_async()) or NativeMediaInfo(
            False,
            detail=self._last_error or "native media unavailable",
        )
        return self._last_info

    def toggle_play_pause(self) -> bool:
        if not self.enabled:
            return False
        return bool(self._run(self._toggle_play_pause_async()))

    def seek_relative(self, seconds: float) -> bool:
        if not self.enabled:
            return False
        return bool(self._run(self._seek_relative_async(seconds)))

    async def _get_manager(self):
        if self._manager is not None:
            return self._manager
        try:
            from winrt.windows.media.control import (
                GlobalSystemMediaTransportControlsSessionManager,
            )
        except Exception as exc:
            self._last_error = f"winrt media package unavailable: {exc}"
            return None

        try:
            self._manager = await GlobalSystemMediaTransportControlsSessionManager.request_async()
        except Exception as exc:
            self._last_error = f"request_async failed: {exc}"
            return None
        return self._manager

    async def _get_session(self):
        manager = await self._get_manager()
        if manager is None:
            return None
        try:
            return manager.get_current_session()
        except Exception as exc:
            self._last_error = f"get_current_session failed: {exc}"
            return None

    async def _get_info_async(self) -> NativeMediaInfo:
        session = await self._get_session()
        if session is None:
            return NativeMediaInfo(False, detail="no current media session")

        title = ""
        artist = ""
        try:
            props = await session.try_get_media_properties_async()
            title = str(getattr(props, "title", "") or "")
            artist = str(getattr(props, "artist", "") or "")
        except Exception:
            pass

        playback_status = ""
        try:
            info = session.get_playback_info()
            playback_status = str(getattr(info, "playback_status", "") or "")
        except Exception:
            pass

        return NativeMediaInfo(
            True,
            title=title,
            artist=artist,
            app_id=str(getattr(session, "source_app_user_model_id", "") or ""),
            playback_status=playback_status,
            detail="native media session",
        )

    async def _toggle_play_pause_async(self) -> bool:
        session = await self._get_session()
        if session is None:
            return False
        try:
            return bool(await session.try_toggle_play_pause_async())
        except Exception as exc:
            self._last_error = f"toggle failed: {exc}"
            return False

    async def _seek_relative_async(self, seconds: float) -> bool:
        session = await self._get_session()
        if session is None:
            return False
        try:
            timeline = session.get_timeline_properties()
            position = timeline.position.total_seconds()
            minimum = timeline.min_seek_time.total_seconds()
            maximum = timeline.max_seek_time.total_seconds()
            if maximum <= minimum:
                maximum = timeline.end_time.total_seconds()
            target = min(max(position + seconds, minimum), maximum)
            return bool(await session.try_change_playback_position_async(_seconds_to_ticks(target)))
        except Exception as exc:
            self._last_error = f"seek failed: {exc}"
            return False

    def _run(self, coroutine):
        try:
            return asyncio.run(coroutine)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(coroutine)
            finally:
                loop.close()
        except Exception as exc:
            self._last_error = str(exc)
            return None


class HybridMediaController:
    def __init__(
        self,
        config: MediaGestureConfig,
        keyboard: KeyboardController,
        native: NativeMediaController | None = None,
    ) -> None:
        self.config = config
        self.keyboard = keyboard
        self.native = native or WindowsNativeMediaController(
            enabled=config.use_native_media_controls
        )

    def play_pause(self, context: ScreenContext) -> str:
        if self.config.use_native_media_controls and self.native.toggle_play_pause():
            return "native play/pause"
        self.keyboard.press(_fallback_key("play/pause", self.config.play_pause_key, context))
        return "key play/pause"

    def seek_forward(self, context: ScreenContext) -> str:
        if self.config.use_native_media_controls and self.native.seek_relative(
            self.config.native_seek_seconds
        ):
            return "native seek forward"
        self.keyboard.press(_fallback_key("seek forward", self.config.seek_forward_key, context))
        return "key seek forward"

    def seek_backward(self, context: ScreenContext) -> str:
        if self.config.use_native_media_controls and self.native.seek_relative(
            -self.config.native_seek_seconds
        ):
            return "native seek backward"
        self.keyboard.press(_fallback_key("seek backward", self.config.seek_backward_key, context))
        return "key seek backward"

    def native_context(self, now: float | None = None) -> ScreenContext:
        if not self.config.use_native_media_controls or not self.config.prefer_native_media_context:
            return ScreenContext(False)
        info = self.native.get_info(now)
        if not info.available:
            return ScreenContext(False, reason=info.detail)
        title = info.title or info.artist or "Windows media session"
        process = info.app_id or "windows media"
        return ScreenContext(
            True,
            title=title,
            process_name=process,
            reason="native media session",
        )


def _fallback_key(action: str, default_key: str, context: ScreenContext) -> str:
    text = f"{context.title} {context.reason}".lower()
    if "youtube" not in text:
        return default_key
    return {"play/pause": "k", "seek backward": "j", "seek forward": "l"}.get(
        action,
        default_key,
    )


def _seconds_to_ticks(seconds: float) -> int:
    return int(seconds * TICKS_PER_SECOND)
