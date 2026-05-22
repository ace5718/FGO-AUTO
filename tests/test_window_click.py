from __future__ import annotations

import sys

import pytest

from fgo_auto.host.tap_target import TapTarget


@pytest.mark.skipif(sys.platform != "win32", reason="Win32 only")
def test_frame_to_screen_offset() -> None:
    from fgo_auto.host.window_click import frame_to_screen

    target = TapTarget(hwnd=0, origin_left=100, origin_top=50)
    assert frame_to_screen(target, 200, 300) == (300, 350)


def test_tap_target_clear() -> None:
    from fgo_auto.host.tap_target import get_tap_target, set_tap_target

    set_tap_target(TapTarget(hwnd=1, origin_left=0, origin_top=0))
    assert get_tap_target() is not None
    set_tap_target(None)
    assert get_tap_target() is None
