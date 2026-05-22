from __future__ import annotations

from pathlib import Path
from typing import Protocol

import cv2
import numpy as np

from fgo_auto.host.window_binder import WindowInfo
from fgo_auto.vision.frame import Frame


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
    """Captures a bound emulator window client area."""

    def __init__(self, window: WindowInfo, preset: tuple[int, int]) -> None:
        self._window = window
        self._preset = preset
        self._last: Frame | None = None

    def capture(self) -> Frame:
        import sys

        if sys.platform != "win32":
            raise CaptureError("Window capture requires Windows")

        try:
            import mss
        except ImportError as exc:
            raise CaptureError("Install windows extras: pip install 'fgo-auto[windows]'") from exc

        with mss.mss() as sct:
            monitor = {
                "left": self._window.left,
                "top": self._window.top,
                "width": self._window.width,
                "height": self._window.height,
            }
            shot = sct.grab(monitor)
            image = np.array(shot)[:, :, :3]
            frame = Frame(data=cv2.cvtColor(image, cv2.COLOR_BGRA2BGR))

        if not frame.matches_display_preset(self._preset):
            raise CaptureError(
                f"Display preset mismatch: got {frame.width}x{frame.height}, "
                f"expected {self._preset[0]}x{self._preset[1]} (display_preset={self._preset[0]}x{self._preset[1]})"
            )
        self._last = frame
        return frame

    def save_diagnostic(self, path: Path) -> None:
        frame = self._last or self.capture()
        path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(path), frame.data)


def create_host_capture(window: WindowInfo, preset: tuple[int, int]) -> WindowHostCapture:
    return WindowHostCapture(window=window, preset=preset)
