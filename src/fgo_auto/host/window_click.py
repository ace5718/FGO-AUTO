"""Click/swipe on a bound window without moving the system cursor."""

from __future__ import annotations

import ctypes
import time
from ctypes import wintypes

import structlog

from fgo_auto.host.tap_target import TapTarget

logger = structlog.get_logger()

WM_MOUSEMOVE = 0x0200
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
MK_LBUTTON = 0x0001


def _user32():
    return ctypes.windll.user32


def frame_to_screen(target: TapTarget, x: int, y: int) -> tuple[int, int]:
    return target.origin_left + x, target.origin_top + y


def _lparam(x: int, y: int) -> int:
    return (int(y) << 16) | (int(x) & 0xFFFF)


def _message_click(hwnd: int, x: int, y: int, *, use_send: bool = True) -> None:
    """Deliver LBUTTONDOWN/UP to client coords; does not move the host cursor."""
    user32 = _user32()
    lp = _lparam(x, y)
    dispatch = user32.SendMessageW if use_send else user32.PostMessageW
    dispatch(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)
    dispatch(hwnd, WM_LBUTTONUP, 0, lp)


def _message_swipe(
    hwnd: int,
    x0: int,
    y0: int,
    x1: int,
    y1: int,
    *,
    duration_s: float = 0.35,
    steps: int | None = None,
) -> None:
    """Drag via window messages only (no SetCursorPos)."""
    user32 = _user32()
    n = steps if steps is not None else max(4, int(duration_s / 0.04))
    lp0 = _lparam(x0, y0)
    user32.SendMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp0)
    for i in range(1, n):
        t = i / n
        cx = int(x0 + (x1 - x0) * t)
        cy = int(y0 + (y1 - y0) * t)
        user32.SendMessageW(hwnd, WM_MOUSEMOVE, MK_LBUTTON, _lparam(cx, cy))
        time.sleep(duration_s / n)
    user32.SendMessageW(hwnd, WM_LBUTTONUP, 0, _lparam(x1, y1))


def post_click(target: TapTarget, x: int, y: int) -> None:
    """Click the game client area without moving the visible mouse cursor."""
    _message_click(target.hwnd, x, y, use_send=True)
    logger.info(
        "window_click",
        x=x,
        y=y,
        hwnd=target.hwnd,
        method="send_message",
    )


def post_swipe(
    target: TapTarget,
    start: tuple[int, int],
    end: tuple[int, int],
    *,
    duration_s: float = 0.35,
) -> None:
    _message_swipe(target.hwnd, start[0], start[1], end[0], end[1], duration_s=duration_s)
    logger.info(
        "window_swipe",
        start=start,
        end=end,
        hwnd=target.hwnd,
        method="send_message",
    )
