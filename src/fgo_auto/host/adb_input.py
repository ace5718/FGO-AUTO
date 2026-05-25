"""Tap/swipe via Android Debug Bridge (BlueStacks HD-Adb). Does not move the host cursor."""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import structlog

logger = structlog.get_logger()


class AdbError(Exception):
    """ADB executable missing or no device connected."""


_WM_SIZE_RE = re.compile(r"(\d+)\s*x\s*(\d+)", re.IGNORECASE)


def scale_frame_to_android(
    x: int,
    y: int,
    *,
    frame_size: tuple[int, int],
    android_size: tuple[int, int],
) -> tuple[int, int]:
    """Map capture / display_preset pixels to Android input coordinates."""
    frame_w, frame_h = frame_size
    android_w, android_h = android_size
    if frame_w <= 0 or frame_h <= 0:
        raise AdbError(f"無效的擷圖尺寸：{frame_size}")
    if android_w <= 0 or android_h <= 0:
        raise AdbError(f"無效的 Android 尺寸：{android_size}")
    if (frame_w, frame_h) == (android_w, android_h):
        return x, y
    ax = int(round(x * android_w / frame_w))
    ay = int(round(y * android_h / frame_h))
    return (
        max(0, min(android_w - 1, ax)),
        max(0, min(android_h - 1, ay)),
    )


class AdbInput:
    def __init__(
        self,
        adb_path: Path,
        device: str,
        *,
        frame_size: tuple[int, int],
        android_size: tuple[int, int],
    ) -> None:
        self._adb = adb_path
        self._device = device
        self._frame_size = frame_size
        self._android_size = android_size

    @property
    def device(self) -> str:
        return self._device

    @property
    def adb_path(self) -> Path:
        return self._adb

    @property
    def frame_size(self) -> tuple[int, int]:
        return self._frame_size

    @property
    def android_size(self) -> tuple[int, int]:
        return self._android_size

    @classmethod
    def create(
        cls,
        *,
        adb_path: str | Path | None = None,
        device: str | None = None,
        frame_size: tuple[int, int] = (1920, 1080),
    ) -> AdbInput:
        resolved = resolve_adb_path(adb_path)
        if resolved is None:
            raise AdbError(
                "找不到 adb。請安裝 BlueStacks（內建 HD-Adb.exe）或設定環境變數 FGO_AUTO_ADB_PATH"
            )
        picked = device or pick_device(resolved)
        android_size = query_android_display_size(resolved, picked)
        return cls(resolved, picked, frame_size=frame_size, android_size=android_size)

    def _to_android(self, x: int, y: int) -> tuple[int, int]:
        return scale_frame_to_android(
            x,
            y,
            frame_size=self._frame_size,
            android_size=self._android_size,
        )

    def tap(self, x: int, y: int) -> None:
        ax, ay = self._to_android(x, y)
        self._run("shell", "input", "tap", str(ax), str(ay))
        logger.info(
            "adb_tap",
            frame_x=x,
            frame_y=y,
            android_x=ax,
            android_y=ay,
            frame_size=self._frame_size,
            android_size=self._android_size,
            device=self._device,
        )

    def swipe(
        self,
        x0: int,
        y0: int,
        x1: int,
        y1: int,
        *,
        duration_ms: int = 350,
    ) -> None:
        ax0, ay0 = self._to_android(x0, y0)
        ax1, ay1 = self._to_android(x1, y1)
        self._run(
            "shell",
            "input",
            "swipe",
            str(ax0),
            str(ay0),
            str(ax1),
            str(ay1),
            str(max(1, int(duration_ms))),
        )
        logger.info(
            "adb_swipe",
            frame_start=(x0, y0),
            frame_end=(x1, y1),
            android_start=(ax0, ay0),
            android_end=(ax1, ay1),
            duration_ms=duration_ms,
            device=self._device,
        )

    def _run(self, *args: str) -> None:
        cmd = [str(self._adb), "-s", self._device, *args]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raise AdbError(f"ADB 逾時：{' '.join(cmd)}") from exc
        except OSError as exc:
            raise AdbError(f"無法執行 ADB：{exc}") from exc
        if result.returncode != 0:
            err = (result.stderr or result.stdout or "").strip()
            raise AdbError(err or f"ADB 失敗 (exit {result.returncode})")


def resolve_adb_path(override: str | Path | None = None) -> Path | None:
    if override:
        path = Path(override)
        if path.is_file():
            return path
        raise AdbError(f"adb_path 不存在：{path}")

    env = os.environ.get("FGO_AUTO_ADB_PATH", "").strip()
    if env:
        path = Path(env)
        if path.is_file():
            return path

    for candidate in (
        Path(r"C:\Program Files\BlueStacks_nxt\HD-Adb.exe"),
        Path(r"C:\Program Files (x86)\BlueStacks_nxt\HD-Adb.exe"),
    ):
        if candidate.is_file():
            return candidate

    found = shutil.which("adb")
    return Path(found) if found else None


def list_devices(adb_path: Path) -> list[str]:
    try:
        result = subprocess.run(
            [str(adb_path), "devices"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise AdbError(str(exc)) from exc
    if result.returncode != 0:
        raise AdbError((result.stderr or result.stdout or "adb devices failed").strip())

    devices: list[str] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("List of devices"):
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[1] == "device":
            devices.append(parts[0])
    return devices


def parse_wm_size_output(text: str) -> tuple[int, int]:
    """Parse `adb shell wm size` (Physical / Override size lines)."""
    for line in text.splitlines():
        if "Physical size" in line or "Override size" in line:
            match = _WM_SIZE_RE.search(line)
            if match:
                return int(match.group(1)), int(match.group(2))
    match = _WM_SIZE_RE.search(text)
    if match:
        return int(match.group(1)), int(match.group(2))
    raise AdbError(f"無法解析 wm size：{text.strip()!r}")


def query_android_display_size(adb_path: Path, device: str) -> tuple[int, int]:
    try:
        result = subprocess.run(
            [str(adb_path), "-s", device, "shell", "wm", "size"],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
    except (subprocess.TimeoutExpired, OSError) as exc:
        raise AdbError(str(exc)) from exc
    if result.returncode != 0:
        raise AdbError((result.stderr or result.stdout or "wm size failed").strip())
    return parse_wm_size_output(result.stdout or result.stderr or "")


def pick_device(adb_path: Path, preferred: str | None = None) -> str:
    devices = list_devices(adb_path)
    if not devices:
        raise AdbError("沒有已連線的 ADB 裝置。請開啟 BlueStacks 並啟用 Android 偵錯。")
    if preferred:
        if preferred in devices:
            return preferred
        raise AdbError(f"找不到裝置 {preferred!r}，目前：{', '.join(devices)}")
    for serial in devices:
        if serial.startswith("emulator-"):
            return serial
    return devices[0]
