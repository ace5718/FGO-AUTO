from __future__ import annotations

import sys
from unittest.mock import MagicMock

import pytest

from fgo_auto.host.tap_target import TapTarget


@pytest.mark.skipif(sys.platform != "win32", reason="Win32 only")
def test_post_swipe_does_not_move_system_cursor(monkeypatch) -> None:
    user32 = MagicMock()
    monkeypatch.setattr("fgo_auto.host.window_click._user32", lambda: user32)

    from fgo_auto.host.window_click import post_swipe

    target = TapTarget(hwnd=99, origin_left=0, origin_top=0)
    post_swipe(target, (100, 200), (100, 400), duration_s=0.12)

    assert not user32.SetCursorPos.called
    assert not user32.mouse_event.called
    assert user32.SendMessageW.called
    down_calls = [
        c
        for c in user32.SendMessageW.call_args_list
        if c.args[1] == 0x0201  # WM_LBUTTONDOWN
    ]
    assert down_calls


@pytest.mark.skipif(sys.platform != "win32", reason="Win32 only")
def test_post_click_uses_send_message_not_cursor(monkeypatch) -> None:
    user32 = MagicMock()
    monkeypatch.setattr("fgo_auto.host.window_click._user32", lambda: user32)

    from fgo_auto.host.window_click import post_click

    post_click(TapTarget(hwnd=42, origin_left=0, origin_top=0), 50, 60)

    assert not user32.SetCursorPos.called
    user32.SendMessageW.assert_any_call(42, 0x0201, 0x0001, (60 << 16) | 50)
