from __future__ import annotations

from pathlib import Path
from typing import Protocol

import cv2
import numpy as np
import structlog

from fgo_auto.host.window_binder import WindowInfo
from fgo_auto.vision.frame import Frame

logger = structlog.get_logger()


class CaptureError(Exception):
    """Screen capture failed."""


class HostCapture(Protocol):
    def capture(self) -> Frame: ...

    def save_diagnostic(self, path: Path) -> None: ...


class FixtureHostCapture:
    """Loads a static PNG for tests and offline runs."""

    def __init__(self, image_path: Path, preset: tuple[int, int] = (1920, 1080)) -> None:
        image = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
        if image is None:
            raise CaptureError(f"Could not read fixture image: {image_path}")
        self._frame = Frame(data=image)
        self._preset = preset

    def capture(self) -> Frame:
        return Frame(data=self._frame.data.copy())

    def save_diagnostic(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), self._frame.data)


class WindowHostCapture:
    """
    Captures the emulator game surface via PrintWindow (not desktop mss).

    Avoids capturing FGO-AUTO or other windows stacked above the emulator.
    """

    def __init__(self, window: WindowInfo, preset: tuple[int, int]) -> None:
        self._window = window
        self._preset = preset
        self._last: Frame | None = None
        self._input_hwnd = window.handle
        import sys

        if sys.platform == "win32":
            from fgo_auto.host.win32_capture import resolve_capture_hwnd, resolve_input_hwnd
            from fgo_auto.host.win32_geometry import client_area_screen_bounds

            self._capture_hwnd = resolve_capture_hwnd(window.handle)
            self._input_hwnd = resolve_input_hwnd(window.handle)
            self._region = client_area_screen_bounds(self._capture_hwnd)
        else:
            self._capture_hwnd = window.handle
            self._region = (window.left, window.top, window.width, window.height)

    def _sync_tap_target(self) -> None:
        from fgo_auto.host.tap_target import TapTarget, get_tap_target, set_tap_target

        if get_tap_target() is None:
            return
        left, top, _w, _h = self._region
        set_tap_target(
            TapTarget(
                hwnd=self._input_hwnd,
                origin_left=left,
                origin_top=top,
                client_coords=True,
            )
        )

    @property
    def capture_hwnd(self) -> int:
        return self._capture_hwnd

    @property
    def capture_region(self) -> tuple[int, int, int, int]:
        """(screen_left, screen_top, width, height) for tap coordinate alignment."""
        return self._region

    def capture(self) -> Frame:
        import sys

        if sys.platform != "win32":
            raise CaptureError("Window capture requires Windows")

        image: np.ndarray | None = None
        for hwnd in self._hwnd_candidates():
            from fgo_auto.host.win32_geometry import client_area_screen_bounds

            left, top, width, height = client_area_screen_bounds(hwnd)
            candidate = self._capture_via_printwindow(hwnd, width, height)
            if candidate is not None:
                self._capture_hwnd = hwnd
                self._region = (left, top, width, height)
                self._sync_tap_target()
                image = candidate
                break

        if image is None:
            _left, _top, width, height = self._region
            image = self._capture_via_mss_fallback(width, height)
        frame = Frame(data=image)

        if not frame.matches_display_preset(self._preset):
            raise CaptureError(
                f"Display preset mismatch: got {frame.width}x{frame.height}, "
                f"expected {self._preset[0]}x{self._preset[1]} "
                f"(client/game area must match 設定→顯示預設)"
            )
        self._last = frame
        return frame

    def _hwnd_candidates(self) -> list[int]:
        top = self._window.handle
        if self._capture_hwnd == top:
            return [top]
        return [self._capture_hwnd, top]

    def _capture_via_printwindow(self, hwnd: int, width: int, height: int) -> np.ndarray | None:
        from fgo_auto.host.win32_capture import capture_hwnd_bgr

        image = capture_hwnd_bgr(hwnd, width, height)
        if image is None:
            logger.warning("printwindow_capture_failed", hwnd=hwnd)
            return None
        if int(np.mean(image)) < 4:
            logger.warning("printwindow_capture_black", hwnd=hwnd)
            return None
        logger.debug("capture_printwindow", hwnd=hwnd, w=width, h=height)
        return image

    def _capture_via_mss_fallback(self, width: int, height: int) -> np.ndarray:
        """Desktop grab when GDI fails; may include windows on top of the emulator."""
        try:
            import mss
        except ImportError as exc:
            raise CaptureError("Install windows extras: pip install 'fgo-auto[windows]'") from exc

        left, top, _, _ = self._region
        logger.warning(
            "capture_mss_fallback",
            hint="Move FGO-AUTO away from BlueStacks or retry bind",
        )
        with mss.mss() as sct:
            shot = sct.grab({"left": left, "top": top, "width": width, "height": height})
            image = np.array(shot)[:, :, :3]
            return cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)

    def save_diagnostic(self, path: Path) -> None:
        frame = self._last or self.capture()
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), frame.data)


def create_host_capture(window: WindowInfo, preset: tuple[int, int]) -> WindowHostCapture:
    return WindowHostCapture(window=window, preset=preset)
