from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from fgo_auto.host.adb_input import (
    AdbError,
    AdbInput,
    parse_wm_size_output,
    pick_device,
    resolve_adb_path,
    scale_frame_to_android,
)
from fgo_auto.host.input_backend import configure_input_backend, reset_input_backend
from fgo_auto.host.tap import tap_pixels


def test_resolve_adb_path_env(monkeypatch, tmp_path: Path) -> None:
    adb = tmp_path / "HD-Adb.exe"
    adb.write_bytes(b"")
    monkeypatch.setenv("FGO_AUTO_ADB_PATH", str(adb))
    assert resolve_adb_path() == adb


def test_pick_device_prefers_emulator() -> None:
    class Result:
        returncode = 0
        stdout = "List of devices attached\n127.0.0.1:5555\tdevice\nemulator-5554\tdevice\n"
        stderr = ""

    monkeypatch = pytest.MonkeyPatch()
    monkeypatch.setattr("fgo_auto.host.adb_input.subprocess.run", lambda *a, **k: Result())
    try:
        assert pick_device(Path("C:/fake/adb.exe")) == "emulator-5554"
    finally:
        monkeypatch.undo()


def test_scale_frame_to_android_1154x682_to_1920x1080() -> None:
    ax, ay = scale_frame_to_android(
        782,
        509,
        frame_size=(1154, 682),
        android_size=(1920, 1080),
    )
    assert ax == 1301
    assert ay == 806


def test_parse_wm_size() -> None:
    assert parse_wm_size_output("Physical size: 1920x1080\n") == (1920, 1080)


def test_adb_tap_invokes_shell_input(monkeypatch, tmp_path: Path) -> None:
    adb = tmp_path / "adb.exe"
    adb.write_bytes(b"")
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        return MagicMock(returncode=0, stdout="", stderr="")

    monkeypatch.setattr("fgo_auto.host.adb_input.subprocess.run", fake_run)
    client = AdbInput(
        adb,
        "emulator-5554",
        frame_size=(1154, 682),
        android_size=(1920, 1080),
    )
    client.tap(782, 509)
    assert calls[-1] == [str(adb), "-s", "emulator-5554", "shell", "input", "tap", "1301", "806"]


def test_tap_pixels_uses_adb_when_configured(monkeypatch, tmp_path: Path) -> None:
    adb = tmp_path / "adb.exe"
    adb.write_bytes(b"")
    calls: list[list[str]] = []

    def fake_run(cmd, **kwargs):
        calls.append(list(cmd))
        if len(cmd) >= 4 and cmd[-2:] == ["wm", "size"]:
            stdout = "Physical size: 1920x1080\n"
        else:
            stdout = "List of devices attached\nemulator-5554\tdevice\n"
        return MagicMock(returncode=0, stdout=stdout, stderr="")

    monkeypatch.setattr("fgo_auto.host.adb_input.subprocess.run", fake_run)
    reset_input_backend()
    configure_input_backend(method="adb", adb_path=str(adb), frame_size=(1154, 682))
    tap_pixels((100, 200))
    assert any("input" in c and "tap" in c for c in calls)
    reset_input_backend()


def test_configure_falls_back_without_devices(monkeypatch, tmp_path: Path) -> None:
    adb = tmp_path / "adb.exe"
    adb.write_bytes(b"")

    def fake_run(cmd, **kwargs):
        return MagicMock(returncode=0, stdout="List of devices attached\n", stderr="")

    monkeypatch.setattr("fgo_auto.host.adb_input.subprocess.run", fake_run)
    reset_input_backend()
    method = configure_input_backend(method="adb", adb_path=str(adb))
    assert method == "window_message"
    reset_input_backend()
