"""Click/swipe on a bound window. BlueStacks often ignores PostMessage — use real input + restore cursor."""

from __future__ import annotations

import ctypes
import time
from ctypes import wintypes

import structlog

from fgo_auto.host.tap_target import TapTarget

logger = structlog.get_logger()

MOUSEEVENTF_MOVE = 0x0001
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


def _user32():
    return ctypes.windll.user32


def frame_to_screen(target: TapTarget, x: int, y: int) -> tuple[int, int]:
    return target.origin_left + x, target.origin_top + y


def _click_screen_restore(screen_x: int, screen_y: int) -> None:
    """Real left click at screen position, then restore cursor (brief flicker)."""
    user32 = _user32()
    saved = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(saved))
    user32.SetCursorPos(int(screen_x), int(screen_y))
    time.sleep(0.03)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(0.02)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    user32.SetCursorPos(saved.x, saved.y)


def post_click(target: TapTarget, x: int, y: int) -> None:
    """Real screen click; BlueStacks ignores PostMessage-only taps."""
    screen_x, screen_y = frame_to_screen(target, x, y)
    _click_screen_restore(screen_x, screen_y)
    logger.info(
        "window_click",
        x=x,
        y=y,
        screen_x=screen_x,
        screen_y=screen_y,
        hwnd=target.hwnd,
        method="cursor_restore",
    )


def post_swipe(
    target: TapTarget,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    duration_s: float = 0.35,
) -> None:
    user32 = _user32()
    saved = wintypes.POINT()
    user32.GetCursorPos(ctypes.byref(saved))
    sx, sy = frame_to_screen(target, start[0], start[1])
    ex, ey = frame_to_screen(target, end[0], end[1])
    steps = max(4, int(duration_s / 0.04))
    user32.SetCursorPos(sx, sy)
    time.sleep(0.03)
    user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    for i in range(1, steps):
        t = i / steps
        cx = int(sx + (ex - sx) * t)
        cy = int(sy + (ey - sy) * t)
        user32.SetCursorPos(cx, cy)
        time.sleep(duration_s / steps)
    user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    user32.SetCursorPos(saved.x, saved.y)
    logger.info("window_swipe", start=start, end=end, hwnd=target.hwnd, method="cursor_restore")
