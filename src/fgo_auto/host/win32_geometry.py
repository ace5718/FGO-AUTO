"""Win32 helpers for client-area geometry (game surface without window chrome)."""

from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes


def client_area_screen_bounds(hwnd: int) -> tuple[int, int, int, int]:
    """
    Return (screen_left, screen_top, width, height) of the window client / game area.

    Falls back to GetWindowRect when client size is zero (some hosts).
    """
    if sys.platform != "win32":
        raise OSError("client_area_screen_bounds requires Windows")

    user32 = ctypes.windll.user32
    client = wintypes.RECT()
    if not user32.GetClientRect(hwnd, ctypes.byref(client)):
        raise OSError("GetClientRect failed")

    width = int(client.right - client.left)
    height = int(client.bottom - client.top)
    origin = wintypes.POINT(0, 0)
    if not user32.ClientToScreen(hwnd, ctypes.byref(origin)):
        raise OSError("ClientToScreen failed")

    if width > 0 and height > 0:
        return int(origin.x), int(origin.y), width, height

    outer = wintypes.RECT()
    if not user32.GetWindowRect(hwnd, ctypes.byref(outer)):
        raise OSError("GetWindowRect failed")
    return (
        int(outer.left),
        int(outer.top),
        int(outer.right - outer.left),
        int(outer.bottom - outer.top),
    )
