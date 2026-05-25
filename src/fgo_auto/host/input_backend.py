"""Select tap/swipe backend for the current Run (ADB vs window messages)."""

from __future__ import annotations

from typing import Literal

import structlog

from fgo_auto.host.adb_input import AdbError, AdbInput

logger = structlog.get_logger()

InputMethod = Literal["adb", "window_message"]

_method: InputMethod = "adb"
_adb: AdbInput | None = None


def configure_input_backend(
    *,
    method: InputMethod = "adb",
    adb_path: str | None = None,
    adb_device: str | None = None,
    frame_size: tuple[int, int] = (1920, 1080),
) -> InputMethod:
    """Initialize input for a Run. Falls back to window_message if ADB is unavailable."""
    global _method, _adb
    if method == "adb":
        try:
            _adb = AdbInput.create(
                adb_path=adb_path,
                device=adb_device,
                frame_size=frame_size,
            )
            _method = "adb"
            logger.info(
                "input_backend",
                method="adb",
                device=_adb.device,
                adb=str(_adb.adb_path),
                frame_size=_adb.frame_size,
                android_size=_adb.android_size,
            )
            return _method
        except AdbError as exc:
            logger.warning("adb_unavailable", error=str(exc), fallback="window_message")
    _adb = None
    _method = "window_message"
    logger.info("input_backend", method=_method)
    return _method


def active_input_method() -> InputMethod:
    return _method


def adb_client() -> AdbInput | None:
    return _adb


def reset_input_backend() -> None:
    global _method, _adb
    _method = "window_message"
    _adb = None
