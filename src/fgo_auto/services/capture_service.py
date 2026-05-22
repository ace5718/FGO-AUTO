from __future__ import annotations

from pathlib import Path

import cv2

from fgo_auto.host.capture import CaptureError, FixtureHostCapture, HostCapture, create_host_capture
from fgo_auto.host.tap_target import TapTarget, set_tap_target
from fgo_auto.host.window_binder import WindowBinder, WindowInfo, create_window_binder
from fgo_auto.services.paths import logs_dir
from fgo_auto.vision.frame import Frame


class CaptureService:
    def __init__(
        self,
        binder: WindowBinder | None = None,
        log_dir: Path | None = None,
    ) -> None:
        self._binder = binder or create_window_binder()
        self._log_dir = log_dir or logs_dir()
        self._log_dir.mkdir(parents=True, exist_ok=True)
        self._capture: HostCapture | None = None
        self._window: WindowInfo | None = None

    @property
    def window(self) -> WindowInfo | None:
        return self._window

    @property
    def capture_backend(self) -> HostCapture | None:
        return self._capture

    def bind(self, title_rule: str, pick_handle: int | None, preset: tuple[int, int]) -> WindowInfo:
        self._window = self._binder.resolve(title_rule, pick_handle=pick_handle)
        capture = create_host_capture(self._window, preset)
        self._capture = capture
        left, top, _w, _h = capture.capture_region
        set_tap_target(
            TapTarget(
                hwnd=capture.capture_hwnd,
                origin_left=left,
                origin_top=top,
                client_coords=True,
            )
        )
        return self._window

    def use_fixture(self, image_path: Path, preset: tuple[int, int]) -> None:
        self._window = None
        self._capture = FixtureHostCapture(image_path, preset=preset)
        set_tap_target(None)

    def capture_frame(self) -> Frame:
        if self._capture is None:
            raise CaptureError("No window bound. Bind a window or use a fixture first.")
        return self._capture.capture()

    def save_frame(self, frame: Frame, path: Path | str = "frame.png") -> Path:
        target = Path(path)
        if not target.is_absolute():
            target = self._log_dir / target
        target.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(target), frame.data)
        return target
